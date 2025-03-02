import uuid
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from chat.models import Conversation, Message
from chat.serializers import WebhookEventSerializer, ConversationSerializer, MessageSerializer
from rest_framework import status
from django.utils import timezone
import json


@pytest.mark.django_db
class TestChatAPI:
    def setup_method(self):
        """Configura o ambiente de teste criando uma conversa aberta."""
        self.client = APIClient()
        self.conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

    def test_criar_conversa(self):
        """Verifica se uma nova conversa pode ser criada com sucesso."""
        url = reverse("chat:webhook")
        response = self.client.post(
            url, {"type": "NEW_CONVERSATION", "data": {"id": str(uuid.uuid4())}}, format="json"
        )

        assert response.status_code == 200
        assert Conversation.objects.count() == 2

    def test_enviar_mensagem(self):
        """Verifica se uma mensagem pode ser enviada com sucesso."""
        url = reverse("chat:webhook")
        response = self.client.post(
            url,
            {
                "type": "NEW_MESSAGE",
                "timestamp": "2025-02-21T10:20:44.349308",
                "data": {
                    "id": str(uuid.uuid4()),
                    "direction": "SENT",
                    "content": "Oi",
                    "conversation_id": str(self.conversation.id),
                },
            },
            format="json",
        )

        assert response.status_code == 200
        assert Message.objects.count() == 1

    def test_nao_permitir_mensagem_em_conversa_fechada(self):
        """Verifica se não é possível enviar mensagem para uma conversa fechada."""
        self.conversation.status = "CLOSED"
        self.conversation.save()

        url = reverse("chat:webhook")
        response = self.client.post(
            url,
            {
                "type": "NEW_MESSAGE",
                "timestamp": "2025-02-21T10:20:44.349308",
                "data": {
                    "id": str(uuid.uuid4()),
                    "direction": "SENT",
                    "content": "Oi",
                    "conversation_id": str(self.conversation.id),
                },
            },
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.data

    @pytest.mark.parametrize(
        "event_type, data, expected_valid",
        [
            ("NEW_CONVERSATION", {"id": str(uuid.uuid4())}, True),
            ("NEW_MESSAGE", 
                {
                    "id": str(uuid.uuid4()), 
                    "direction": "SENT", 
                    "content": "Oi", 
                    "conversation_id": str(uuid.uuid4()) 
                }, 
                True
            ),
            ("CLOSE_CONVERSATION", {"id": str(uuid.uuid4())}, True),
            ("UNKNOWN_EVENT", {"id": str(uuid.uuid4())}, False), 
        ],
    )
    def test_webhook_event_serializer(self, event_type, data, expected_valid):
        """Verifica se o WebhookEventSerializer valida corretamente os eventos."""
        serializer = WebhookEventSerializer(data={"type": event_type, "data": data or {}})
        assert serializer.is_valid() == expected_valid

    def test_message_serializer_valid_data(self):
        """Verifica se o MessageSerializer valida corretamente os dados."""
        conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

        data = {
            "id": str(uuid.uuid4()),
            "conversation_id": str(conversation.id),
            "direction": "SENT",
            "content": "Olá, tudo bem?",
            "timestamp": "2024-03-01T12:30:00Z"
        }

        serializer = MessageSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_message_serializer_invalid_direction(self):
        """Verifica se o MessageSerializer rejeita direções inválidas."""
        conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

        data = {
            "id": str(uuid.uuid4()),
            "direction": "INVALID_DIRECTION",
            "content": "Olá!",
            "conversation_id": str(conversation.id),
        }

        serializer = MessageSerializer(data=data)
        assert not serializer.is_valid()
        assert "direction" in serializer.errors

    def test_message_serializer_missing_fields(self):
        """Verifica se o MessageSerializer retorna erro ao faltar campos obrigatórios."""
        data = {"id": str(uuid.uuid4()), "content": "Oi"}
        serializer = MessageSerializer(data=data)
        assert not serializer.is_valid()
        assert "direction" in serializer.errors

    def test_is_valid_uuid(self):
        """Verifica se o método is_valid_uuid reconhece corretamente UUIDs válidos e inválidos."""
        serializer = WebhookEventSerializer()

        assert serializer.is_valid_uuid(str(uuid.uuid4())) is True
        assert serializer.is_valid_uuid("UUID_INVALIDO") is False


    def test_close_conversation(self):
        """Verifica se o método close() altera corretamente o status e define closed_at."""
        conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

        conversation.close()

        assert conversation.status == "CLOSED"
        assert conversation.closed_at is not None

    def test_message_creation(self):
        """Verifica se uma mensagem é criada corretamente e associada à conversa."""
        conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

        message = Message.objects.create(
            id=uuid.uuid4(),
            conversation=conversation,
            direction="SENT",
            content="Olá, tudo bem?",
            timestamp=timezone.now(),
        )

        assert message in conversation.messages.all()

    def test_message_ordering(self):
        """Verifica se as mensagens são ordenadas corretamente pelo timestamp."""
        conversation = Conversation.objects.create(id=uuid.uuid4(), status="OPEN")

        msg1 = Message.objects.create(
            id=uuid.uuid4(), conversation=conversation, direction="SENT", content="Primeira", timestamp=timezone.now()
        )
        msg2 = Message.objects.create(
            id=uuid.uuid4(), conversation=conversation, direction="SENT", content="Segunda", timestamp=timezone.now()
        )

        messages = list(conversation.messages.all())

        assert messages == sorted(messages, key=lambda msg: msg.timestamp)


    def test_webhook_empty_body(self):
        """Verifica se o webhook retorna erro quando a requisição está vazia."""
        response = self.client.post(reverse("chat:webhook"), {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Request body is empty"    


    def test_webhook_new_message_invalid_uuid(self):
        """Teste para webhook com UUID inválido"""

        url = reverse("chat:webhook")  
        data = {
            "data": json.dumps({"message": "Hello"})
        }

        response = self.client.post(url, data, content_type="application/json")

        
        assert response.status_code == 400

    def test_webhook_new_message_duplicate(self):
        """Teste para webhook enviando mensagem duplicada"""

        url = reverse("chat:webhook")
        message_id = str(uuid.uuid4())
        data = {
            "message_id": message_id,
            "content": "Mensagem de teste"
        }
        self.client.post(url, json.dumps(data), content_type="application/json")
        response = self.client.post(url, json.dumps(data), content_type="application/json")
        
        assert response.status_code ==400 

    def test_webhook_close_conversation_not_found(self):
        """Testa fechamento de conversa inexistente."""
        response = self.client.post(
            reverse("chat:webhook"),
            data=json.dumps({"type": "CLOSE_CONVERSATION", "data": {"id": "invalid-uuid"}}),
            content_type="application/json",  
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "Invalid conversation ID"

    def test_get_conversation_invalid_uuid(self):
        """Verifica erro ao buscar uma conversa com UUID inválido."""
        invalid_uuid = str(uuid.uuid4())
        response = self.client.get(reverse("chat:get_conversation", args=[invalid_uuid]))
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"] == "Conversation not found"

    def test_get_conversation_not_found(self):
        """Verifica erro ao buscar uma conversa inexistente."""
        response = self.client.get(reverse("chat:get_conversation", args=[str(uuid.uuid4())]))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["error"] == "Conversation not found"

    def test_get_conversation_success(self):
        """Verifica se retorna os dados corretamente para uma conversa existente."""
        response = self.client.get(reverse("chat:get_conversation", args=[str(self.conversation.id)]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(self.conversation.id)
