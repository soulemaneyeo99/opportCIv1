# backend/chat/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .services import GeminiChatService
from .models import ChatConversation, ChatMessage
import logging

logger = logging.getLogger(__name__)

class ChatSendMessageView(APIView):
    """Envoie un message et reçoit la réponse de l'IA"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            message_content = request.data.get('message', '').strip()
            conversation_id = request.data.get('conversation_id')
            context_type = request.data.get('context_type', 'general')
            
            if not message_content:
                return Response(
                    {'error': 'Le message ne peut pas être vide'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Utiliser le service Gemini
            chat_service = GeminiChatService()
            result = chat_service.send_message(
                user=request.user,
                message_content=message_content,
                context_type=context_type,
                conversation_id=conversation_id
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'conversation_id': result['conversation_id'],
                    'response': result['response'],
                    'response_time_ms': result['response_time_ms'],
                    'conversation_title': result.get('conversation_title')
                })
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Erreur chat send message: {str(e)}")
            return Response(
                {'error': 'Erreur lors de l\'envoi du message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatHistoryView(APIView):
    """Récupère l'historique d'une conversation"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, conversation_id=None):
        try:
            chat_service = GeminiChatService()
            history = chat_service.get_conversation_history(
                user=request.user,
                conversation_id=conversation_id,
                limit=int(request.query_params.get('limit', 50))
            )
            
            return Response({
                'messages': history,
                'total': len(history)
            })
            
        except Exception as e:
            logger.error(f"Erreur chat history: {str(e)}")
            return Response(
                {'error': 'Erreur lors du chargement de l\'historique'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatConversationsListView(APIView):
    """Liste les conversations de l'utilisateur"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            chat_service = GeminiChatService()
            conversations = chat_service.get_user_conversations(
                user=request.user,
                limit=int(request.query_params.get('limit', 20))
            )
            
            return Response({
                'conversations': conversations,
                'total': len(conversations)
            })
            
        except Exception as e:
            logger.error(f"Erreur conversations list: {str(e)}")
            return Response(
                {'error': 'Erreur lors du chargement des conversations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatNewConversationView(APIView):
    """Crée une nouvelle conversation"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            context_type = request.data.get('context_type', 'general')
            
            chat_service = GeminiChatService()
            conversation = chat_service.get_or_create_conversation(
                user=request.user,
                context_type=context_type
            )
            
            return Response({
                'conversation_id': str(conversation.id),
                'context_type': conversation.context_type,
                'title': conversation.title or 'Nouvelle conversation'
            })
            
        except Exception as e:
            logger.error(f"Erreur new conversation: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la création de la conversation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )