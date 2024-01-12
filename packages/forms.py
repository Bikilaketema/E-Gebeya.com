from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, EmailField, IntegerField
from wtforms.validators import Email,EqualTo,Length,DataRequired,ValidationError, Regexp
from packages.models import User
from flask_login import current_user


class SignupForm(FlaskForm):
    def validate_username(self,username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exist! Please try a different username.')

    def validate_email(self,email_to_check):
        email = User.query.filter_by(email=email_to_check.data).first()
        if email:
            raise ValidationError('There is already an account with the email address.'
                                  'Please try different email address!')
        
    def validate_phone(self,phone_to_check):
        phone = User.query.filter_by(phone=phone_to_check.data).first()
        if phone:
            raise ValidationError('There is already an account with the Phone number you entered..'
                                  'Please try different phone number!')

    username = StringField(
    label="Username",
    validators=[
        DataRequired(message="Username is required."),
        Length(min=2, max=20, message="Username must be between 2 and 20 characters."),
        Regexp(r'^[A-Z][a-zA-Z]*$', message="Username must start with a capital letter and contain only letters.")
    ]
)
    email = EmailField(label="Email Address",
    validators=[Email(),
                DataRequired()])
    
    phone = StringField(label="Phone Number",
        validators=[
        DataRequired(message="The phone number field can not be empty!"),
        Regexp(
            r"^(?:[1-9]\d{0,8}|9)$",
            message="You entered an existing phone number or a bad phone number. Phone number must be a number between 1-0 and 9 digits. It must be without zero"
        )
    ])
    
    dob = DateField(label="Date of birth",
    validators=[DataRequired(message="You have to enter a valid birthday!")])

    budget = IntegerField(label="Enter your budget",
    validators=[DataRequired("Please enter your budget!")])

    password1 = PasswordField(label="Password",
    validators=[Length(min=6),DataRequired(message="You must insert the same password twice!")])
    password2 = PasswordField(label="Confirm password",validators=[EqualTo('password1'),DataRequired("You must insert the same password twice!")])

    submit = SubmitField(label="Sign up")


class LoginForm(FlaskForm):
    username = StringField(label="Username",validators=[Length(min=4,max=30),DataRequired()])
    password = PasswordField(label="Password",validators=[Length(min=6),DataRequired()])
    submit = SubmitField(label="Log in")

class PurchaseItemForm(FlaskForm):
    submit = SubmitField(label="Purchase")

class DeleteAccountForm(FlaskForm):
    delete = SubmitField(label="Yes, I am sure!")

class UpdateInfoForm(FlaskForm):
    edit = SubmitField(label="Update my profile")

    username = StringField(
        label="Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=2, max=20, message="Username must be between 2 and 20 characters."),
            Regexp(r'^[A-Z][a-zA-Z]*$', message="Username must start with a capital letter and contain only letters.")
        ]
    )
    email = EmailField(label="Email Address",
                       validators=[Email(), DataRequired()])

    phone = StringField(label="Phone Number",
                        validators=[
                            DataRequired(message="The phone number field cannot be empty!"),
                            Regexp(
                                r"^(?:[1-9]\d{0,8}|9)$",
                                message="Phone number must be a number between 1-9 and 9 digits. It must be without zero"
                            )
                        ])

    budget = IntegerField(label="Enter your budget", validators=[DataRequired("Please enter your budget!")])

    def validate_username(self, username_to_check):
        if username_to_check.data != current_user.username:  # Skip validation if username matches current user's username
            user = User.query.filter_by(username=username_to_check.data).first()
            if user:
                raise ValidationError('Username already exists! Please try a different username.')

    def validate_email(self, email_to_check):
        if email_to_check.data != current_user.email:  # Skip validation if email matches current user's email
            email = User.query.filter_by(email=email_to_check.data).first()
            if email:
                raise ValidationError('There is already an account with the email address. Please try a different email address!')

    def validate_phone(self, phone_to_check):
        if phone_to_check.data != current_user.phone:  # Skip validation if phone number matches current user's phone number
            phone = User.query.filter_by(phone=phone_to_check.data).first()
            if phone:
                raise ValidationError('There is already an account with the phone number you entered. Please try a different phone number!')
            
class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    confirm = SubmitField('Update Password')
        





