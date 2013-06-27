#from flask.ext.login import login_user, logout_user, current_user, login_required
# Include the Flask framework
import re

import app
import models 

from config import *

from flask import Flask, url_for, request, redirect, render_template, session, flash, g
from forms import LoginForm
from dwolla import DwollaClientApp

from app import app, db
from models import User



# Instantiate a new Dwolla User client
# And, Seed a previously generated access token
Dwolla = DwollaClientApp(DWOLLA_API_KEY, DWOLLA_API_SECRET)

@app.route('/', methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate_on_submit():
        phone = '1' + re.sub("[^0-9]", "", form.phone.data)
        email = form.email.data 

        session['email'] = email
        session['phone'] = phone
        return dwolla_oauth()
    
    return render_template('login.html', 
        title = 'Sign In',
        form = form)

@app.route("/oauth")
def dwolla_oauth():
    oauth_return_url = url_for('dwolla_oauth_return', _external=True) # Point back to this file/URL
    permissions = 'Send|Transactions|Balance|Request|Contacts|AccountInfoFull'
    authUrl = Dwolla.init_oauth_url(oauth_return_url, permissions)

    return redirect(authUrl)

@app.route("/dwolla/oauth_return")
def dwolla_oauth_return():
    oauth_return_url = url_for('dwolla_oauth_return', _external=True) # Point back to this file/URL
    code = request.args.get("code")
    token = Dwolla.get_oauth_token(code, redirect_uri=oauth_return_url)
    me = models.User(phone=session['phone'], email=session['email'], token=str(token))
    db.session.merge(me)
    db.session.commit()
    return "Success! Now just text message <a href='https://medium.com/look-what-i-made/9a1ba1870025'> one of the commands </a> to 1-904-DWLLA-07. :)"
    

