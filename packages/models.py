from packages import db,bcrypt,login_manager
from flask_login import UserMixin
from datetime import datetime
import uuid




class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    total_price = db.Column(db.Integer(), nullable=False)
    status = db.Column(db.String(length=20), nullable=False, default='Pending')  # 'Pending', 'Completed', 'Cancelled'
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)


class OrderItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)
    product_price = db.Column(db.Integer(), nullable=False)

    @property
    def subtotal(self):
        return self.quantity * self.product_price

class Cart(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False, default=1)
    product = db.relationship('Product', backref='cart_entries')

    @staticmethod
    def add_to_cart(user_id, product_id, quantity):
        cart_entry = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

        if cart_entry:
            # If the item is already in the cart, increase the quantity
            cart_entry.quantity += quantity
        else:
            # If the item is not in the cart, create a new cart entry
            cart_entry = Cart(user_id=user_id, product_id=product_id, quantity=quantity)

        db.session.add(cart_entry)
        db.session.commit()

    @staticmethod
    def remove_from_cart(user_id, product_id):
        cart_entry = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

        if cart_entry:
            db.session.delete(cart_entry)
            db.session.commit()


class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(length=20), nullable=False, unique=True)
    category = db.Column(db.String(length=20), nullable=False)
    image = db.Column(db.String(length=20), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)

class Category(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(length=20), nullable=False, unique=True)
    image = db.Column(db.String(length=20), nullable=False, unique=True)

@login_manager.user_loader
def Load_user(user_id):
    return User.query.get(str(user_id))
    
class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(length=20), nullable=False, unique=True)
    email = db.Column(db.String(length=20), nullable=False, unique=True)
    phone = db.Column(db.String(), nullable=False, unique=True)
    dob = db.Column(db.Date())
    password_hash = db.Column(db.String(length=20), nullable=False)
   # product = db.relationship('Product',backref='owned_user',lazy=True)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)
