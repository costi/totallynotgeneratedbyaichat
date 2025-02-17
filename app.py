from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Import models after db initialization
from models import User, Room, Message

# Create initial General room if it doesn't exist
with app.app_context():
    db.create_all()
    if not Room.query.filter_by(name="General").first():
        general_room = Room(name="General")
        db.session.add(general_room)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('message', {'message': 'Connected to server'})
    # Send list of rooms on connect
    rooms = [room.name for room in Room.query.all()]
    emit('rooms', {'rooms': rooms})
    # Automatically join General room
    general_room = Room.query.filter_by(name="General").first()
    if general_room:
        join_room("General")
        messages = Message.query.filter_by(room_id=general_room.id).order_by(Message.timestamp.desc()).limit(50).all()
        for msg in reversed(messages):
            author = User.query.get(msg.user_id)
            message_data = {
                'messageText': msg.content,
                'room': "General",
                'username': author.username if author else 'Anonymous'
            }
            emit('message', {'message': message_data})
        emit('message', {'message': f"Joined room: General"})

@socketio.on('message')
def handle_message(data):
    if 'message' in data:
        message_data = data['message']
        room_name = message_data.get('room')
        if room_name:
            room = Room.query.filter_by(name=room_name).first()
            if room:
                # Get or create user
                username = message_data.get('username', 'Anonymous')
                user = User.query.filter_by(username=username).first()
                if not user:
                    user = User(username=username)
                    db.session.add(user)
                    db.session.commit()  # Commit to get user.id

                # Create and save message
                message = Message(
                    content=message_data.get('messageText'),
                    user_id=user.id,
                    room_id=room.id
                )
                db.session.add(message)
                db.session.commit()

                # Broadcast message only to the specific room
                emit('message', {'message': message_data}, to=room_name)

@socketio.on('new_username')
def handle_username(data):
    if 'username' in data:
        username = data['username']
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        emit('message', {'message': f"Username changed to {username}"})

@socketio.on('create_room')
def handle_create_room(data):
    if 'room_name' in data:
        room_name = data['room_name'].strip()
        if not room_name:
            return

        # Case insensitive search for existing room
        existing_room = Room.query.filter(Room.name.ilike(room_name)).first()
        if not existing_room:
            room = Room(name=room_name)
            db.session.add(room)
            try:
                db.session.commit()
                rooms = [room.name for room in Room.query.all()]
                emit('rooms', {'rooms': rooms}, broadcast=True)
                # Join the newly created room
                join_room(room_name)
                # Send room history signal first
                emit('clear_room_history')
                emit('message', {'message': f"Created and joined room: {room_name}"})
                # Tell client to update current room
                emit('room_joined', {'room': room_name})
            except Exception as e:
                db.session.rollback()
                emit('message', {'message': f"Error creating room: {str(e)}"})
        else:
            emit('message', {'message': f"Room '{room_name}' already exists"})

@socketio.on('join_room')
def handle_join_room(data):
    if 'room_name' in data:
        room_name = data['room_name']
        room = Room.query.filter_by(name=room_name).first()
        if room:
            # Leave all other rooms first
            for r in Room.query.all():
                leave_room(r.name)
            # Join the new room
            join_room(room_name)
            # Send room history signal first
            emit('clear_room_history')
            # Then send last 50 messages from room
            messages = Message.query.filter_by(room_id=room.id).order_by(Message.timestamp.desc()).limit(50).all()
            for msg in reversed(messages):
                author = User.query.get(msg.user_id)
                message_data = {
                    'messageText': msg.content,
                    'room': room_name,
                    'username': author.username if author else 'Anonymous'
                }
                emit('message', {'message': message_data})
            emit('message', {'message': f"Joined room: {room_name}"})
            # Tell client to update current room
            emit('room_joined', {'room': room_name})

@socketio.on('list_rooms')
def handle_list_rooms():
    rooms = [room.name for room in Room.query.all()]
    emit('rooms', {'rooms': rooms})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)