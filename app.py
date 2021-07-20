from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import urllib
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId

app = Flask(__name__)
app.config['SECRET_KEY'] = "SECRETKEYFORAPP"
app.config['MONGO_URI'] = 'mongodb+srv://' + urllib.parse.quote_plus('manoj2rox') + ':'+urllib.parse.quote_plus(
    'Manu@2020') + '@cluster0.tymuz.mongodb.net/spiceblue?retryWrites=true&w=majority'

mongo = PyMongo(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers['Authorization']
        token = token.split()[1]
        print(token)
        if not token:
            return jsonify({"message": 'Token is missing'}), 403
        try:
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms="HS256")
            print(data)
        except Exception as ex:
            return jsonify({'message': str(ex)}), 403
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@token_required
def home():
    return {'message': "protected with token"}


@app.route('/register', methods=['POST'])
def create_user():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()

        user = mongo.db.users.find_one({"email": data['email']})
        if not user:
            hashed_pwd = generate_password_hash(data['password'])
            inserted_user = mongo.db.users.insert_one(
                {'first_name': data['first_name'],
                 'last_name': data['last_name'],
                 'email': data['email'],
                 'password': hashed_pwd
                 })
            res_data = {"_id": str(inserted_user.inserted_id)}
            code = 201
            status = "success"
            message = "User Created"
        else:
            message = "Email Already exists"
            status = 'fail'
            code = 409
    except Exception as ex:
        message = str(ex)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/login', methods=['POST'])
def login():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        user = mongo.db.users.find_one({"email": data['email']})
        if user:
            user['_id'] = str(user['_id'])
            if user and check_password_hash(user['password'], data['password']):
                time = datetime.utcnow() + timedelta(minutes=30)
                token = jwt.encode(
                    {'email': data['email'], 'exp': time}, app.config['SECRET_KEY'])
                del user['password']
                message = f"user Authenticated"
                code = 200
                status = "successful"
                res_data['token'] = token
            else:
                message = "invalid login details"
                code = 401
                status = "fail"
        else:
            message = "Invalid login details"
            code = 401
            status = "fail"
    except Exception as ex:
        print(ex)
        message = f"{ex}"
        code = 500
        status = "fail"
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/template', methods=['POST'])
@token_required
def create_template():
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        template_collection = mongo.db.templates
        found_template = template_collection.find_one(
            {"template_name": data['template_name'], "subject": data['subject'], 'body': data['body']})
        if not found_template:
            inserted_template = template_collection.insert_one(
                {"template_name": data['template_name'], "subject": data['subject'], 'body': data['body']})
            res_data = {"_id": str(inserted_template.inserted_id)}
            code = 201
            message = "successfully created"
        else:
            message = "template Already exists"
            status = 'fail'
            code = 409
    except Exception as err:
        message = str(err)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/template', methods=['GET'])
@token_required
def get_all_templates():
    message = ""
    res_data = []
    code = 500
    status = "fail"
    try:
        template_collection = mongo.db.templates
        all_templates = list(template_collection.find())
        for template in all_templates:
            template['_id'] = str(template['_id'])
        res_data = all_templates
        code = 201
        status = 'success'
        message = 'successfully retrieved all the templates'
    except Exception as err:
        message = str(err)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/template/<template_id>', methods=['GET'])
@token_required
def get_template_by_id(template_id):
    message = ""
    res_data = []
    code = 500
    status = "fail"
    try:
        template_collection = mongo.db.templates
        found_template = template_collection.find_one(
            {'_id': ObjectId(template_id)})
        if found_template:
            found_template['_id'] = str(found_template['_id'])
            res_data = found_template
            code = 201
            status = 'success'
            message = 'found the template'
        else:
            code = 404
            status = "fail"
            message = "template not found"
    except Exception as err:
        message = str(err)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/template/<template_id>', methods=['PUT'])
@token_required
def update_template_by_id(template_id):
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        data = request.get_json()
        template_collection = mongo.db.templates
        found_template = template_collection.find_one(
            {'_id': ObjectId(template_id)})
        if not found_template:
            code = 404
            status = "fail"
            message = "template not found"
        else:

            template_collection.update_one(
                {'_id': ObjectId(template_id)},
                {'$set': {"template_name": data['template_name'],
                          "subject": data['subject'], "body": data['body']}}
            )
            code = 200
            status = "success"
            message = "template has been updated"
    except Exception as err:
        message = str(err)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.route('/template/<template_id>', methods=['DELETE'])
@token_required
def delete_template_by_id(template_id):
    message = ""
    res_data = {}
    code = 500
    status = "fail"
    try:
        template_collection = mongo.db.templates
        found_template = template_collection.find_one(
            {'_id': ObjectId(template_id)})
        if not found_template:
            code = 404
            status = "fail"
            message = "template not found"
        else:
            template_collection.delete_one({"_id": found_template['_id']})
            code = 200
            status = "success"
            message = "template has been deleted"
    except Exception as err:
        message = str(err)
    return jsonify({'status': status, "data": res_data, "message": message}), code


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'message': 'Resource not found ' + request.url,
        'status': 404
    }
    response = jsonify(message)
    response.status_code = 404
    return response


if __name__ == '__main__':
    app.run(debug=True)
