from flask import Flask, render_template, redirect, url_for, request, jsonify, session
from flask import make_response
import os.path
import os
import json
import re

from datetime import datetime
from flask_cors import CORS

import pymongo
from pymongo import MongoClient
from flask_pymongo import PyMongo,pymongo
from flask_mongoengine import MongoEngine
# from flask import JSONEncoder

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

# DB import
from flask_pymongo import PyMongo,pymongo

# from business.scheduler_handler import 
from flask_apscheduler import APScheduler
# scheduler methods import
import time
from flask import Blueprint

api = Blueprint('parking_api_bp', __name__)

app = Flask(__name__)

app.register_blueprint(api)

app.config["MONGO_URI"] = "mongodb+srv://sanjeyts06:sanjeyts06@cluster0.vb546.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


app.config['MONGODB_SETTINGS'] = {
    'db': 'parking',
    'host': app.config["MONGO_URI"]
}

mongo = PyMongo(app)
bcrypt = Bcrypt()
CORS(app)


scheduler = APScheduler()
scheduler.init_app(app)

mongo  = PyMongo(app)

# Setup Mongo Engine
db = MongoEngine()
db.init_app(app)

app.secret_key = 'enjaamiTale$eFennelda$S'
SESSION_ID_KEY = "sid"

UPLOAD_FOLDER = 'static/uploads/'


cluster = MongoClient('mongodb+srv://sanjeyts06:sanjeyts06@cluster0.vb546.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

db = cluster["parking"]

def is_session_valid():

    if(SESSION_ID_KEY in session):
        return True

    return False

def get_sid():

    return session.get(SESSION_ID_KEY, None)


def get_userid():

    return session.get("user_id", None)

@app.route('/', methods=['GET', 'POST'])
def page_index():
    logged_in = is_session_valid()

    user_id = get_userid()
    # tlogger.info("logged_in", logged_in)
    return render_template( 
        'tasks.html', logged_in=logged_in,user_id = user_id
    )

@app.route('/login', methods=['GET'])
def page_login_get():  

    if(is_session_valid()):

        user_id = get_userid()
        
        resp = make_response(redirect(url_for('page_index')))
        resp.set_cookie('user_id', str(user_id))
        return resp
    
    return render_template(
        'login.html'
    )


from flask_bcrypt import Bcrypt

import base64
import binascii

bcrypt = Bcrypt()

def hash_password(password):

    return bcrypt.generate_password_hash(password)

def match_password(db_password, password):

    return bcrypt.check_password_hash(db_password, password)

def encode_base(message):
    
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('ascii')
    return base64_message

def decode_base(base64_message):

    base64_bytes = base64_message.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('ascii')
   
    return message

F13R_SALT           = "ontea_tct_pullakai"
EXPIRE_TIME_MINUTES = 20

VALID_SESSION      = 0
BROKEN_SESSION_ID  = 1
SESSION_EXPIRED    = 2
IP_MISMATCH        = 3
USERID_MISMATCH    = 4
INVALID_SESSION_ID = 5

import socket

def get_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip

import datetime
import time


def get_current_time_millis():

    millis = int(round(time.time() * 1000))

    return millis

def get_session_base(userid):

    ip = get_ip()
    current_time_millis = get_current_time_millis()
    expire_time_millis = current_time_millis + (EXPIRE_TIME_MINUTES * 60 * 1000)

    session_base = ip + '_' + str(userid) + '_' + str(expire_time_millis) + '_' + F13R_SALT 
    session_base_end = encode_base(session_base)

    return session_base_end

def validate_sessionid(sid):
    """
        Session Format:
        ip_userid_expireat_salt

        result:
        0 - valid session
        1 - broken session id
        2 - sessoin expired
        3 - ip mismatch
        4 - userid mismatch
        5 - invalid session id

    """

    if(sid is None):
        return False, INVALID_SESSION_ID

    decoded_session_id = decode_base(sid)

    # 1 - broken session id
    if(not decoded_session_id):
        return False, BROKEN_SESSION_ID

    # 1 - broken session id
    if('_' not in decoded_session_id):
        return False, BROKEN_SESSION_ID

    session_parts = decoded_session_id.split('_')

    userid = int(session_parts[1])

    # 4 - userid mismatch
    # TODO: Please fix this later
    '''
    if(userid != SAMPLE_USERID):
        return False, USERID_MISMATCH
    '''

    session_userip = session_parts[0]

    # 3 - ip mismatch
    ip = get_ip()
    if(session_userip != ip):
        return False, IP_MISMATCH

    # check session whether it is expired or not
    future_expire_millis = int(session_parts[2])
    current_time_millis =get_current_time_millis()

    seconds_left = (future_expire_millis - current_time_millis) / 1000

    # 2 - sessoin expired
    if(seconds_left < 0):
        return False, SESSION_EXPIRED

    return True, VALID_SESSION


def created_sessionid(userid):

    return get_session_base(userid)

def get_userid_from_sid(sid):

    decoded_session_id = decode_base(sid)

    session_parts = decoded_session_id.split('_')

    userid = int(session_parts[1])

    return userid

def login_user(username,password):
    col = db["user_details"]
    user_creds = col.find_one({"email" : username})

    if (user_creds is None):
        return "user does not exist"
    

    if (not match_password(user_creds['password'], password)):
        return "invalid password"
    
    user_id           = user_creds['user_id']
    user_name         = user_creds['firstname'] + " " + user_creds['lastname'] 
    authenticated     = 'Authentication successful'
    session['userid'] = user_creds['user_id']
    # is_mentor          = user_creds["user_role"]

    sid = created_sessionid(user_id)

    result_dict = {
        "username" : user_name,
        "user_id" : user_id,
        # "user_role" : is_mentor,
        "authenticated" : authenticated,
        "sid" : sid
    }

    return result_dict

@app.route('/logout', methods=['GET'])
def page_logout_get():

    if(SESSION_ID_KEY in session):
        del session[SESSION_ID_KEY]

    resp = make_response(redirect(url_for('page_login_get')))

    resp.set_cookie('user_id', '', expires=0)

    return resp

@app.route('/login', methods=['POST'])
def page_login_post():

    username    = request.values.get('email')
    password    = request.values.get('password')

    result_json = login_user(username, password)
    logged_in   = is_session_valid()
    session[SESSION_ID_KEY] = result_json['sid']
    session["user_id"]      = result_json['user_id']
    result                  = result_json

    user_id = get_userid()
    try:
        session['redirect_url'] = "/"
        resp = make_response(redirect(session["redirect_url"]))
    except:
        resp = make_response(redirect(url_for('/')))

    resp.set_cookie('user_id', str(user_id))
   
    return resp

def get_last_user_id():

    col = db["user_details"]

    last_user_id      = col.find().sort([('user_id',-1)]).limit(1)

    try:
        last_user_id = last_user_id[0]['user_id']
    except:
        last_user_id = 0

    return last_user_id

@app.route('/signup', methods=['POST'])
def page_signup_post():

    col = db["user_details"]

    lastname  = request.values.get('lastname')
    firstname = request.values.get('firstname')
    email     = request.values.get('email')
    password  = request.values.get('password')
    mobile    = request.values.get('mobile')
    confpassword = request.values.get('confpassword') 

    # if(confpassword!=password):
    #     return "password doesn't match"
    user_id = get_last_user_id()

    new_user_id = user_id + 1

    logged_in = is_session_valid()

    hashpass        = hash_password(password)

    existing_user = get_user_by_email(email)

    if existing_user:

        return "user already exists"
    
    user_dict = {
        "user_id"  : new_user_id,
        "lastname" : lastname,
        "firstname": firstname,
        "email"    : email,
        "password" : hashpass,
        "mobile"   : mobile
    }

    col.insert_one(user_dict)

    return "Signed up successfully"

@app.route('/signup', methods=['GET'])
def page_signup_get():

    return render_template(
        'sign_up.html'
    )

@app.route('/test', methods=['GET'])
def test():

    return "hiii"

@app.route('/get/user/details', methods=['GET'])
def get_user_details_ui():

    user_details = get_user_details()

    return render_template("user-details.html", user_details = user_details)

def get_user_by_email(email):

    col = db["user_details"]

    user_dict = {
        "email" : email
    }

    user_obj = col.find_one(user_dict)

    return user_obj

def get_user_details():

    col = db["user_details"]

    user_id = get_userid()

    s_id = get_sid()

    user_details = col.find_one({"user_id":int(user_id)},{"_id":False,"password":False})

    return user_details

JS_FILE_PATH = "static/js/leaflet_map/leaflet_markers.js"

@app.route('/admin/add')
def admin():
    return render_template('add_marker.html')

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def get_lat_long(address):
    # Initialize the geolocator
    geolocator = Nominatim(user_agent="geoapi")

    try:
        # Get the location
        location = geolocator.geocode(address)
        
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except GeocoderTimedOut:
        return None, None

    # Example Usage

@app.route('/test/loc')
def test_loc():

    loc = "10, Timsbury walk, roehampton, london"

    address = "10, Timsbury walk, roehampton, london"
    latitude, longitude = get_lat_long(address)

    if latitude and longitude:
        print(f"The latitude and longitude of the address are {latitude}, {longitude}")
    else:
        print("Could not retrieve the coordinates.")
    
    return 'noob'
    


@app.route('/add_marker', methods=['POST'])
def add_marker():

    # loc = "10, Timsbury walk, roehampton, london"

    # address = "10, Timsbury walk, roehampton, london"
    # latitude, longitude = get_lat_long(address)

    # if latitude and longitude:
    #     print(f"The latitude and longitude of the address are {latitude}, {longitude}")
    # else:
    #     print("Could not retrieve the coordinates.")
    address = request.form.get("address")
    latitude, longitude = get_lat_long(address)
    new_marker = {
        "id": int(request.form.get("id")),
        "type_point": request.form.get("type_point"),
        "location_latitude": float(latitude),
        "location_longitude": float(longitude),
        "map_image_url": request.form.get("map_image_url"),
        "rate": request.form.get("rate"),
        "name_point": request.form.get("name_point"),
        "get_directions_start_address": request.form.get("get_directions_start_address", ""),
        "phone": request.form.get("phone"),
        "url_point": request.form.get("url_point")
    }

    try:
        with open(JS_FILE_PATH, 'r+') as js_file:
            content = js_file.read()

            start = content.find("[")
            end = content.rfind("]") + 1

            if start == -1 or end == -1:
                return jsonify({"success": False, "error": "Malformed JavaScript file"})

            markers_data = json.loads(content[start:end])

            markers_data.append(new_marker)

            new_content = content[:start] + json.dumps(markers_data, indent=4) + content[end:]

            js_file.seek(0)
            js_file.write(new_content)
            js_file.truncate()

        return jsonify({"success": True, "marker": new_marker})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5053, debug=True)     