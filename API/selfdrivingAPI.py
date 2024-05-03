import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit
from werkzeug.exceptions import HTTPException
from pydantic import BaseModel, Field, ValidationError

app = Flask(__name__)

# Configuration for JWT
app.config['JWT_SECRET_KEY'] = 'your-very-secret-key'  # Change this in production!

# Initialize JWT and SocketIO
jwt = JWTManager(app)
socketio = SocketIO(app)

# Mock databases
navigation_modules = {}
collision_avoidance_modules = {}
nav_id_counter = 1
ca_id_counter = 1

# Logging setup
logging.basicConfig(level=logging.INFO)

def increment_nav_id():
    global nav_id_counter
    nav_id_counter += 1
    return nav_id_counter

def increment_ca_id():
    global ca_id_counter
    ca_id_counter += 1
    return ca_id_counter

class NavigationData(BaseModel):
    name: str
    version: str
    parameters: dict = Field(..., example={"accuracy": "high", "speed": "fast"})

class CollisionAvoidanceData(BaseModel):
    name: str
    sensor_type: str
    settings: dict = Field(..., example={"sensitivity": "high", "range": "100m"})

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'admin' or password != 'secret':
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@app.route('/navigation', methods=['POST'])
def create_navigation():
    try:
        data = NavigationData(**request.json)
    except ValidationError as e:
        return jsonify(error=str(e)), 400
    nav_id = increment_nav_id()
    navigation_modules[nav_id] = data.dict()
    return jsonify({'message': 'Navigation module created', 'id': nav_id}), 201

@app.route('/navigation/<int:nav_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def navigation_module(nav_id):
    if request.method == 'GET':
        module = navigation_modules.get(nav_id)
        if module:
            return jsonify(module)
        else:
            return jsonify({'message': 'Navigation module not found'}), 404
    elif request.method == 'PUT':
        try:
            updated_data = NavigationData(**request.json)
            navigation_modules[nav_id] = updated_data.dict()
            return jsonify({'message': 'Navigation module updated', 'data': updated_data.dict()})
        except ValidationError as e:
            return jsonify(error=str(e)), 400
    elif request.method == 'DELETE':
        if nav_id in navigation_modules:
            del navigation_modules[nav_id]
            return jsonify({'message': 'Navigation module deleted'})
        else:
            return jsonify({'message': 'Navigation module not found'}), 404

@app.route('/collision-avoidance', methods=['POST'])
def create_collision_avoidance():
    try:
        data = CollisionAvoidanceData(**request.json)
    except ValidationError as e:
        return jsonify(error=str(e)), 400
    ca_id = increment_ca_id()
    collision_avoidance_modules[ca_id] = data.dict()
    return jsonify({'message': 'Collision avoidance module created', 'id': ca_id}), 201

@app.route('/collision-avoidance/<int:ca_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def collision_avoidance_module(ca_id):
    if request.method == 'GET':
        module = collision_avoidance_modules.get(ca_id)
        if module:
            return jsonify(module)
        else:
            return jsonify({'message': 'Collision avoidance module not found'}), 404
    elif request.method == 'PUT':
        try:
            updated_data = CollisionAvoidanceData(**request.json)
            collision_avoidance_modules[ca_id] = updated_data.dict()
            return jsonify({'message': 'Collision avoidance module updated', 'data': updated_data.dict()})
        except ValidationError as e:
            return jsonify(error=str(e)), 400
    elif request.method == 'DELETE':
        if ca_id in collision_avoidance_modules:
            del collision_avoidance_modules[ca_id]
            return jsonify({'message': 'Collision avoidance module deleted'})
        else:
            return jsonify({'message': 'Collision avoidance module not found'}), 404

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    emit('response', {'data': 'Message received!'})

@app.errorhandler(404)
def resource_not_found(e):
    app.logger.error('Resource not found: %s', (request.path))
    return jsonify(error=str(e)), 404

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    app.logger.error('An error occurred: %s', str(e))
    return jsonify(error="An internal error occurred"), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)