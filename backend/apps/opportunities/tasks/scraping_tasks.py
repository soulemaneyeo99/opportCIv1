"""
OpportuCI - Scraping Tasks
==========================
Tâches Celery pour le scraping automatisé.
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    name='opportunities.scrape_all_sources'
)
def scrape_all_sources(self):
    """
    Tâche planifiée: scrape toutes les sources actives.

    Planification recommandée: toutes les 6 heures
    """
    from apps.opportunities.services.aggregation_service import (
        OpportunityAggregationService
    )

    logger.info("Démarrage scraping automatique de toutes les sources")

    service = OpportunityAggregationService()
    stats = service.run_all_scrapers()

    logger.info(f"Scraping terminé: {stats}")

    return {
        'status': 'completed',
        'stats': stats,
        'timestamp': timezone.now().isoformat(),
    }


@shared_task(
    bind=True,
    name='opportunities.scrape_source'
)
def scrape_source(self, source_id: int):
    """
    Scrape une source spécifique.

    Args:
        source_id: ID de l'OpportunitySource
    """
    from apps.opportunities.models import OpportunitySource
    from apps.opportunities.services.aggregation_service import (
        OpportunityAggregationService
    )

    try:
        source = OpportunitySource.objects.get(id=source_id)
    except OpportunitySource.DoesNotExist:
        logger.error(f"Source {source_id} non trouvée")
        return {'error': f'Source {source_id} not found'}

    logger.info(f"Scraping source: {source.name}")

    service = OpportunityAggregationService()
    stats = service.run_scraper_for_source(source)

    return {
        'source': source.name,
        'stats': stats,
        'timestamp': timezone.now().isoformat(),
    }


@shared_task(name='opportunities.cleanup_expired')
def cleanup_expired_opportunities():
    """
    Tâche planifiée: marque les opportunités expirées.

    Planification recommandée: quotidienne (minuit)
    """
    from apps.opportunities.services.aggregation_service import (
        OpportunityAggregationService
    )

    service = OpportunityAggregationService()
    count = service.cleanup_expired(days_grace=7)

    logger.info(f"Nettoyage: {count} opportunités marquées expirées")

    return {
        'expired_count': count,
        'timestamp': timezone.now().isoformat(),
    }


@shared_task(name='opportunities.import_manual_data')
def import_manual_data(data: list, source_name: str = 'Import Manuel'):
    """
    Importe des données manuelles en background.

    Args:
        data: Liste de dictionnaires d'opportunités
        source_name: Nom de la source
    """
    from apps.opportunities.models import OpportunitySource
    from apps.opportunities.services.aggregation_service import (
        OpportunityAggregationService
    )

    source, _ = OpportunitySource.objects.get_or_create(
        name=source_name,
        defaults={'source_type': 'manual'}
    )

    service = OpportunityAggregationService()
    result = service.import_opportunities(data, source)

    logger.info(f"Import terminé: {result}")

    return result


# Configuration Celery Beat (à ajouter dans settings)
CELERY_BEAT_SCHEDULE_CONFIG = {
    'scrape-all-sources-every-6h': {
        'task': 'opportunities.scrape_all_sources',
        'schedule': 6 * 60 * 60,  # 6 heures en secondes
    },
    'cleanup-expired-daily': {
        'task': 'opportunities.cleanup_expired',
        'schedule': 24 * 60 * 60,  # 24 heures
    },
}
