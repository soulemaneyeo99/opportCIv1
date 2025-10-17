"""
OpportuCI - Interview WebSocket Consumer
=========================================
Consumer pour chat en temps réel pendant les entretiens
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from apps.simulations.models import InterviewSimulation
from apps.simulations.services.interview_simulator import InterviewSimulatorService

User = get_user_model()


class InterviewConsumer(AsyncWebsocketConsumer):
    """Consumer pour les simulations d'entretien en temps réel"""
    
    async def connect(self):
        """Connexion WebSocket"""
        self.simulation_id = self.scope['url_route']['kwargs']['simulation_id']
        self.room_name = f'interview_{self.simulation_id}'
        
        # Vérifier que l'utilisateur a accès à cette simulation
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Vérifier propriété de la simulation
        has_access = await self.check_simulation_access(user, self.simulation_id)
        if not has_access:
            await self.close(code=4003)
            return
        
        # Rejoindre le room
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer état initial
        simulation = await self.get_simulation(self.simulation_id)
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'simulation_id': str(self.simulation_id),
            'status': simulation.status
        }))
    
    async def disconnect(self, close_code):
        """Déconnexion"""
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Réception d'un message du client"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'send_message':
                await self.handle_send_message(data)
            elif action == 'start_interview':
                await self.handle_start_interview()
            elif action == 'end_interview':
                await self.handle_end_interview()
            else:
                await self.send_error('Action inconnue')
        
        except json.JSONDecodeError:
            await self.send_error('Format JSON invalide')
        except Exception as e:
            await self.send_error(f'Erreur: {str(e)}')
    
    async def handle_send_message(self, data):
        """Gère l'envoi d'un message utilisateur"""
        user_message = data.get('message', '').strip()
        
        if not user_message:
            await self.send_error('Message vide')
            return
        
        # Traiter le message
        simulator = InterviewSimulatorService()
        simulation = await self.get_simulation(self.simulation_id)
        
        # Traiter de manière synchrone (à optimiser avec async si possible)
        recruiter_response = await database_sync_to_async(
            simulator.process_user_response
        )(simulation, user_message)
        
        # Rafraîchir simulation
        await database_sync_to_async(simulation.refresh_from_db)()
        
        # Envoyer la réponse
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'interview_message',
                'message': {
                    'user_message': user_message,
                    'recruiter_response': recruiter_response,
                    'status': simulation.status,
                    'conversation_length': len(simulation.conversation),
                    'is_completed': simulation.status == 'completed'
                }
            }
        )
    
    async def handle_start_interview(self):
        """Démarre l'entretien"""
        simulator = InterviewSimulatorService()
        simulation = await self.get_simulation(self.simulation_id)
        
        if simulation.status != 'scheduled':
            await self.send_error('Simulation déjà démarrée ou terminée')
            return
        
        # Démarrer
        first_message = await database_sync_to_async(
            simulator.start_simulation
        )(simulation)
        
        # Rafraîchir
        await database_sync_to_async(simulation.refresh_from_db)()
        
        # Notifier
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'interview_started',
                'message': {
                    'first_message': first_message,
                    'status': simulation.status,
                    'started_at': simulation.started_at.isoformat() if simulation.started_at else None
                }
            }
        )
    
    async def handle_end_interview(self):
        """Termine l'entretien"""
        simulator = InterviewSimulatorService()
        simulation = await self.get_simulation(self.simulation_id)
        
        if simulation.status != 'in_progress':
            await self.send_error('Simulation pas en cours')
            return
        
        # Finaliser
        await database_sync_to_async(
            simulator.finalize_interview
        )(simulation)
        
        # Rafraîchir
        await database_sync_to_async(simulation.refresh_from_db)()
        
        # Notifier
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'interview_ended',
                'message': {
                    'status': simulation.status,
                    'overall_score': simulation.overall_score,
                    'completed_at': simulation.completed_at.isoformat() if simulation.completed_at else None
                }
            }
        )
    
    # Handlers pour les events du group
    
    async def interview_message(self, event):
        """Envoie un message au client"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))
    
    async def interview_started(self, event):
        """Notifie que l'entretien a démarré"""
        await self.send(text_data=json.dumps({
            'type': 'interview_started',
            'data': event['message']
        }))
    
    async def interview_ended(self, event):
        """Notifie que l'entretien est terminé"""
        await self.send(text_data=json.dumps({
            'type': 'interview_ended',
            'data': event['message']
        }))
    
    # Helpers
    
    async def send_error(self, error_message):
        """Envoie un message d'erreur"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))
    
    @database_sync_to_async
    def check_simulation_access(self, user, simulation_id):
        """Vérifie que l'utilisateur a accès à la simulation"""
        return InterviewSimulation.objects.filter(
            id=simulation_id,
            user=user
        ).exists()
    
    @database_sync_to_async
    def get_simulation(self, simulation_id):
        """Récupère la simulation"""
        return InterviewSimulation.objects.get(id=simulation_id)