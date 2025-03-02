from django.urls import path
from .views import webhook_view, get_conversation, list_conversations


app_name = "chat"

urlpatterns = [
    path('webhook/', webhook_view, name="webhook"),
    path('conversations/', list_conversations, name="list_conversation"),
    path('conversations/<uuid:id>/', get_conversation, name="get_conversation"),
    

]