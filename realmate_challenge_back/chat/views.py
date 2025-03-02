import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.utils import IntegrityError
from django.utils.dateparse import parse_datetime
from uuid import UUID
from .models import Conversation, Message
from .serializers import ConversationSerializer

# Configuração de logs
logger = logging.getLogger(__name__)

def is_valid_uuid(value):
    """Verifica se um valor é um UUID válido"""
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False

@api_view(['POST'])
def webhook_view(request):
    try:
        event = request.data

        if not event:
            return Response({'error': 'Request body is empty'}, status=status.HTTP_400_BAD_REQUEST)

        event_type = event.get('type')
        event_data = event.get('data')

        if not event_type or not event_data:
            return Response({'error': 'Missing type or data field'}, status=status.HTTP_400_BAD_REQUEST)

        # 🚀 Criar uma nova conversa
        if event_type == 'NEW_CONVERSATION':
            conversation_id = event_data.get('id')

            if not is_valid_uuid(conversation_id):
                return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

            Conversation.objects.get_or_create(id=conversation_id)

        # 🚀 Criar uma nova mensagem
        elif event_type == 'NEW_MESSAGE':
            required_fields = ['id', 'conversation_id', 'direction', 'content']
            if not all(field in event_data for field in required_fields):
                return Response({'error': 'Missing fields in NEW_MESSAGE event'}, status=status.HTTP_400_BAD_REQUEST)

            message_id = event_data['id']
            conversation_id = event_data['conversation_id']

            if not is_valid_uuid(message_id) or not is_valid_uuid(conversation_id):
                return Response({'error': 'Invalid message or conversation ID'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                conversation = Conversation.objects.get(id=conversation_id, status='OPEN')

                timestamp = parse_datetime(event.get('timestamp'))
                if not timestamp:
                    return Response({'error': 'Invalid timestamp format'}, status=status.HTTP_400_BAD_REQUEST)

                # 🚀 Verifica se a mensagem já existe
                if Message.objects.filter(id=message_id).exists():
                    return Response({'error': 'Message ID already exists'}, status=status.HTTP_409_CONFLICT)

                Message.objects.create(
                    id=message_id,
                    conversation=conversation,
                    direction=event_data['direction'],
                    content=event_data['content'],
                    timestamp=timestamp
                )
            except Conversation.DoesNotExist:
                return Response({'error': 'Conversation not found or closed'}, status=status.HTTP_400_BAD_REQUEST)
            except IntegrityError:
                return Response({'error': 'Message ID already exists'}, status=status.HTTP_409_CONFLICT)

        # 🚀 Fechar uma conversa
        elif event_type == 'CLOSE_CONVERSATION':
            conversation_id = event_data.get('id')

            if not is_valid_uuid(conversation_id):
                return Response({'error': 'Invalid conversation ID'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                conversation = Conversation.objects.get(id=conversation_id)
                conversation.close()
            except Conversation.DoesNotExist:
                return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({'error': 'Invalid event type'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Event processed'}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def list_conversations(request):
    conversations = Conversation.objects.all()
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_conversation(request, id):
    try:
        if not is_valid_uuid(id):
            return Response({'error': 'Invalid conversation ID'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = Conversation.objects.get(id=id)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
