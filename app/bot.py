import models
import twilio.twiml

from flask import Flask, request, redirect, session, Response, url_for, render_template, flash, g

from dwolla import DwollaClientApp
from functools import wraps
from simplejson import loads
from urllib2 import urlopen
from urlobject import URLObject

from app import app, db
from config import DWOLLA_API_KEY, DWOLLA_API_SECRET, DWOLLA_API_TOKEN, TWILIO_AUTH_TOKEN
from dwolla import *    
from validation import *
from models import User
from forms import LoginForm

Dwolla = DwollaClientApp(DWOLLA_API_KEY, DWOLLA_API_SECRET)

@app.route("/twilio", methods=['GET', 'POST'])
def sms():

    try:
        next_action = session['next_action']
    except KeyError: 
        next_action = 'ask_for_amount'

    sms_body = request.values.get('Body') #slap the sms body into sms_body

    #check sms_body to see if it's any of the "global" commands
    if sms_body == "q" or sms_body == "r" or sms_body == "restart" or sms_body == "x":
        next_action = "reset"
    elif sms_body == "about":
        next_action = "about"
    elif sms_body == "help":
        next_action = "help"
    elif sms_body == "balance":
        next_action = "balance"
    elif sms_body[0] == '?':
        next_action = "search"

    phone = request.values.get('From').replace('+', '')
    u = models.User.query.get(phone)

    if not u:
        next_action = 'register'
    else: 
        dwolla_token = u.token

    #do work, son
    if next_action == "register":
        message = register()

    elif next_action == "about":
        message = about()
    elif next_action == "help": 
        message = help()
    elif next_action == "reset": 
        message = reset()
    elif next_action == "balance":
        message = balance(dwolla_token, request)
    elif next_action == "reset":
        message = reset()
    elif next_action == "search":
        message = search(sms_body, dwolla_token)
    elif next_action == "response_to_search":
        message = response_to_search(sms_body)
    elif next_action == "ask_for_amount":
        message = ask_for_amount(sms_body)
    elif next_action == "ask_for_pin":
        message = ask_for_pin(sms_body)
    elif next_action == "send_money":
        message = send_money(sms_body, dwolla_token)

    resp = twilio.twiml.Response()
    message = message.replace('@', '(a)')
    resp.sms(message)
     
    return str(resp)

def register():
    return "Dwollabot searched hard and it looks like you're not registered! Sign up at http://dwollabot.brettneese.com."

def about():
    return "(C) 2013 by Brett Neese -- http://brettneese.com // Built in Iowa using Dwolla, Twilio, Python, and hosted on Heroku // Never stop running."

def help():
    message = "I can: 'q' 2 start over, send w/ email/phone/dwlla/twitter/fb, BALANCE 4 balance; ABOUT for credits, ?find contact.";

def reset():
    session.clear()
    session['next_action'] = 'ask_for_amount'
    return  "Let's try this again! Reply with a valid Dwolla identifer (Facebook, (a)Twitter, e(a)mail.com, phone number, Dwolla User ID, or ?search)";

def balance(dwolla_token, request):
    return "Your current Dwolla Balance is $" + str(DwollaUser(dwolla_token).get_balance()) + "."

def search(sms_body, dwolla_token):
    string = ''
    sms_body = sms_body.replace('?', '')
    contacts = DwollaUser(dwolla_token).get_contacts(sms_body, limit=10, types='Dwolla')
 
    for index, key in enumerate(contacts[0:10]):
        session['contacts'] = contacts
        string += str(index) + ') ' + str(key['Name']) + ' '
    
    session['next_action'] = 'response_to_search'
    return str(string)

def response_to_search(sms_body):
    contacts = session['contacts']
    destinationId = contacts[int(sms_body)]['Id']
    user = Dwolla.get_account_info(destinationId)
    name = user['Name']
    session['account_type'] = 'Dwolla'
    session['destinationName'] = name
    session['destinationId'] = destinationId
    session['next_action'] = 'ask_for_pin'
    return "How much money would you like to send to " + name + "? Reply with 'q' any time to start over."


def ask_for_amount(sms_body):

    sms_body = sms_body.replace('(a)', '@')
    destinationId = sms_body
    account_type = parse_account_type(destinationId)

    if account_type == 'dwolla' or account_type == 'dwolla_email':
        user = Dwolla.get_account_info(sms_body)
        name = user['Name']
    elif account_type == 'email':
        name = 'the email address ' + sms_body
    elif account_type == 'facebook':
        content = loads(urlopen('http://graph.facebook.com/'+sms_body).read())
        name = 'your Facebook friend ' + content['name']
    elif account_type == 'twitter':
        name = 'Twitter user ' + sms_body
    elif account_type == 'phone':
        name = 'phone number ' + sms_body
    else:
        return "That's not right. Please enter a valid (a)twitter, Facebook, e(a)mail.com, or phone number, or Dwolla ID."

    session['account_type'] = account_type
    session['destinationName'] = name
    session['destinationId'] = destinationId
    session['next_action'] = 'ask_for_pin'

    return "How much money would you like to send to " + name + "? Reply with 'q' any time to start over."

def ask_for_pin(sms_body):

    amount = sms_body.replace("$", "")

    if valid_amount(amount) == True:
        session['next_action'] = 'send_money'
        session['amount'] = amount
        return "Sending $" + str(amount) + " to " + session['destinationName'] + "! PIN? (use 'delete message' to rmv ur rspnse whn cmplte.)"
    else:
        session['next_action'] = 'ask_for_pin'
        return 'Invalid amount. Please enter a valid amount to send to ' + session['destinationName'] + '.'

def send_money(sms_body, dwolla_token):
    pin = sms_body

    try:
        transaction = DwollaUser(dwolla_token).send_funds(session['amount'], session['destinationId'], pin, 'Sent via http://dwollabot.brettneese.com', dest_type=session['account_type'])
        transaction_info = DwollaUser(dwolla_token).get_transaction(transaction)
        session.clear()
        return 'Sent $' + str(transaction_info['Amount']) + ' to ' + transaction_info['DestinationName'] + '!' + ' TID:' + str(transaction_info['Id']) + '. Rspnd w/ new contact or other cmd.'
    except DwollaAPIError, e:
        session.clear()
        session['next_action'] = 'ask_for_amount'
        return "Error: " + str(e) + ". Who would you like to send money to?"
