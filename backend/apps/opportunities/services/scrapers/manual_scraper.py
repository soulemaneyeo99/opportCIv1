"""
OpportuCI - Manual Data Scraper
===============================
"Scraper" pour les données saisies manuellement ou importées.
Utile pour le seeding et les partenaires.
"""
from typing import List
from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry


@ScraperRegistry.register
class ManualScraper(BaseScraper):
    """
    Pseudo-scraper pour les données manuelles.

    Utilisé pour:
    - Seed de données initiales
    - Import de fichiers CSV/JSON
    - Données de partenaires
    """

    SCRAPER_ID = 'manual'
    SCRAPER_NAME = 'Saisie Manuelle'
    SOURCE_URL = ''

    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Retourne les données fournies dans la config.
        """
        data = self.config.get('opportunities', [])

        opportunities = []
        for item in data:
            try:
                opp = ScrapedOpportunity(
                    title=item.get('title', 'Sans titre'),
                    description=item.get('description', ''),
                    organization=item.get('organization', 'OpportuCI'),
                    opportunity_type=item.get('opportunity_type', 'other'),
                    source_url=item.get('source_url', ''),
                    application_link=item.get('application_link', ''),
                    location=item.get('location', 'Côte d\'Ivoire'),
                    is_remote=item.get('is_remote', False),
                    deadline=self.parse_date(item.get('deadline', '')),
                    publication_date=self.parse_date(item.get('publication_date', '')),
                    education_level=item.get('education_level', 'any'),
                    skills_required=item.get('skills_required', []),
                    experience_years=item.get('experience_years', 0),
                    compensation=item.get('compensation', ''),
                    external_id=item.get('external_id', ''),
                )
                opportunities.append(opp)
            except Exception as e:
                self.log_error(f"Erreur parsing data: {e}")

        self.stats['opportunities_found'] = len(opportunities)
        return opportunities
