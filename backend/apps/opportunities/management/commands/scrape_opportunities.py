"""
OpportuCI - Scrape Opportunities Command
=========================================
Commande pour exécuter le scraping des vraies opportunités.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.opportunities.models import OpportunitySource
from apps.opportunities.services.aggregation_service import OpportunityAggregationService


class Command(BaseCommand):
    help = 'Scrape les opportunités depuis les sources actives (GreatYop, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Nom de la source spécifique à scraper',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Scraper toutes les sources actives',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Nettoyer les opportunités expirées',
        )

    def handle(self, *args, **options):
        service = OpportunityAggregationService()

        if options['cleanup']:
            self.stdout.write('Nettoyage des opportunités expirées...')
            count = service.cleanup_expired()
            self.stdout.write(
                self.style.SUCCESS(f'✓ {count} opportunités marquées expirées')
            )
            return

        if options['source']:
            # Scraper une source spécifique
            source_name = options['source']
            try:
                source = OpportunitySource.objects.get(
                    name__icontains=source_name,
                    is_active=True
                )
                self.stdout.write(f'Scraping: {source.name}...')
                stats = service.run_scraper_for_source(source)
                self._print_stats(stats)
            except OpportunitySource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Source "{source_name}" non trouvée')
                )
                self._list_sources()
                return
        else:
            # Scraper toutes les sources actives
            self.stdout.write('Scraping de toutes les sources actives...')
            self._list_sources()

            stats = service.run_all_scrapers()
            self._print_stats(stats)

    def _list_sources(self):
        """Liste les sources disponibles."""
        sources = OpportunitySource.objects.filter(
            is_active=True,
            source_type__in=['website', 'api']
        )

        if sources.exists():
            self.stdout.write('\nSources actives:')
            for source in sources:
                scraper_id = source.scrape_config.get('scraper_id', 'N/A')
                last_scraped = source.last_scraped_at or 'Jamais'
                self.stdout.write(
                    f'  • {source.name} [{scraper_id}] - Dernier: {last_scraped}'
                )
        else:
            self.stdout.write(
                self.style.WARNING('Aucune source active configurée')
            )

    def _print_stats(self, stats):
        """Affiche les statistiques."""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Résultats du scraping:'))
        self.stdout.write(f"  Sources traitées: {stats.get('sources_processed', 0)}")
        self.stdout.write(f"  Opportunités scrapées: {stats.get('opportunities_scraped', 0)}")
        self.stdout.write(f"  Nouvelles créées: {stats.get('opportunities_created', 0)}")
        self.stdout.write(f"  Mises à jour: {stats.get('opportunities_updated', 0)}")
        self.stdout.write(f"  Doublons ignorés: {stats.get('duplicates_skipped', 0)}")
        self.stdout.write(f"  Erreurs: {stats.get('errors', 0)}")
        self.stdout.write('=' * 50)
