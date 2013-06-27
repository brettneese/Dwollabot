import re
import requests
import formencode
from dwolla import DwollaUser, DwollaClientApp
from formencode import validators, national
from config import DWOLLA_API_KEY, DWOLLA_API_SECRET, DWOLLA_API_TOKEN

class InvalidIdentiferError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def valid_amount(prompt):
    try:
        validators.Number.to_python(prompt)
        return True
    except formencode.Invalid, e:
        return False

def valid_phone(prompt):
    try:
        national.USPhoneNumber().to_python(prompt)
        return True
    except formencode.Invalid, e:
        return False

def valid_email_format(prompt):
    prompt = prompt.replace('(a)', '@')
    
    try:
        validators.Email().to_python(prompt)
        return True
    except formencode.Invalid, e:
        return False

def valid_email(prompt):
    if valid_email_format(prompt) == True:
        try:
            Dwolla = DwollaClientApp(DWOLLA_API_KEY, DWOLLA_API_SECRET)
            Dwolla.get_account_info(prompt)
            return True
        except:
            return False 
    else: 
        return False

def valid_twitter_format(prompt):    
    try:
        validators.Regex('(^|[^@\w])@(\w{1,15})').to_python(prompt)
        return True
    except formencode.Invalid, e:
        return False    

def twitter_user_exists(prompt):
    r = requests.get('https://twitter.com/' + prompt.strip())
    if r.status_code == 200:
        return True
    else:
        return False

def valid_twitter(prompt):
    if valid_twitter_format(prompt) == True and twitter_user_exists(prompt) == True:
        return True
    else: 
        return False

def valid_facebook(prompt):   
    r = requests.get('https://graph.facebook.com/' + prompt.strip())
    if r.status_code == 200:
        return True
    else:
        return False

def valid_dwolla(prompt):
    if valid_phone(prompt) == True:
        try:
            Dwolla = DwollaClientApp(DWOLLA_API_KEY, DWOLLA_API_SECRET)
            Dwolla.get_account_info(prompt)
            return True
        except:
            return False
    else:
        return False

def parse_account_type(prompt):

    if valid_twitter(prompt) == True:
        return "twitter"
    elif valid_facebook(prompt) == True:
        return "facebook"
    elif valid_email(prompt) == True: 
        return "dwolla_email"
    elif valid_dwolla(prompt) == True:
        return "dwolla"
    elif valid_email_format(prompt):
        return "email"
    elif valid_phone(prompt) == True:
        return "phone"
    else:
        return False