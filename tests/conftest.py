import os
import pytest
from app import app, db, socketio
from models import User, Room, Message

@pytest.fixture
def test_app():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    return app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def test_db():
    # Set up the database
    with app.app_context():
        db.create_all()
        
        # Create test data
        if not Room.query.filter_by(name="General").first():
            general_room = Room(name="General")
            db.session.add(general_room)
            db.session.commit()
    
    yield db
    
    # Clean up after tests
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def socket_client(test_app, test_db):
    test_client = socketio.test_client(test_app)
    return test_client
