import pytest
from app import db
from models import User, Room, Message

def test_connect(socket_client):
    """Test client connection and initial room setup"""
    received = socket_client.get_received()
    assert len(received) > 0
    assert any(event['name'] == 'message' and 'Connected to server' in str(event['args']) for event in received)
    assert any(event['name'] == 'rooms' for event in received)

def test_create_and_join_room(socket_client):
    """Test room creation and joining"""
    # Create a new room
    socket_client.emit('create_room', {'room_name': 'Test Room'})
    received = socket_client.get_received()
    
    # Verify room creation messages
    assert any(event['name'] == 'rooms' for event in received)
    assert any(
        event['name'] == 'message' and 
        'Created and joined room: Test Room' in str(event['args'])
        for event in received
    )
    
    # Verify room_joined event
    assert any(
        event['name'] == 'room_joined' and 
        event['args'][0]['room'] == 'Test Room'
        for event in received
    )

def test_message_isolation(socket_client):
    """Test that messages only appear in their designated rooms"""
    # Create two rooms
    socket_client.emit('create_room', {'room_name': 'Room1'})
    socket_client.get_received()  # Clear received messages
    
    socket_client.emit('create_room', {'room_name': 'Room2'})
    socket_client.get_received()  # Clear received messages
    
    # Send message to Room1
    socket_client.emit('message', {
        'message': {
            'messageText': 'Hello Room1',
            'room': 'Room1',
            'username': 'TestUser'
        }
    })
    
    received = socket_client.get_received()
    messages_in_room1 = [
        event for event in received
        if event['name'] == 'message' and 
        isinstance(event['args'][0].get('message'), dict) and
        event['args'][0]['message'].get('messageText') == 'Hello Room1'
    ]
    
    assert len(messages_in_room1) == 1

def test_username_persistence(socket_client):
    """Test username changes and message attribution"""
    # Change username
    socket_client.emit('new_username', {'username': 'TestUser'})
    received = socket_client.get_received()
    
    assert any(
        event['name'] == 'message' and 
        'Username changed to TestUser' in str(event['args'])
        for event in received
    )
    
    # Send message and verify username
    socket_client.emit('message', {
        'message': {
            'messageText': 'Test Message',
            'room': 'General',
            'username': 'TestUser'
        }
    })
    
    received = socket_client.get_received()
    assert any(
        event['name'] == 'message' and 
        event['args'][0]['message'].get('username') == 'TestUser'
        for event in received
    )

def test_room_filtering(socket_client):
    """Test room creation and listing"""
    # Create multiple rooms
    room_names = ['TestRoom1', 'TestRoom2', 'AnotherRoom']
    for room_name in room_names:
        socket_client.emit('create_room', {'room_name': room_name})
        socket_client.get_received()
    
    # Request room list
    socket_client.emit('list_rooms')
    received = socket_client.get_received()
    
    # Verify all rooms are listed
    room_list_events = [event for event in received if event['name'] == 'rooms']
    assert len(room_list_events) == 1
    
    rooms = room_list_events[0]['args'][0]['rooms']
    assert 'General' in rooms
    for room_name in room_names:
        assert room_name in rooms
