# backend/chat/services.py
import google.generativeai as genai
from django.conf import settings
from .models import ChatConversation, ChatMessage
import time
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class GeminiChatService:
    """Service de chat intelligent avec Gemini pour OpportuCI"""

    # Liste des modèles par ordre de priorité
    PREFERRED_MODELS = [
        "models/gemini-2.5-pro",
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.5-pro",
    ]

    def __init__(self):
        """Initialisation du service Gemini"""
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("⚠️ GEMINI_API_KEY non défini dans settings.py")

        genai.configure(api_key=api_key)
        self.model_name = self._select_best_model()
        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"✅ Gemini AI service initialisé avec le modèle: {self.model_name}")

        # Contexte système par défaut
        self.system_context = """
        Tu es l'assistant IA d'OpportuCI, une plateforme qui aide les jeunes Ivoiriens 
        à trouver des opportunités professionnelles et à développer leurs carrières.

        Ton rôle:
        - Conseiller les utilisateurs sur leur carrière
        - Aider à trouver des opportunités adaptées
        - Recommander des formations et compétences
        - Donner des conseils pratiques pour le marché du travail ivoirien/africain

        Contexte local important:
        - Focus sur la Côte d'Ivoire et l'Afrique de l'Ouest
        - Secteurs en croissance: tech, agriculture moderne, finance, énergies renouvelables
        - Défis: chômage des jeunes, gap de compétences, accès limité aux opportunités
        - Opportunités: transformation numérique, entrepreneuriat, marchés émergents

        Style de communication:
        - Amical et encourageant
        - Pratique et orienté action
        - Adapté au contexte africain
        - En français avec expressions locales appropriées
        """

    # -------------------------------
    # 🔹 Sélection automatique du modèle
    # -------------------------------
    def _select_best_model(self) -> str:
        try:
            available_models = [m.name for m in genai.list_models()]

            for model in self.PREFERRED_MODELS:
                if model in available_models:
                    return model

            raise ValueError("⚠️ Aucun modèle compatible trouvé dans l'API Gemini")
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du modèle: {e}")
            # Fallback forcé pour éviter un crash
            return "models/gemini-1.5-pro-latest"

    # -------------------------------
    # 🔹 Gestion des conversations
    # -------------------------------
    def get_or_create_conversation(self, user, context_type="general"):
        """Récupère ou crée une conversation active"""
        conversation = ChatConversation.objects.filter(
            user=user, is_active=True, context_type=context_type
        ).first()

        if not conversation:
            conversation = ChatConversation.objects.create(
                user=user, context_type=context_type
            )

        return conversation

    # -------------------------------
    # 🔹 Envoi et réponse de l'IA
    # -------------------------------
    def send_message(
        self, user, message_content: str, context_type="general", conversation_id=None
    ) -> Dict:
        start_time = time.time()

        try:
            # Récupérer la conversation
            if conversation_id:
                conversation = ChatConversation.objects.filter(
                    id=conversation_id, user=user
                ).first()
                if not conversation:
                    conversation = self.get_or_create_conversation(user, context_type)
            else:
                conversation = self.get_or_create_conversation(user, context_type)

            # Sauvegarde du message utilisateur
            ChatMessage.objects.create(
                conversation=conversation, role="user", content=message_content
            )

            # Contexte de conversation
            chat_history = self._build_chat_history(conversation)
            user_context = self._get_user_context(user)

            # Construction du prompt
            full_prompt = f"""
            {self.system_context}

            CONTEXTE UTILISATEUR:
            {user_context}

            HISTORIQUE DE CONVERSATION:
            {chat_history}

            NOUVEAU MESSAGE UTILISATEUR: {message_content}
            """

            # Appel API Gemini
            try:
                response = self.model.generate_content(full_prompt)
                ai_response = response.text
            except Exception as api_error:
                logger.error(f"Gemini API error: {api_error}")
                ai_response = (
                    "⚠️ Je rencontre un problème technique. Pouvez-vous réessayer ?"
                )

            response_time = int((time.time() - start_time) * 1000)

            # Sauvegarde du message IA
            ai_message = ChatMessage.objects.create(
                conversation=conversation,
                role="assistant",
                content=ai_response,
                response_time_ms=response_time,
                model_version=self.model_name,
            )

            # Génération auto du titre
            if conversation.messages.count() <= 2 and not conversation.title:
                conversation.title = self._generate_conversation_title(
                    message_content, ai_response
                )
                conversation.save()

            return {
                "success": True,
                "conversation_id": str(conversation.id),
                "message_id": str(ai_message.id),
                "response": ai_response,
                "response_time_ms": response_time,
                "conversation_title": conversation.title,
            }

        except Exception as e:
            logger.error(f"Erreur send_message: {e}")
            return {"success": False, "error": str(e)}

    # -------------------------------
    # 🔹 Helpers internes
    # -------------------------------
    def _build_chat_history(
        self, conversation: ChatConversation, limit=10
    ) -> str:
        """Construit l'historique pour le prompt"""
        try:
            recent_messages = conversation.messages.order_by("-timestamp")[:limit]
            recent_messages = list(reversed(recent_messages))

            return "\n".join(
                [
                    f"{'Utilisateur' if msg.role=='user' else 'Assistant'}: {msg.content}"
                    for msg in recent_messages
                ]
            ) or "Pas d'historique précédent."
        except Exception as e:
            logger.error(f"Erreur build_chat_history: {e}")
            return "Erreur lors du chargement de l'historique."

    def _get_user_context(self, user) -> str:
        """Construit un résumé du profil utilisateur"""
        try:
            parts = [f"Nom: {user.get_full_name() or user.username}"]

            if getattr(user, "education_level", None):
                parts.append(f"Niveau d'éducation: {user.education_level}")

            if getattr(user, "institution", None):
                parts.append(f"Institution: {user.institution}")

            if getattr(user, "city", None) or getattr(user, "country", None):
                location = ", ".join(
                    filter(None, [getattr(user, "city", None), getattr(user, "country", None)])
                )
                parts.append(f"Localisation: {location}")

            return "\n".join(parts) or "Profil utilisateur basique."
        except Exception as e:
            logger.error(f"Erreur get_user_context: {e}")
            return "Utilisateur OpportuCI"

    def _generate_conversation_title(self, user_message: str, ai_response: str) -> str:
        """Titre auto basé sur les premiers mots"""
        try:
            title = " ".join(user_message.split()[:3])
            return title[:50] or f"Discussion {time.strftime('%d/%m')}"
        except Exception:
            return f"Discussion {time.strftime('%d/%m')}"

    # -------------------------------
    # 🔹 Historique & conversations
    # -------------------------------
    def get_conversation_history(
        self, user, conversation_id=None, limit=50
    ) -> List[Dict]:
        try:
            conversation = (
                ChatConversation.objects.filter(id=conversation_id, user=user).first()
                if conversation_id
                else self.get_or_create_conversation(user)
            )
            if not conversation:
                return []

            messages = conversation.messages.order_by("timestamp")[:limit]

            return [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "response_time_ms": msg.response_time_ms,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Erreur get_conversation_history: {e}")
            return []

    def get_user_conversations(self, user, limit=20) -> List[Dict]:
        try:
            conversations = ChatConversation.objects.filter(
                user=user, is_active=True
            ).order_by("-updated_at")[:limit]

            return [
                {
                    "id": str(conv.id),
                    "title": conv.title or "Nouvelle conversation",
                    "context_type": conv.context_type,
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": conv.messages.count(),
                    "last_message": (
                        conv.messages.last().content[:100] + "..."
                        if conv.messages.exists()
                        else ""
                    ),
                }
                for conv in conversations
            ]
        except Exception as e:
            logger.error(f"Erreur get_user_conversations: {e}")
            return []
