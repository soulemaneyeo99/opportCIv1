"""
OpportuCI - Afri-Carrières Scraper
==================================
Scraper pour africarrieres.com (opportunités panafricaines)
"""
from typing import List, Optional
from datetime import datetime
from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry


@ScraperRegistry.register
class AfriCarrieresScraper(BaseScraper):
    """
    Scraper pour Afri-Carrières - Opportunités panafricaines.

    Source: https://africarrieres.com
    Types: Bourses, Emplois, Stages, Concours, Formations
    """

    SCRAPER_ID = 'africarrieres'
    SCRAPER_NAME = 'Afri-Carrières'
    SOURCE_URL = 'https://africarrieres.com'

    CATEGORIES = {
        'bourses': {
            'path': '/category/bourses-detudes/',
            'type': 'scholarship'
        },
        'emplois': {
            'path': '/category/offres-demploi/',
            'type': 'job'
        },
        'stages': {
            'path': '/category/stages/',
            'type': 'internship'
        },
        'concours': {
            'path': '/category/concours/',
            'type': 'competition'
        },
        'formations': {
            'path': '/category/formations-et-certifications/',
            'type': 'training'
        },
    }

    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Scrape les opportunités depuis Afri-Carrières.
        """
        opportunities = []

        categories = self.config.get(
            'categories',
            ['bourses', 'emplois', 'stages']
        )

        for cat_key in categories:
            if cat_key not in self.CATEGORIES:
                continue

            cat_info = self.CATEGORIES[cat_key]
            url = f"{self.SOURCE_URL}{cat_info['path']}"

            self.log_info(f"Scraping {cat_key}: {url}")

            opps = self._scrape_category(url, cat_info['type'])
            opportunities.extend(opps)

        self.stats['opportunities_found'] = len(opportunities)
        return opportunities

    def _scrape_category(
        self,
        url: str,
        opp_type: str
    ) -> List[ScrapedOpportunity]:
        """
        Scrape une catégorie.
        """
        soup = self.fetch_page(url)
        if not soup:
            return []

        opportunities = []

        # Structure WordPress
        articles = soup.select('article, .post, .entry')

        for article in articles:
            try:
                opp = self._parse_article(article, opp_type)
                if opp:
                    opportunities.append(opp)
            except Exception as e:
                self.log_error(f"Erreur parsing: {e}")

        return opportunities

    def _parse_article(
        self,
        article,
        opp_type: str
    ) -> Optional[ScrapedOpportunity]:
        """
        Parse un article en ScrapedOpportunity.
        """
        title_elem = article.select_one('h2 a, h3 a, .entry-title a')
        if not title_elem:
            return None

        title = self.clean_text(title_elem.get_text())
        link = title_elem.get('href', '')

        # Extrait
        excerpt = ''
        excerpt_elem = article.select_one('.entry-summary, .excerpt, p')
        if excerpt_elem:
            excerpt = self.clean_text(excerpt_elem.get_text())

        # Date
        date_elem = article.select_one('time, .entry-date')
        pub_date = None
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text()
            pub_date = self.parse_date(date_str)

        # Génère un ID externe unique
        slug = link.rstrip('/').split('/')[-1] if link else ''
        external_id = f"afric_{slug}"

        return ScrapedOpportunity(
            title=title,
            description=excerpt or f"Opportunité: {title}",
            organization='Afri-Carrières',
            opportunity_type=opp_type,
            source_url=link,
            application_link=link,
            location='Afrique / International',
            publication_date=pub_date,
            external_id=external_id,
        )
