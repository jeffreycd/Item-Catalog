from flask import (Flask, render_template, request, redirect, jsonify,
                   url_for, flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base

# Imports for login
from flask import session as login_session
import random
import string

# Imports for handling login call back
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret_292740499331-2ch9hgkl9bssbbcl3hgqr4scgn60mhid.apps.'
         'googleusercontent.com.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:fr3Ed0@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a state token to prevent request forgery
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.
                    digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Route for home page of application
@app.route("/")
@app.route("/catalog")
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    latestitems = session.query(Item).order_by(Item.id.desc()).limit(10)
    return render_template('catalog.html', categories=categories,
                           latestitems=latestitems)


# Login with google account
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade the authorization code into a credential object
        oauth_flow = flow_from_clientsecrets('client_secret_292740499331-2ch9h'
                                             'gkl9bssbbcl3hgqr4scgn60mhid.apps'
                                             '.googleusercontent.com.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the \
        authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match \
        given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match \
        app's."), 401)
        print "Token's client ID does not match app's"
        response.headers['Content-Type'] = 'application/json'
        return reponse
    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
        connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user Info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id
    output = ''
    output += 'Welcome, '
    output += login_session["username"]
    output += '!</br>'
    output += '<img src="'
    output += 'static/ajax-loader.gif'
    output += ' " style = "width: 30px; height: 30px;">'
    flash("Successfully logged in as %s" % login_session['username'])
    return output


# Disconnect user from google account
@app.route("/gdisconnect")
def gdisconnect():
    # Only disconnec a logged in user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not logged in'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully logged out.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid
        response = make_response(json.dumps('Failed to revoke token for given \
        user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Login with Facebook account
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    # Exchange client token for long-lived server-side token
    app_id = json.loads(open('fb_client_secrets.json',
                             'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json',
                                 'r').read())['web']['app_secret']
    url = ('https://graph.facebook.com/v2.11/oauth/access_token?'
           'grant_type=fb_exchange_token&client_id=%s&client_secret=%s'
           '&fb_exchange_token=%s' % (app_id, app_secret, access_token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print url
    print result
    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.11/me'
    data = json.loads(result)
    token = 'access_token=' + data['access_token']

    url = 'https://graph.facebook.com/v2.11/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Get user picture
    url = ('https://graph.facebook.com/v2.11/me/picture?%s&'
           'redirect=0&height=200&width=200' % token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += 'Welcome, '
    output += login_session["username"]

    output += '!</br>'
    output += '<img src="'
    output += 'static/ajax-loader.gif'
    output += ' " style = "width: 30px; height: 30px;">'
    flash("Successfully logged in as %s" % login_session['username'])
    return output


# Disconnect user from facebook account
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


# Disconnect user - Revoke the user's token and reset their login_session
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in!")
        return redirect(url_for('showCatalog'))


# Route for category page
@app.route("/catalog/<int:category_id>")
@app.route("/catalog/<int:category_id>/items")
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return render_template('category.html', items=items, category=category)


# Route for item page
@app.route("/catalog/<int:category_id>/item/<int:item_id>")
def showItem(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return render_template('publicitem.html', item=item,
                               category_id=category_id)
    else:
        return render_template('item.html', item=item, category_id=category_id)


# Route for adding a new item
@app.route("/catalog/item/new", methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=request.form['category'], user_id='1')
        session.add(newItem)
        session.commit()
        flash("New Item Successfully Created - %s!" % newItem.name)
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('newitem.html', categories=categories)


# Route for editing an existing item
@app.route("/catalog/<int:category_id>/item/<int:item_id>/edit",
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Updated - %s' % editedItem.name)
            return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).order_by(asc(Category.name))
        return render_template('edititem.html', item=editedItem,
                               categories=categories)


# Route for deleting an existing item
@app.route("/catalog/<int:category_id>/item/<int:item_id>/delete",
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    deletedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("Item Successfully Deleted!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteitem.html', item=deletedItem)


# Route for category JSON API endpoint
@app.route("/catalog/<int:category_id>/JSON")
@app.route("/catalog/<int:category_id>/items/JSON")
def catalogJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


# Route for item JSON API endpoint
@app.route("/catalog/<int:category_id>/item/<int:item_id>/JSON")
def itemJSON(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=item.serialize)


# Get user ID
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Get user Info
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Create a user
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
