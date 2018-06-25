from user_model import Base, User, Request, Proposal

from flask import Flask, jsonify, request, url_for, abort, g, render_template
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

#from flask.ext.httpauth import HTTPBasicAuth
import json

#NEW IMPORTS
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests

#auth = HTTPBasicAuth()


engine = create_engine('sqlite:///User.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__) 

# Create the appropriate app.route functions, 
#test and see if they work



#How can we include token? what is ID, what is the purpose of ID? Does token return an id?


def verify_password(username_or_token, password):
    #Try to see if it's a token first 
    user_id = User.verify_auth_token(username_or_token)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

@app.route('/api/v1/<provider>/login', methods = ['POST'])
def login(provider):
    #STEP 1 - Parse the auth code
    auth_code = request.json.get('auth_code')
    if provider == 'google':
        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
          
        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        #STEP 3 - Find User or make a new one
        
        #Get user info
        h = httplib2.Http()
        userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)
      
        data = answer.json()

        picture = data['picture']
        email = data['email']
        
        
     
        #see if user exists, if it doesn't make a new one
        user = session.query(User).filter_by(email = email).first()
        if not user:
            user = User(picture = picture, email = email)
            session.add(user)
            session.commit()

        #STEP 4 - Make token
        token = user.generate_auth_token(600)

        

        #STEP 5 - Send back token to the client 
        return jsonify({'token': token.decode('ascii')})
        
        #return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'
#@app.route('api/v1/<provider>/logout', method = ['POST'])
#def log_out (token):

@app.route('/token')
#@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})

@app.route('/api/v1/users', methods = ['GET'])
def get_user_all(token):
    user_id = User.verify_auth_token(token)
    if user_id:
        users = session.query(User).all()
        return jsonify(Users=[i.serialize for i in users])
    else:
        print "token is not available"
        return jsonify(), 400


@app.route('/api/v1/users', methods = ['POST'])
def new_user():
    email_u = request.json.get('email')
    password = request.json.get('password')
    picture = request.json.get('picture')
    if email_u is None or password is None:
        print "missing arguments"
        return jsonify(), 400
        
    if session.query(User).filter_by(email = email_u).first() is not None:
        print "existing user"
        user = session.query(User).filter_by(email = email_u).first()
        return jsonify({'message':'user already exists'}), 200
    user = User(email = email_u)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return jsonify({ 'username': user.email}), 201


@app.route('/api/v1/users', methods = ['PUT'])
def update_user(token):
    email_u = request.json.get('email')
    picture = request.json.get('picture')
    user_id = User.verify_auth_token(token)
    User = session.query(User).filter_by(id = user_id).one()
    User.email = email
    User.picture = picture
    session.add(User)
    session.commit()

@app.route('/api/v1/users/<int:id>', methods = ['GET'])
def get_user(token):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id=user_id).one()
    if not user:
        abort(400)
    return jsonify(user.serialize)

# @app.route('/api/v1/dats/<int:id>')
# def test(id):
#   getuser(id)

@app.route('/api/v1/users', methods = ['DELETE'])
def delete_user(token):
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        session.delete(user)
        session.commit()
    else:
        return jsonify(), 400


@app.route('/api/v1/requests', methods = ['GET'])
def get_all_request(token):
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        requests = session.query(Request).all()
        return jsonify(Requests = [i.serialize for i in users])
    else:
        return jsonify(), 400

@app.route('/api/v1/requests', methods = ['POST'])
def makes_new():
    user_id = 1
    meal_type = request.json.get('meal_type')
    location_string = request.json.get('location_string')
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    meal_time = request.json.get('meal_time')
        #filled = request.json.get('filled')
    requests = session.query(Request).filter_by(user_id = user_id).first()
    if requests:
        requests.meal_type = meal_type
        requests.location_string = location_string
        requests.latitude = latitude
        requests.longiture = longitude
        requests.meal_time = mean_time
            #request.filled = filled
        session.add(requests)
        session.commit()
    else:
        requests = Request(meal_type = meal_type, location_string = location_string, \
              user_id = user_id, latitude= latitude, longitude = longitude, \
              meal_time = meal_time)
        session.add(requests)
        session.commit()
    # token = request.args.get('token')
    #user_id = User.verify_auth_token(token)
    #user = session.query(User).filter_by(id = user_id).one()
    #if user:
    """
        meal_type = request.json.get('meal_type')
        location_string = request.json.get('location_string')
        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')
        meal_time = request.json.get('meal_time')
        #filled = request.json.get('filled')
        request = session.query(Request).filter_by(user_id = user_id).one()
        if request:
            request.meal_type = meal_type
            request.location_string = location_string
            request.latitude = latitude
            request.longiture = longitude
            request.meal_time = mean_time
            #request.filled = filled
            sesson.add(request)
            session.commit()
        else:
            request = Request(meal_type = meal_type, location_string = location_string, \
              user_id = user_id, latitude= latitude, longitude = longitude, \
              meal_time = meal_time, filled = filled)
    """
    #else:
    return jsonify(), 400

@app.route('/api/v1/requests/<int:id>', methods = ['GET'])
def get_specific(id):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        request = session.query(Request).filter_by(id = id).one()
        if request:
            return jsonify(request.serialize)
        else:
            return jsonify(), 400
    else:
        return jsonify(), 400


@app.route('/api/v1/requests/<int:id>', methods = ['PUT'])
def up_meetup(id):
    token = request.args.get('token')
    user_id = user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    request = session.query(Request).filter_by(id = id).one()
    if request:
        if user:
            if user_id == request.user_id:
                meal_type = request.json.get('meal_type')
                location_string = request.json.get('location_string')
                latitude = request.json.get('latitude')
                longitude = request.json.get('longitude')
                meal_time = request.json.get('meal_time')
                filled = request.json.get('filled')
                request.meal_type = meal_type
                request.location_string = location_string
                request.latitude = latitude
                request.longiture = longitude
                request.meal_time = mean_time
                request.filled = filled
                sesson.add(request)
                session.commit()
            else:
                return jsonify(),400
        else:
            return jsonify(),400
    else:
        return jsonify(),400

@app.route('/api/v1/requests/<int:id>', methods = ['PUT'])
def delete_request(id):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    request = session.query(Request).filter_by(id = id).one()
    if request:
        if user:
            if user_id == request.user_id:
                session.delete(request)
                session.commit()
    token = request.args.get('token')
            else:
                return jsonify(),400
        else:
            return jsonify(),400
    else:
        return jsonify(),400

@app.route('/api/v1/proposals', methods = ['GET'])
def meet_up_proposal():
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    requests = session.query(Request).filter_by(user_id = user_id).all()
    proposals = []
    for i in requests:
        request_id = i.id
        proposal_user = session.query(Proposal).filter_by(request_id = request_id).one()
        proposals.append(proposal_user)
    return jsonify(Proposals = [i.serialize for i in proposals])

@app.route('/api/v1/proposals', methods = ['POST'])
def post_proposal():
    token = request.args.get('token')
    request_id = request.args.get('request_id')
    request_u = session.query(Request).filter_by(request_id = request_id).one()
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    user2 = session.query(User).filter_by(id = request_u.user_id)
    if user:
        proposals = Proposal(user_proposed_from = user.email, user_proposed_to = user2.email, request_id = request_id)
        session.add(proposals)
        session.commit()
    else:
        return jsonify(),400

@app.route('/api/v1/proposals/<int:id>', methods = ['GET'])
def get_proposal(id):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user1 = session.query(User).filter_by(id = user_id).first()
    if user1:
        user = session.query(User).filter_by(id = user_id).first()
        if session.query(Proposal).filter_by(user_proposed_to = user.email).first():
            propose = session.query(Proposal).filter_by(user_proposed_to = user.email).first()
        elif session.query(Proposal).filter_by(user_proposed_from = user.email).first():
            propose = session.query(Proposal).filter_by(user_proposed_from = user.email).first()
        return jsonify(propose.serialize)
    else:
        return jsonify(Proposals = [i.serialize for i in proposals])

@app.route('/api/v1/proposals/<int:id>', methods = ['PUT'])
def up_propose(id):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        propose = session.query(Proposal).filter_by(id = id).first()
        if user.email = propose.user_proposed_from:
            propose.user_proposed_from = user.email
            propose.user_proposed_to = request.json.get('user_proposed_to')
        else:
            return jsonify(), 400
    else:
        return jsonify(), 400

@app.route('/api/v1/proposals/<int:id>', methods = ['DELETE'])
def delete_propose(id):
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        propose = session.query(Proposal).filter_by(id = id).first()
        if user.email = propose.user_proposed_from:
            session.delete(propose)
            session.commit()
        else:
            return jsonify(), 400
    else:
        return jsonify(), 400

@app.route('/api/v1/dates', methods = ['GET'])
def get_date:
    token = request.args.get('token')
    user_id = User.verify_auth_token(token)
    user = session.query(User).filter_by(id = user_id).one()
    if user:
        user1 = session.query(MealDate).filter_by(user1 = user.email).all()
        user2 = session.query(MealDate).filter_by(user2 = user.email).all()
        if user1 and user2:
            user1.append(user2)
            return jsonify(users = [i.serialize for i in user1])
        elif user1:
            return jsonify(users = [i.serialize for i in user1])
        elif user2:
            return jsonify(users = [i.serialize for i in user2])
        else:
            return jsonify(),400
    else:
        return jsonify(),400
            

if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=5000)	