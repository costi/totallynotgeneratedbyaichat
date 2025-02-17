class ChatClient {
    constructor() {
        this.ws = null;
        this.currentRoom = null;
        this.username = this.getSavedUsername() || 'Guest' + Math.floor(Math.random() * 1000);
        this.rooms = [];
        this.selectedRoomIndex = -1;
        this.shouldScrollToBottom = true;
        this.initializeElements();
        this.initializeEventListeners();
        this.connectWebSocket();
    }

    initializeElements() {
        // Status elements
        this.statusBadge = document.getElementById('status-badge');
        this.connectionStatus = document.getElementById('connection-status');

        // Input elements
        this.usernameInput = document.getElementById('username-input');
        this.messageInput = document.getElementById('message-input');
        this.newRoomInput = document.getElementById('new-room-input');

        // Buttons
        this.changeUsernameBtn = document.getElementById('change-username-btn');
        this.createRoomBtn = document.getElementById('create-room-btn');
        this.sendMessageBtn = document.getElementById('send-message-btn');

        // Containers
        this.roomList = document.getElementById('room-list');
        this.messageContainer = document.getElementById('message-container');
        this.currentRoomElement = document.getElementById('current-room');
        this.roomSuggestions = document.getElementById('room-suggestions');

        // Set initial username
        this.usernameInput.value = this.username;

        // Set up scroll listener
        this.messageContainer.addEventListener('scroll', () => {
            const { scrollTop, scrollHeight, clientHeight } = this.messageContainer;
            this.shouldScrollToBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 1;
        });
    }

    getSavedUsername() {
        return localStorage.getItem('chatUsername');
    }

    saveUsername(username) {
        localStorage.setItem('chatUsername', username);
    }

    changeUsername() {
        const newUsername = this.usernameInput.value.trim();
        if (!newUsername) return;

        this.ws.emit('new_username', {
            username: newUsername
        });
        this.username = newUsername;
        this.saveUsername(newUsername);
        // Focus message input after username change
        this.messageInput.focus();
    }

    createRoom() {
        const roomName = this.newRoomInput.value.trim();
        if (!roomName) return;

        this.ws.emit('create_room', {
            room_name: roomName
        });
        this.newRoomInput.value = '';
        this.roomSuggestions.classList.add('d-none');
        // Focus message input after room creation
        this.messageInput.focus();
    }

    connectWebSocket() {
        const socket = io(window.location.origin);
        this.ws = socket;

        socket.on('connect', () => {
            this.updateConnectionStatus(true);
            this.currentRoom = "General";
            this.currentRoomElement.textContent = "General";
            this.messageInput.disabled = false;
            this.sendMessageBtn.disabled = false;
        });

        socket.on('disconnect', () => {
            this.updateConnectionStatus(false);
        });

        socket.on('message', (data) => {
            if (data.message) {
                this.displayMessage(data.message);
            }
        });

        socket.on('rooms', (data) => {
            if (data.rooms) {
                this.rooms = data.rooms;
                this.updateRoomList(data.rooms);
            }
        });

        socket.on('clear_room_history', () => {
            this.clearMessageContainer();
        });

        socket.on('room_joined', (data) => {
            if (data.room) {
                this.currentRoom = data.room;
                this.currentRoomElement.textContent = data.room;
            }
        });
    }

    updateRoomSelection() {
        const suggestions = this.roomSuggestions.querySelectorAll('.room-suggestion-item');
        suggestions.forEach((item, index) => {
            item.classList.toggle('active', index === this.selectedRoomIndex);
        });
        if (this.selectedRoomIndex >= 0) {
            suggestions[this.selectedRoomIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    displayMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.username === this.username ? 'own-message' : ''}`;

        if (typeof message === 'string') {
            messageElement.innerHTML = `<div class="message-content system-message">${this.escapeHtml(message)}</div>`;
        } else {
            messageElement.innerHTML = `
                <div class="username">${this.escapeHtml(message.username)}</div>
                <div class="message-content">${this.escapeHtml(message.messageText)}</div>
            `;
        }

        this.messageContainer.appendChild(messageElement);
        if (this.shouldScrollToBottom) {
            this.scrollToBottom();
        }
    }

    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    getFilteredRooms() {
        const input = this.newRoomInput.value.toLowerCase().trim();
        return this.rooms.filter(room => room.toLowerCase().includes(input));
    }

    filterRooms() {
        const filteredRooms = this.getFilteredRooms();

        if (filteredRooms.length > 0 && this.newRoomInput.value.trim() !== '') {
            this.roomSuggestions.innerHTML = '';
            filteredRooms.forEach(room => {
                const suggestion = document.createElement('div');
                suggestion.className = 'room-suggestion-item';
                suggestion.textContent = room;
                suggestion.addEventListener('click', () => {
                    this.joinRoom(room);
                    this.newRoomInput.value = '';
                    this.roomSuggestions.classList.add('d-none');
                });
                this.roomSuggestions.appendChild(suggestion);
            });
            this.roomSuggestions.classList.remove('d-none');
        } else {
            this.roomSuggestions.classList.add('d-none');
        }
    }

    sendMessage() {
        const messageText = this.messageInput.value.trim();
        if (!messageText || !this.currentRoom) return;

        this.ws.emit('message', {
            message: {
                messageText: messageText,
                room: this.currentRoom,
                username: this.username
            }
        });
        this.messageInput.value = '';
    }


    initializeEventListeners() {
        // Username change
        this.changeUsernameBtn.addEventListener('click', () => this.changeUsername());
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.changeUsername();
        });

        // Room creation and filtering
        this.createRoomBtn.addEventListener('click', () => this.createRoom());
        this.newRoomInput.addEventListener('input', () => this.filterRooms());
        this.newRoomInput.addEventListener('keydown', (e) => {
            const filteredRooms = this.getFilteredRooms();
            if (filteredRooms.length > 0) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.selectedRoomIndex = Math.min(this.selectedRoomIndex + 1, filteredRooms.length - 1);
                    this.updateRoomSelection();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.selectedRoomIndex = Math.max(this.selectedRoomIndex - 1, 0);
                    this.updateRoomSelection();
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (this.selectedRoomIndex >= 0) {
                        this.joinRoom(filteredRooms[this.selectedRoomIndex]);
                    } else if (filteredRooms.length === 1) {
                        this.joinRoom(filteredRooms[0]);
                    } else {
                        this.createRoom();
                    }
                    this.newRoomInput.value = '';
                    this.roomSuggestions.classList.add('d-none');
                    this.selectedRoomIndex = -1;
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                this.createRoom();
                this.newRoomInput.value = '';
                this.roomSuggestions.classList.add('d-none');
            }
        });

        // Message sending
        this.sendMessageBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // Hide room suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.newRoomInput.contains(e.target) && !this.roomSuggestions.contains(e.target)) {
                this.roomSuggestions.classList.add('d-none');
                this.selectedRoomIndex = -1;
            }
        });
    }

    joinRoom(roomName) {
        if (roomName === this.currentRoom) return;

        this.ws.emit('join_room', {
            room_name: roomName
        });
        this.currentRoom = roomName;
        this.currentRoomElement.textContent = roomName;
        this.messageInput.disabled = false;
        this.sendMessageBtn.disabled = false;

        // Update room list active state
        document.querySelectorAll('.room-item').forEach(item => {
            item.classList.toggle('active', item.textContent === roomName);
        });

        // Focus message input after joining room
        this.messageInput.focus();
    }

    updateConnectionStatus(connected) {
        this.statusBadge.className = `badge rounded-pill ${connected ? 'connected' : 'disconnected'}`;
        this.connectionStatus.textContent = connected ? 'Connected' : 'Disconnected';
        this.messageInput.disabled = !connected || !this.currentRoom;
        this.sendMessageBtn.disabled = !connected || !this.currentRoom;
    }

    clearMessageContainer() {
        this.messageContainer.innerHTML = '';
    }

    updateRoomList(rooms) {
        this.roomList.innerHTML = '';
        rooms.forEach(room => {
            const roomElement = document.createElement('div');
            roomElement.className = `room-item ${room === this.currentRoom ? 'active' : ''}`;
            roomElement.textContent = room;
            roomElement.addEventListener('click', () => this.joinRoom(room));
            this.roomList.appendChild(roomElement);
        });
    }

    escapeHtml(unsafe) {
        if (unsafe == null) return '';
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize the chat client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Load Socket.IO client library
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js';
    script.onload = () => {
        new ChatClient();
    };
    document.head.appendChild(script);
});