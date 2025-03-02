from django.db import models
from django.utils import timezone
import uuid


class Conversation(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


    def close(self):
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.save()

        
class Message(models.Model):
    DIRECTION_CHOICES = [
        ('SENT', 'Sent'),
        ('RECEIVED', 'Received'),
    ]


    id = models.UUIDField(primary_key=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['timestamp']