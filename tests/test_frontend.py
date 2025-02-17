import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_message_input_focus(selenium, live_server):
    """Test that message input receives focus after various actions"""
    selenium.get(live_server.url)
    
    # Wait for page to load and WebSocket to connect
    WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, "connection-status"))
    )
    
    # Test focus after room creation
    new_room_input = selenium.find_element(By.ID, "new-room-input")
    new_room_input.send_keys("TestRoom")
    create_room_btn = selenium.find_element(By.ID, "create-room-btn")
    create_room_btn.click()
    
    # Verify message input has focus
    active_element = selenium.switch_to.active_element
    assert active_element.get_attribute("id") == "message-input"
    
    # Test focus after username change
    username_input = selenium.find_element(By.ID, "username-input")
    username_input.send_keys("TestUser")
    change_username_btn = selenium.find_element(By.ID, "change-username-btn")
    change_username_btn.click()
    
    # Verify message input has focus
    active_element = selenium.switch_to.active_element
    assert active_element.get_attribute("id") == "message-input"

def test_room_filtering(selenium, live_server):
    """Test room filtering and keyboard navigation"""
    selenium.get(live_server.url)
    
    # Create test rooms
    new_room_input = selenium.find_element(By.ID, "new-room-input")
    create_room_btn = selenium.find_element(By.ID, "create-room-btn")
    
    test_rooms = ["TestRoom1", "TestRoom2", "AnotherRoom"]
    for room in test_rooms:
        new_room_input.send_keys(room)
        create_room_btn.click()
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "room-item"))
        )
    
    # Test room filtering
    new_room_input.send_keys("Test")
    room_suggestions = WebDriverWait(selenium, 10).until(
        EC.presence_of_element_located((By.ID, "room-suggestions"))
    )
    
    suggestion_items = room_suggestions.find_elements(By.CLASS_NAME, "room-suggestion-item")
    assert len(suggestion_items) == 2  # Should show TestRoom1 and TestRoom2
