from flask import render_template, redirect,url_for,flash, request
from packages import app,bcrypt
from packages import db
from packages.forms import SignupForm, LoginForm, PurchaseItemForm, UpdateInfoForm, DeleteAccountForm, ChangePasswordForm
from packages.models import Product, Category, User
from flask_login import login_user,login_required,logout_user,current_user
from flask_bcrypt import check_password_hash, generate_password_hash


# route to display the homepage of the website
@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

#route to display the market page of the webiste
@app.route('/market', methods=['GET','POST'])
@login_required
def market():
    purchase_form = PurchaseItemForm()
    if request.method == "POST":
        purchased_item = request.form.get('purchased_item')
        p_item_object = Product.query.filter_by(title=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.owner = current_user.id
                current_user.budget -= p_item_object.price
                db.session.commit()
                flash(f"Congrats! You have successfully purchased {p_item_object.title} for ${p_item_object.price}.",category='success')
                return redirect(url_for('market'))
            else:
                flash(f"Unfortunately you don't have enough money to purchase {p_item_object.title}.",category='danger')

    products_data = Product.query.filter_by(owner=None)
    return render_template('market.html', products=products_data, purchase_form=purchase_form)


# root to display the products category page
@app.route('/products')
@login_required
def products():
    # Fetch product categories from data/category.py
    categories = Category.query.all()

    return render_template('products.html', categories=categories)

#route to display the products by their category
@app.route('/category/<string:category>', methods=['GET','POST'])
@login_required
def category(category):
    purchase_form = PurchaseItemForm()
    products = Product.query.filter_by(category=category,owner=None).all()
    if request.method == "POST":
        purchased_item = request.form.get('purchased_item')
        p_item_object = Product.query.filter_by(title=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.owner = current_user.id
                current_user.budget -= p_item_object.price
                db.session.commit()
                flash(f"Congrats! You have successfully purchased {p_item_object.title} for ${p_item_object.price}.",category='success')
                return redirect(url_for('category', category=category))
            else:
                flash(f"Unfortunately you don't have enough money to purchase {p_item_object.title}.",category='danger')

    return render_template('category.html', category=category, products=products, purchase_form=purchase_form)

# route to display the sign-up page
@app.route('/signup',methods=['GET','POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = SignupForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email=form.email.data,
                              phone=form.phone.data,
                              budget=form.budget.data + 1000,
                              dob=form.dob.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f'Account created Successfully! You are now logged in as {user_to_create.username}!', category='success')
        return redirect(url_for('dashboard'))
    if form.errors != {}:
        for error_msg in form.errors.values():
            flash(f'{error_msg}',category='danger')
    return render_template('signup.html',form=form)

# Route to log in the user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()

        if attempted_user:
            if attempted_user.check_password_correction(attempted_password=form.password.data):
                login_user(attempted_user)
                flash(f'Successfully logged in as {attempted_user.username}!', category='success')
                return redirect(url_for('dashboard'))
            else:
                flash('Username or password is wrong! Please try again.', category='danger')
        else:
            flash('Account with this username does not exist. Please sign up.', category='danger')
            return redirect(url_for('signup'))
            # You can redirect to the signup page or render a specific template for account creation.

    return render_template('login.html', form=form)

#route to log out the user
@app.route('/logout')
def logout():
    logout_user()
    flash(f'You have been logged out!',category='info')
    return redirect(url_for('index'))

#route to display the dashboard of the user
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    purchase_form = PurchaseItemForm()
    owned_items = Product.query.filter_by(owner=current_user.id)
    delete_form = DeleteAccountForm()

    if delete_form.validate_on_submit():
        user_id = current_user.id
        user = User.query.get(user_id)

        if user:
            # Update products owned by the user to set the 'owner' to None
            Product.query.filter_by(owner=user_id).update({"owner": None})

            # Delete the user account from the database
            db.session.delete(user)
            db.session.commit()

            flash('Your account has been deleted. We are sorry to see you go.', 'danger')

            return redirect(url_for('index'))
    
    return render_template('dashboard.html', user=current_user, owned_items=owned_items, purchase_form=purchase_form, delete_form=delete_form)


@app.route('/update', methods=['GET', 'POST'])
@login_required  # Requires the user to be logged in to access this route
def update_info():
    update_info = UpdateInfoForm()

    # Check if the user already has a username, and set the default value accordingly
    if not update_info.username.data:
        update_info.username.data = current_user.username

    # Check if the user already has a phone number, and set the default value accordingly
    if not update_info.phone.data:
        update_info.phone.data = current_user.phone

    # Check if the user already has an email address, and set the default value accordingly
    if not update_info.email.data:
        update_info.email.data = current_user.email

    # Check if the user already has a budget value, and set the default value accordingly
    if not update_info.budget.data:
        update_info.budget.data = current_user.budget


    
    if update_info.validate_on_submit():
        # Get the current user's ID
        user_id = current_user.id 
        
        # Fetch the user from the database by ID
        user = User.query.get(user_id)
        
        if user:
            # Update the user's attributes from the form data
            user.username = update_info.username.data
            user.email = update_info.email.data
            user.phone = update_info.phone.data
            user.budget = update_info.budget.data
            
            # Commit the changes to the database
            db.session.commit()
            
            flash('Your profile has been updated successfully!', 'success')
            
            return redirect(url_for('dashboard'))
        
    if update_info.errors != {}:
        for error_msg in update_info.errors.values():
            flash(f'{error_msg}',category='danger')
    
    return render_template('update_profile.html', update_info=update_info)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Check if the old password provided matches the current user's password
        if form.old_password.data == form.new_password.data:
            flash('New password must be different from the old password.', 'danger')

        elif not bcrypt.check_password_hash(current_user.password_hash, form.old_password.data):
            flash('Incorrect old password. Please try again.', 'danger')
        else:
            # Update the user's password with the new password
            current_user.password_hash = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('dashboard'))

    return render_template('change_password.html', form=form)




# route to display the about page
@app.route('/about')
def about():
    return render_template('about.html')


# route to display the contact us page
@app.route('/contact')
def contact():
    return render_template('contact.html')
