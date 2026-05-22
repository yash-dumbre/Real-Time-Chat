from django.db import models

class Message(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'), ('image', 'Image'), ('video', 'Video'),
    )
    username   = models.CharField(max_length=100)
    room       = models.CharField(max_length=100)
    content    = models.TextField(blank=True)
    file       = models.FileField(upload_to='chat_uploads/', blank=True, null=True)
    msg_type   = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    is_edited  = models.BooleanField(default=False)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.username} in {self.room}: {self.content[:30]}'

class OnlineUser(models.Model):
    username  = models.CharField(max_length=100)
    room      = models.CharField(max_length=100)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('username', 'room')

class PushSubscription(models.Model):
    user      = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    endpoint  = models.TextField(unique=True)
    p256dh    = models.TextField()
    auth      = models.TextField()
    created   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} subscription'