import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, OnlineUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        self.username = self.user.username if self.user.is_authenticated else 'Anonymous'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.set_online(True)
        await self.accept()

        # Notify room someone joined
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'presence_update',
            'username': self.username,
            'action': 'joined',
            'online_users': await self.get_online_users(),
        })

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'presence_update',
            'username': self.username,
            'action': 'left',
            'online_users': await self.get_online_users(),
        })
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action', 'message')

        if action == 'typing':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_update',
                'username': self.username,
                'is_typing': data.get('is_typing', False),
            })
            return

        if action == 'delete':
            msg_id = data.get('msg_id')
            success = await self.delete_message(msg_id)
            if success:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'message_deleted',
                    'msg_id': msg_id,
                })
            return

        if action == 'edit':
            msg_id = data.get('msg_id')
            new_content = data.get('message', '')
            success = await self.edit_message(msg_id, new_content)
            if success:
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'message_edited',
                    'msg_id': msg_id,
                    'message': new_content,
                })
            return

        if action == 'react':
            msg_id = data.get('msg_id')
            emoji = data.get('emoji', '👍')
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'message_reaction',
                'msg_id': msg_id,
                'emoji': emoji,
                'username': self.username,
            })
            return

        # Regular message or media
        msg_type = data.get('msg_type', 'text')
        message = data.get('message', '')
        file_url = data.get('file_url', '')

        saved_id = await self.save_message(self.username, self.room_name, message, msg_type, file_url)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'msg_id': saved_id,
            'msg_type': msg_type,
            'message': message,
            'file_url': file_url,
            'username': self.username,
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'msg_id': event['msg_id'],
            'msg_type': event['msg_type'],
            'message': event['message'],
            'file_url': event['file_url'],
            'username': event['username'],
        }))

    async def typing_update(self, event):
        if event['username'] != self.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'username': event['username'],
            'action': event['action'],
            'online_users': event['online_users'],
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'deleted',
            'msg_id': event['msg_id'],
        }))

    async def message_edited(self, event):
        await self.send(text_data=json.dumps({
            'type': 'edited',
            'msg_id': event['msg_id'],
            'message': event['message'],
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'msg_id': event['msg_id'],
            'emoji': event['emoji'],
            'username': event['username'],
        }))

    @database_sync_to_async
    def save_message(self, username, room, message, msg_type='text', file_url=''):
        msg = Message.objects.create(
            username=username, room=room,
            content=message, msg_type=msg_type,
        )
        return msg.id

    @database_sync_to_async
    def delete_message(self, msg_id):
        try:
            msg = Message.objects.get(id=msg_id, username=self.username)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def edit_message(self, msg_id, new_content):
        try:
            msg = Message.objects.get(id=msg_id, username=self.username)
            msg.content = new_content
            msg.is_edited = True
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def set_online(self, is_online):
        if is_online:
            OnlineUser.objects.get_or_create(username=self.username, room=self.room_name)
        else:
            OnlineUser.objects.filter(username=self.username, room=self.room_name).delete()

    @database_sync_to_async
    def get_online_users(self):
        return list(OnlineUser.objects.filter(room=self.room_name).values_list('username', flat=True))