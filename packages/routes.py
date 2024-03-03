from flask import render_template, redirect,url_for,flash, request
from packages import app,bcrypt
from packages import db
from packages.forms import SignupForm, LoginForm, PurchaseItemForm, UpdateInfoForm, DeleteAccountForm, ChangePasswordForm
from packages.models import Product, Category, User, Cart, Order, OrderItem
from flask_login import login_user,login_required,logout_user,current_user
from flask_bcrypt import check_password_hash, generate_password_hash
from flask import session
from sqlalchemy import desc
from sqlalchemy.orm import joinedload


# route to display the homepage of the website
@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

# Route to display the market page of the website
@app.route('/market', methods=['GET', 'POST'])
@login_required
def market():
    purchase_form = PurchaseItemForm()
    if request.method == "POST":
        purchased_item = request.form.get('purchased_item')
        p_item_object = Product.query.filter_by(title=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                # Add the item to the cart
                Cart.add_to_cart(user_id=current_user.id, product_id=p_item_object.id, quantity=1)
                flash(f"{p_item_object.title} added to your cart.", category='success')
            else:
                flash(f"Unfortunately you don't have enough money to purchase {p_item_object.title}.", category='danger')
        return redirect(url_for('market'))

    products_data = Product.query.all()
    return render_template('market.html', products=products_data, purchase_form=purchase_form)


# root to display the products category page
@app.route('/products')
@login_required
def products():
    # Fetch product categories from data/category.py
    categories = Category.query.all()

    return render_template('products.html', categories=categories)

# Route to display the products by their category
@app.route('/category/<string:category>', methods=['GET', 'POST'])
@login_required
def category(category):
    purchase_form = PurchaseItemForm()
    products = Product.query.filter_by(category=category).all()
    if request.method == "POST":
        purchased_item = request.form.get('purchased_item')
        p_item_object = Product.query.filter_by(title=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                # Add the item to the cart
                Cart.add_to_cart(user_id=current_user.id, product_id=p_item_object.id, quantity=1)
                flash(f"{p_item_object.title} added to your cart.", category='success')
                # Store the category information in the session
                session['last_category'] = category
            else:
                flash(f"Unfortunately you don't have enough money to purchase {p_item_object.title}.", category='danger')

        # Redirect back to the same category page
        return redirect(url_for('category', category=category))

    return render_template('category.html', category=category, products=products, purchase_form=purchase_form)


# cart route
@app.route('/cart', methods=['GET','POST'])
@login_required
def cart():
    purchase_form = PurchaseItemForm()  # Assuming PurchaseItemForm is defined
    cart_entries = Cart.query.filter_by(user_id=current_user.id).all()
    products_in_cart = []
    total_price = 0
    
    for cart_entry in cart_entries:
        product = Product.query.get(cart_entry.product_id)
        products_in_cart.append((product, cart_entry.quantity))
        total_price += product.price * cart_entry.quantity
    
    return render_template('cart.html', products_in_cart=products_in_cart, total_price=total_price, purchase_form=purchase_form)


@app.route('/delete_item_from_cart/<int:item_id>', methods=['POST'])
@login_required
def delete_item_from_cart(item_id):
    # Find the cart entry for the item
    cart_entry = Cart.query.filter_by(user_id=current_user.id, product_id=item_id).first()
    if cart_entry:
        # Delete the cart entry
        db.session.delete(cart_entry)
        db.session.commit()
        flash('Item deleted from cart.', 'success')
    else:
        flash('Item not found in cart.', 'danger')

    # Redirect back to the cart page
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Retrieve user's cart items
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart'))

    # Calculate total price
    total_price = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)

    # Check if user can afford all items
    if not current_user.can_afford_total(total_price):
        flash("You don't have enough budget to purchase all items in your cart.", 'error')
        return redirect(url_for('cart'))

    # Create an order
    order = Order(user_id=current_user.id, total_price=total_price)
    db.session.add(order)
    db.session.commit()

    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price
        )
        db.session.add(order_item)

    # Update user's budget
    current_user.budget -= total_price
    db.session.commit()

    # Clear the user's cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash('Your order has been placed successfully!', 'success')
    return redirect(url_for('dashboard'))  # Redirect to orders page or any other desired page




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


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    purchase_form = PurchaseItemForm()
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

    # Fetch pending orders and associated items using a single query
    user_pending_orders = Order.query.filter_by(user_id=current_user.id, status='Pending').options(joinedload(Order.items)).order_by(desc(Order.created_at)).all()

    # Initialize a dictionary to store ordered items and their quantities
    ordered_items = {}

    # Fetch items and their quantities from each pending order
    for order in user_pending_orders:
        for order_item in order.items:
            product_id = order_item.product_id
            quantity = order_item.quantity
            if product_id in ordered_items:
                ordered_items[product_id]['quantity'] += quantity
            else:
                product = Product.query.get(product_id)
                if product:
                    ordered_items[product_id] = {'product': product, 'quantity': quantity}

    return render_template('dashboard.html', user=current_user, ordered_items=ordered_items.values(), purchase_form=purchase_form, delete_form=delete_form)



#Route to update the user details
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
