from flask import render_template, redirect,url_for,flash,request, jsonify
from packages import app,bcrypt
from packages import db
from packages.forms import SignupForm, LoginForm, PurchaseItemForm, UpdateInfoForm, DeleteAccountForm, ChangePasswordForm
from packages.models import Product, Category, User, Cart, Order, OrderItem
from flask_login import login_user,login_required,logout_user,current_user
from flask_bcrypt import check_password_hash, generate_password_hash
from flask import session
from sqlalchemy import desc,and_
from sqlalchemy.orm import joinedload
from packages.payment import initialize_payment, verify_payment

# Define the get_cart_count function
def get_cart_count():
    if current_user.is_authenticated:
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
        return cart_count
    return 0

# Define a context processor to make get_cart_count available in all templates
@app.context_processor
def inject_cart_count():
    cart_count = get_cart_count()
    return dict(cart_count=cart_count)

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
            # Add the item to the cart
            Cart.add_to_cart(user_id=current_user.id, product_id=p_item_object.id, quantity=1)
            flash(f"{p_item_object.title} added to your cart.", category='success')
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
            # Add the item to the cart
            Cart.add_to_cart(user_id=current_user.id, product_id=p_item_object.id, quantity=1)
            flash(f"{p_item_object.title} added to your cart.", category='success')
            # Store the category information in the session
            session['last_category'] = category

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

@app.route('/update_cart', methods=['POST'])
@login_required
def update_cart():
    # Get the product ID from the form
    product_id = request.form.get('product_id')

    # Check if product_id is provided and valid
    if not product_id or not product_id.isdigit():
        flash('Invalid product ID', 'danger')
        return redirect(url_for('cart'))

    # Convert product_id to integer
    product_id = int(product_id)

    # Get the action (increase/decrease) from the form
    action = request.form.get('action')

    # Get the quantity from the form
    new_quantity = request.form.get('quantity')

    # Check if new_quantity is provided and valid
    if not new_quantity or not new_quantity.isdigit():
        flash('Invalid quantity', 'danger')
        return redirect(url_for('cart'))

    # Convert new_quantity to integer
    new_quantity = int(new_quantity)

    # Fetch the cart entry for the user and product
    cart_entry = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if cart_entry:
        # Update the quantity based on the action
        if action == 'increase':
            cart_entry.quantity += 1
        elif action == 'decrease':
            if cart_entry.quantity > 1:
                cart_entry.quantity -= 1
            else:
                # Remove the item from the cart if the quantity becomes 0
                db.session.delete(cart_entry)
    else:
        flash('Cart entry not found', 'danger')
        return redirect(url_for('cart'))

    # Commit changes to the database
    db.session.commit()

    flash('Cart updated successfully!', 'success')
    return redirect(url_for('cart'))

@app.route('/delete_item_from_cart/<int:item_id>', methods=['POST'])
@login_required
def delete_item_from_cart(item_id):
    # Find the cart entry for the item
    cart_entry = Cart.query.filter_by(user_id=current_user.id, product_id=item_id).first()
    if cart_entry:
        # Delete the cart entry
        db.session.delete(cart_entry)
        db.session.commit()
        flash('Item deleted from cart.', 'danger')
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
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart'))

    # Calculate total price
    total_price = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)

    # Create an order with Waiting payment status
    order = Order(user_id=current_user.id, total_price=total_price, status='Waiting payment')
    db.session.add(order)
    db.session.commit()  # Commit to get the order ID

    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            product_price=cart_item.product.price
        )
        db.session.add(order_item)
    
    db.session.commit()  # Commit the order items

    # Initialize payment with Chapa
    try:
        payment_response = initialize_payment(
            order_id=order.id,
            amount=total_price,
            email=current_user.email,
            first_name=current_user.username,
            last_name=current_user.username
        )
        
        if payment_response.get('status') == 'success':
            # Don't clear the cart yet - wait for successful payment
            return redirect(payment_response['data']['checkout_url'])
        else:
            # If payment initialization fails, delete the order and its items
            OrderItem.query.filter_by(order_id=order.id).delete()
            Order.query.filter_by(id=order.id).delete()
            db.session.commit()
            
            flash('Payment initialization failed. Please try again.', 'danger')
            return redirect(url_for('cart'))
            
    except Exception as e:
        # If there's an error, delete the order and its items
        OrderItem.query.filter_by(order_id=order.id).delete()
        Order.query.filter_by(id=order.id).delete()
        db.session.commit()
        
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('cart'))

@app.route('/payment/callback', methods=['POST'])
def payment_callback():
    """Handle payment callback from Chapa"""
    try:
        transaction_id = request.form.get('transaction_id')
        tx_ref = request.form.get('tx_ref')
        
        # Verify the payment
        verification = verify_payment(transaction_id)
        
        if verification.get('status') == 'success':
            # Update order status
            order = Order.query.filter_by(id=tx_ref).first()
            if order:
                order.status = 'Pending'
                db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/payment/success')
@login_required
def payment_success():
    """Handle successful payment return"""
    # Debug: Print all request data
    print("Request args:", dict(request.args))
    print("Request form:", dict(request.form))
    print("Request headers:", dict(request.headers))
    
    # Get transaction reference from Chapa's response
    tx_ref = request.args.get('trx_ref') or request.args.get('tx_ref')
    print("Transaction reference:", tx_ref)
    
    if not tx_ref:
        # If no transaction reference, try to get the latest waiting payment order
        latest_order = Order.query.filter_by(
            user_id=current_user.id,
            status='Waiting payment'
        ).order_by(Order.created_at.desc()).first()
        
        if latest_order:
            print("Found latest waiting payment order:", latest_order.id)
            order = latest_order
            
            # Clear the user's cart
            Cart.query.filter_by(user_id=current_user.id).delete()
            
            # Update order status to Pending (for paid orders)
            order.status = 'Pending'
            db.session.commit()
            
            # Join with Product table to get product details
            order_items = db.session.query(OrderItem, Product).join(
                Product, OrderItem.product_id == Product.id
            ).filter(OrderItem.order_id == order.id).all()
            
            # Extract OrderItem objects from the joined query
            order_items = [item[0] for item in order_items]
            total = sum(item.product_price * item.quantity for item in order_items)
            
            return render_template('receipt.html', 
                                order=order,
                                order_items=order_items,
                                total=total,
                                user=current_user)
    
    # If we have a transaction reference, try to find the order
    order = Order.query.filter_by(id=tx_ref).first()
    if order:
        print("Found order by tx_ref:", order.id)
        
        # Clear the user's cart
        Cart.query.filter_by(user_id=current_user.id).delete()
        
        # Update order status to Pending (for paid orders)
        order.status = 'Pending'
        db.session.commit()
        
        # Join with Product table to get product details
        order_items = db.session.query(OrderItem, Product).join(
            Product, OrderItem.product_id == Product.id
        ).filter(OrderItem.order_id == order.id).all()
        
        # Extract OrderItem objects from the joined query
        order_items = [item[0] for item in order_items]
        total = sum(item.product_price * item.quantity for item in order_items)
        
        return render_template('receipt.html', 
                            order=order,
                            order_items=order_items,
                            total=total,
                            user=current_user)
    
    # If we get here, we couldn't find the order
    print("No order found for tx_ref:", tx_ref)
    flash('Payment successful! Your order has been placed.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/cancel_order/<int:product_id>', methods=['POST'])
@login_required
def cancel_order(product_id):
    # Find the ordered item by product_id and current user
    ordered_item = OrderItem.query.join(Order).filter(and_(OrderItem.product_id == product_id, Order.user_id == current_user.id)).first()

    if ordered_item:
        # Get the order associated with this item
        order = ordered_item.order
        
        # Set the order status to Cancelled
        order.status = 'Cancelled'
        db.session.commit()
        
        flash('Order cancelled successfully!', 'success')
    else:
        flash('Ordered item not found or you are not authorized to cancel this order.', 'danger')

    return redirect(url_for('dashboard'))

    


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
                flash('Password is wrong! Please try again.', category='danger')
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
            # Delete the user account from the database
            db.session.delete(user)
            db.session.commit()

            flash('Your account has been deleted. We are sorry to see you go.', 'danger')

            return redirect(url_for('index'))

    # Fetch pending orders and associated items using a single query
    user_orders = Order.query.filter_by(
        user_id=current_user.id,
        status='Pending'  # Show orders with Pending status (paid orders)
    ).options(joinedload(Order.items)).order_by(desc(Order.created_at)).all()

    # Initialize a dictionary to store ordered items and their quantities
    ordered_items = {}

    # Fetch items and their quantities from each order
    for order in user_orders:
        for order_item in order.items:
            product_id = order_item.product_id
            quantity = order_item.quantity
            if product_id in ordered_items:
                ordered_items[product_id]['quantity'] += quantity
            else:
                product = Product.query.get(product_id)
                if product:
                    ordered_items[product_id] = {'product': product, 'quantity': quantity}

    return render_template('dashboard.html', 
                         user=current_user, 
                         ordered_items=ordered_items.values(), 
                         purchase_form=purchase_form, 
                         delete_form=delete_form)



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
            flash('Incorrect old password. Please insert a correct password!.', 'danger')
        else:
            # Update the user's password with the new password
            current_user.password_hash = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully!', 'success')
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
