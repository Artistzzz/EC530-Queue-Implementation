import json
import pika
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from pydantic import BaseModel, Field, ValidationError
import threading

'''
Python Flask application with integrated RabbitMQ for handling sensor data messages from various devices in self-driving robot project. 
The application uses the Flask framework for the API, Pika for RabbitMQ interaction, and includes endpoints to receive sensor data, 
enqueue it for processing, and a worker to process the messages from the queue.

'''

# Flask app initialization
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-very-secret-key'  # Change this in production!
jwt = JWTManager(app)

# Mock databases for demonstration
navigation_modules = {}
collision_avoidance_modules = {}
nav_id_counter = 1
ca_id_counter = 1

# Setup RabbitMQ connection
def get_rabbit_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

# Ensure the queue exists
def setup_queue():
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue='sensor_data_queue', durable=True)
    connection.close()

setup_queue()  # Initialize the queue when the app starts

# Increment IDs
def increment_nav_id():
    global nav_id_counter
    nav_id_counter += 1
    return nav_id_counter

def increment_ca_id():
    global ca_id_counter
    ca_id_counter += 1
    return ca_id_counter

# Data models using Pydantic for validation
class NavigationData(BaseModel):
    name: str
    version: str
    parameters: dict = Field(..., example={"accuracy": "high", "speed": "fast"})

class CollisionAvoidanceData(BaseModel):
    name: str
    sensor_type: str
    settings: dict = Field(..., example={"sensitivity": "high", "range": "100m"})

# Routes for API
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username == 'admin' and password == 'secret':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"msg": "Bad username or password"}), 401

@app.route('/sensor-data', methods=['POST'])
def handle_sensor_data():
    data = request.json
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.basic_publish(
        exchange='',
        routing_key='sensor_data_queue',
        body=json.dumps(data),
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )
    connection.close()
    return jsonify({'message': 'Data queued for processing'}), 202

def process_sensor_data(body):
    data = json.loads(body)
    print("Processed sensor data:", data)

def sensor_data_worker():
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue='sensor_data_queue', durable=True)

    def callback(ch, method, properties, body):
        process_sensor_data(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='sensor_data_queue', on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

# Run the worker in a separate thread
threading.Thread(target=sensor_data_worker, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)