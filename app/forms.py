from flask.ext.wtf import Form, TextField, BooleanField
from flask.ext.wtf import Required, Regexp, Email

class LoginForm(Form):
	
    phone = TextField('phone', validators = [Required(), Regexp('^(\d{3})\D*(\d{3})\D*(\d{4})$', message='Please enter a valid US phone number.')])
    email = TextField('email', validators = [Email()])
