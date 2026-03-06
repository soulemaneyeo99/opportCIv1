"""
OpportuCI - GreatYop Scraper
============================
Scraper pour greatyop.com (bourses, stages, formations francophones)
"""
import re
from typing import List, Optional
from datetime import datetime
from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry


@ScraperRegistry.register
class GreatYopScraper(BaseScraper):
    """
    Scraper pour GreatYop - Opportunités francophones.

    Source: https://greatyop.com/cote-divoire/
    Types: Bourses, Stages, Formations, Concours
    """

    SCRAPER_ID = 'greatyop'
    SCRAPER_NAME = 'GreatYop'
    SOURCE_URL = 'https://greatyop.com'

    # Pages à scraper (URLs anglais - structure actuelle du site)
    PAGES = {
        'scholarships': '/category/scholarships/',
        'internships': '/category/internships/',
        'trainings': '/category/trainings/',
        'competitions': '/category/competition/',
        'jobs': '/category/jobs/',
    }

    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Scrape les opportunités depuis GreatYop.
        """
        opportunities = []

        # Scraper les catégories configurées ou toutes
        categories = self.config.get('categories', ['scholarships', 'internships'])

        for category in categories:
            page_path = self.PAGES.get(category, self.PAGES['scholarships'])
            url = f"{self.SOURCE_URL}{page_path}"

            self.log_info(f"Scraping {category}: {url}")

            page_opps = self._scrape_listing_page(url, category)
            opportunities.extend(page_opps)

            # Pagination (si configuré)
            max_pages = self.config.get('max_pages', 3)
            for page_num in range(2, max_pages + 1):
                paginated_url = f"{url}page/{page_num}/"
                page_opps = self._scrape_listing_page(paginated_url, category)
                if not page_opps:
                    break
                opportunities.extend(page_opps)

        self.stats['opportunities_found'] = len(opportunities)
        self.log_info(f"Total: {len(opportunities)} opportunités trouvées")

        return opportunities

    def _scrape_listing_page(
        self,
        url: str,
        category: str
    ) -> List[ScrapedOpportunity]:
        """
        Scrape une page de listing.
        """
        soup = self.fetch_page(url)
        if not soup:
            return []

        opportunities = []

        # Sélecteur pour les articles (structure WordPress commune)
        articles = soup.select('article.post, .entry-content article, .post-item')

        for article in articles:
            try:
                opp = self._parse_article(article, category)
                if opp:
                    opportunities.append(opp)
            except Exception as e:
                self.log_error(f"Erreur parsing article: {e}")

        return opportunities

    def _parse_article(
        self,
        article,
        category: str
    ) -> Optional[ScrapedOpportunity]:
        """
        Parse un article HTML en ScrapedOpportunity.
        """
        # Titre
        title_elem = article.select_one('h2 a, h3 a, .entry-title a')
        if not title_elem:
            return None

        title = self.clean_text(title_elem.get_text())
        link = title_elem.get('href', '')

        # Extrait/description courte
        excerpt_elem = article.select_one('.entry-summary, .excerpt, p')
        excerpt = self.clean_text(excerpt_elem.get_text()) if excerpt_elem else ''

        # Date de publication
        date_elem = article.select_one('.entry-date, .post-date, time')
        pub_date = None
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get_text()
            pub_date = self.parse_date(date_str)

        # Déterminer le type
        opp_type = self._category_to_type(category)

        # Scraper la page de détail pour plus d'infos
        full_data = self._scrape_detail_page(link) if link else {}

        return ScrapedOpportunity(
            title=title,
            description=full_data.get('description', excerpt),
            organization=full_data.get('organization', 'GreatYop'),
            opportunity_type=opp_type,
            source_url=link,
            application_link=full_data.get('application_link', link),
            location=full_data.get('location', 'International'),
            deadline=full_data.get('deadline'),
            publication_date=pub_date,
            education_level=full_data.get('education_level', 'any'),
            requirements=full_data.get('requirements', ''),
            external_id=f"gyop_{link.split('/')[-2]}" if link else '',
        )

    def _scrape_detail_page(self, url: str) -> dict:
        """
        Scrape la page de détail d'une opportunité.
        """
        # Limiter les appels détaillés pour éviter de surcharger
        if not self.config.get('fetch_details', True):
            return {}

        soup = self.fetch_page(url)
        if not soup:
            return {}

        data = {}

        # Contenu principal
        content = soup.select_one('.entry-content, .post-content, article')
        if content:
            data['description'] = self.clean_text(content.get_text()[:2000])

            # Chercher la deadline dans le texte
            deadline = self._extract_deadline(content.get_text())
            if deadline:
                data['deadline'] = deadline

            # Chercher l'organisation
            org = self._extract_organization(content.get_text())
            if org:
                data['organization'] = org

            # Chercher le lien de candidature
            apply_link = content.select_one(
                'a[href*="apply"], a[href*="candidature"], a[href*="postuler"]'
            )
            if apply_link:
                data['application_link'] = apply_link.get('href')

            # Niveau d'éducation
            data['education_level'] = self.detect_education_level(
                content.get_text()
            )

        return data

    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """
        Extrait la date limite depuis le texte.
        """
        # Patterns courants pour les deadlines
        patterns = [
            r'date limite[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'deadline[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'avant le[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'jusqu\'au[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
        ]

        text_lower = text.lower()

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1) if len(match.groups()) == 1 else match.group(0)
                return self.parse_date(date_str)

        return None

    def _extract_organization(self, text: str) -> Optional[str]:
        """
        Extrait le nom de l'organisation.
        """
        # Chercher patterns comme "offert par X" ou "proposé par X"
        patterns = [
            r'offert[es]?\s+par\s+([A-Za-zÀ-ÿ\s&\'-]+)',
            r'proposé[es]?\s+par\s+([A-Za-zÀ-ÿ\s&\'-]+)',
            r'organisé[es]?\s+par\s+([A-Za-zÀ-ÿ\s&\'-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                org = match.group(1).strip()
                # Limiter la longueur et nettoyer
                return org[:100].rstrip('.')

        return None

    def _category_to_type(self, category: str) -> str:
        """
        Convertit la catégorie GreatYop en type OpportuCI.
        """
        mapping = {
            'scholarships': 'scholarship',
            'internships': 'internship',
            'trainings': 'training',
            'competitions': 'competition',
            'cote_ivoire': 'other',
        }
        return mapping.get(category, 'other')
