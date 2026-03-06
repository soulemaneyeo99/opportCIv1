"""
OpportuCI - Aggregation Service
===============================
Coordonne le scraping et l'import des opportunités.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from ..models import Opportunity, OpportunitySource, OpportunityCategory
from .scrapers import ScraperRegistry, ScrapedOpportunity

logger = logging.getLogger(__name__)


class OpportunityAggregationService:
    """
    Service central pour l'agrégation des opportunités.

    Responsabilités:
    - Orchestrer les scrapers
    - Dédoublonner les opportunités
    - Sauvegarder en base de données
    - Mettre à jour les statistiques des sources
    """

    def __init__(self):
        self.stats = {
            'sources_processed': 0,
            'opportunities_scraped': 0,
            'opportunities_created': 0,
            'opportunities_updated': 0,
            'duplicates_skipped': 0,
            'errors': 0,
        }

    def run_all_scrapers(self) -> Dict[str, Any]:
        """
        Exécute tous les scrapers actifs.

        Returns:
            Statistiques d'exécution
        """
        active_sources = OpportunitySource.objects.filter(
            is_active=True,
            source_type__in=['website', 'api']
        )

        for source in active_sources:
            try:
                self.run_scraper_for_source(source)
            except Exception as e:
                logger.error(f"Erreur scraping {source.name}: {e}")
                self.stats['errors'] += 1

        return self.get_stats()

    def run_scraper_for_source(
        self,
        source: OpportunitySource
    ) -> Dict[str, Any]:
        """
        Exécute le scraper pour une source spécifique.
        """
        scraper_id = source.scrape_config.get('scraper_id')
        if not scraper_id:
            logger.warning(f"Source {source.name} sans scraper_id configuré")
            return {}

        scraper = ScraperRegistry.create(
            scraper_id,
            config=source.scrape_config
        )

        if not scraper:
            logger.error(f"Scraper {scraper_id} non trouvé")
            return {}

        logger.info(f"Démarrage scraping: {source.name} ({scraper_id})")

        # Exécuter le scraping
        opportunities = scraper.scrape()

        # Sauvegarder les opportunités
        saved_count = self._save_opportunities(opportunities, source)

        # Mettre à jour la source
        source.last_scraped_at = timezone.now()
        source.save(update_fields=['last_scraped_at'])

        self.stats['sources_processed'] += 1
        self.stats['opportunities_scraped'] += len(opportunities)

        scraper_stats = scraper.get_stats()
        logger.info(
            f"Terminé {source.name}: {saved_count} sauvegardées, "
            f"{scraper_stats['errors']} erreurs"
        )

        return scraper_stats

    def import_opportunities(
        self,
        data: List[Dict],
        source: OpportunitySource = None
    ) -> Dict[str, Any]:
        """
        Importe des opportunités depuis des données brutes.

        Args:
            data: Liste de dictionnaires d'opportunités
            source: Source à associer (optionnel)
        """
        if source is None:
            source, _ = OpportunitySource.objects.get_or_create(
                name='Import Manuel',
                defaults={'source_type': 'manual'}
            )

        # Utiliser le ManualScraper pour normaliser
        scraper = ScraperRegistry.create('manual', config={'opportunities': data})
        if not scraper:
            return {'error': 'ManualScraper non disponible'}

        opportunities = scraper.scrape()
        saved_count = self._save_opportunities(opportunities, source)

        return {
            'imported': len(data),
            'saved': saved_count,
            'duplicates': len(data) - saved_count,
        }

    def _save_opportunities(
        self,
        opportunities: List[ScrapedOpportunity],
        source: OpportunitySource
    ) -> int:
        """
        Sauvegarde les opportunités en base avec dédoublonnage.
        """
        saved_count = 0

        for scraped_opp in opportunities:
            try:
                with transaction.atomic():
                    created = self._save_single_opportunity(scraped_opp, source)
                    if created:
                        saved_count += 1
                        self.stats['opportunities_created'] += 1
                    else:
                        self.stats['duplicates_skipped'] += 1
            except Exception as e:
                logger.error(f"Erreur sauvegarde: {e}")
                self.stats['errors'] += 1

        return saved_count

    def _save_single_opportunity(
        self,
        scraped: ScrapedOpportunity,
        source: OpportunitySource
    ) -> bool:
        """
        Sauvegarde une opportunité unique.

        Returns:
            True si créée, False si doublon/mise à jour
        """
        external_id = scraped.generate_external_id()

        # Vérifier si existe déjà
        existing = Opportunity.objects.filter(
            source=source,
            external_id=external_id
        ).first()

        if existing:
            # Mise à jour si plus récent
            if scraped.publication_date and existing.publication_date:
                if scraped.publication_date > existing.publication_date:
                    self._update_opportunity(existing, scraped)
                    self.stats['opportunities_updated'] += 1
            return False

        # Créer nouvelle opportunité
        data = scraped.to_dict()

        # Associer/créer la catégorie
        category = self._get_or_create_category(scraped.opportunity_type)

        opportunity = Opportunity.objects.create(
            source=source,
            category=category,
            status='published',
            **data
        )

        logger.debug(f"Créée: {opportunity.title[:50]}")
        return True

    def _update_opportunity(
        self,
        existing: Opportunity,
        scraped: ScrapedOpportunity
    ) -> None:
        """
        Met à jour une opportunité existante.
        """
        data = scraped.to_dict()

        # Champs à mettre à jour
        update_fields = [
            'description', 'deadline', 'application_link',
            'requirements', 'skills_required'
        ]

        for field in update_fields:
            if field in data and data[field]:
                setattr(existing, field, data[field])

        existing.save()

    def _get_or_create_category(
        self,
        opp_type: str
    ) -> Optional[OpportunityCategory]:
        """
        Récupère ou crée une catégorie.
        """
        type_to_category = {
            'scholarship': ('Bourses', 'bourses'),
            'internship': ('Stages', 'stages'),
            'job': ('Emplois', 'emplois'),
            'training': ('Formations', 'formations'),
            'competition': ('Concours', 'concours'),
            'event': ('Événements', 'evenements'),
        }

        if opp_type not in type_to_category:
            return None

        name, slug = type_to_category[opp_type]

        category, _ = OpportunityCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name}
        )

        return category

    def cleanup_expired(self, days_grace: int = 7) -> int:
        """
        Marque les opportunités expirées.

        Args:
            days_grace: Jours de grâce après deadline

        Returns:
            Nombre d'opportunités marquées expirées
        """
        cutoff = timezone.now() - timedelta(days=days_grace)

        expired = Opportunity.objects.filter(
            status='published',
            deadline__lt=cutoff
        ).update(status='expired')

        logger.info(f"Marquées expirées: {expired}")
        return expired

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'agrégation."""
        return {
            **self.stats,
            'timestamp': timezone.now().isoformat(),
        }
