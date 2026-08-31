# Real-Time Chat Application

A scalable real-time chat application built with Django Channels, Redis, and WebSockets for low-latency message delivery.

## Tech Stack

- **Backend Framework**: Django + Django Channels
- **Message Broker**: Redis
- **Real-time Protocol**: WebSockets
- **Database**: PostgreSQL (typical with Django)
- **Async Support**: ASGI server

## Features

- Real-time message delivery using WebSockets
- User presence tracking
- Multiple chat rooms/conversations
- Message persistence
- Connection management with Redis as message broker
- Async message handling with Django Channels

## Installation

### Prerequisites
- Python 3.8+
- Redis server
- PostgreSQL (optional, configurable)

### Setup

1. Clone the repository
```bash
git clone <repo-url>
cd real-time-chat-app
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure Redis connection in Django settings
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

5. Run migrations
```bash
python manage.py migrate
```

6. Start Redis server
```bash
redis-server
```

7. Run development server
```bash
daphne -b 0.0.0.0 -p 8000 project_name.asgi:application
```

## Architecture

### WebSocket Flow
- Client connects to WebSocket endpoint
- Django Channels consumer handles connection
- Messages routed through Redis channel layer
- Broadcast to room consumers
- Response sent back to clients

### Key Components
- **Consumers**: Handle WebSocket connections and message logic
- **Channel Layer**: Redis manages message routing across workers
- **Room Management**: Track active connections per chat room

## Usage

### Connect to Chat Room
```javascript
const socket = new WebSocket('ws://localhost:8000/ws/chat/room-name/');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Message:', data.message);
};

socket.send(JSON.stringify({
    'message': 'Hello, chat!'
}));
```

### Server-Side Consumer Example
```python
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.room_name,
            {'type': 'chat_message', 'message': data['message']}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))
```

## Performance Considerations

- Redis connection pooling for efficiency
- Message batching for high-volume scenarios
- Connection timeouts configured appropriately
- Scaling with multiple ASGI worker processes

## Environment Variables

Create `.env` file:
```
REDIS_URL=redis://localhost:6379
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```

## Future Enhancements

- End-to-end encryption for messages
- Message read receipts
- Typing indicators
- File/media sharing
- User authentication improvements
- Message search functionality

## License

MIT License
