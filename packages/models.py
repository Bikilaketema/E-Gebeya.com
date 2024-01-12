from packages import db,bcrypt,login_manager
from flask_login import UserMixin


class Product(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(length=20), nullable=False, unique=True)
    category = db.Column(db.String(length=20), nullable=False)
    image = db.Column(db.String(length=20), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))

class Category(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=20), nullable=False, unique=True)
    image = db.Column(db.String(length=20), nullable=False, unique=True)

@login_manager.user_loader
def Load_user(user_id):
    return User.query.get(int(user_id))
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=20), nullable=False, unique=True)
    email = db.Column(db.String(length=20), nullable=False, unique=True)
    phone = db.Column(db.String(), nullable=False, unique=True)
    budget = db.Column(db.Integer(), nullable=False, default=1000)
    dob = db.Column(db.Date())
    password_hash = db.Column(db.String(length=20), nullable=False)
    product = db.relationship('Product',backref='owned_user',lazy=True)

    @property
    def prettier_budget(self):
        formatted_budget = "{:,.2f}".format(self.budget)
        return f'$ {formatted_budget}'



    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)
    
    def can_purchase(self, item_obj):
        return self.budget >= item_obj.price
