from rest_framework import serializers
from .models import Message, Conversation
from uuid import UUID

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'conversation_id', 'direction', 'content', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'status', 'created_at', 'closed_at', 'messages']

class WebhookEventSerializer(serializers.Serializer):
    EVENT_TYPES = ['NEW_CONVERSATION', 'NEW_MESSAGE', 'CLOSE_CONVERSATION']
    
    type = serializers.ChoiceField(choices=EVENT_TYPES)
    data = serializers.JSONField()
    timestamp = serializers.DateTimeField(required=False)

    def validate_data(self, value):
        """Valida os dados conforme o tipo do evento, utilizando os Serializers adequados."""
        event_type = self.initial_data.get('type')

        if not event_type:
            raise serializers.ValidationError({'type': 'Event type is required'})

        if event_type == 'NEW_CONVERSATION':
            serializer = ConversationSerializer(data=value)
        elif event_type == 'NEW_MESSAGE':
            serializer = MessageSerializer(data=value)
        elif event_type == 'CLOSE_CONVERSATION':
            if 'id' not in value or not self.is_valid_uuid(value['id']):
                raise serializers.ValidationError({'id': 'Invalid conversation ID'})
            return value
        else:
            raise serializers.ValidationError({'type': 'Invalid event type'})  # Corrige o erro para eventos desconhecidos

        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)

        return serializer.validated_data

    def is_valid_uuid(self, value):
        """Verifica se um valor é um UUID válido."""
        try:
            UUID(str(value))
            return True
        except ValueError:
            return False
