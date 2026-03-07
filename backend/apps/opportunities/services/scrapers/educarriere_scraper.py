"""
OpportuCI - Educarriere.ci Scraper
==================================
Scraper pour emploi.educarriere.ci (emplois et stages en Côte d'Ivoire)
Utilise Playwright pour gérer le JavaScript.
"""
import re
import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone as tz
from django.utils import timezone

from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry

logger = logging.getLogger(__name__)


@ScraperRegistry.register
class EducarriereScraper(BaseScraper):
    """
    Scraper pour Educarriere.ci - Emplois et Stages en Côte d'Ivoire.

    Source: https://emploi.educarriere.ci/
    Types: Emplois, Stages
    """

    SCRAPER_ID = 'educarriere'
    SCRAPER_NAME = 'Educarriere.ci'
    SOURCE_URL = 'https://emploi.educarriere.ci'

    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Scrape les opportunités depuis Educarriere.ci avec Playwright.
        """
        opportunities = []

        try:
            from playwright.sync_api import sync_playwright

            max_pages = self.config.get('max_pages', 5)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                for page_num in range(1, max_pages + 1):
                    url = f"{self.SOURCE_URL}/nos-offres?page={page_num}"
                    self.log_info(f"Scraping page {page_num}: {url}")

                    try:
                        page.goto(url, timeout=60000)
                        # Attendre que la page soit chargée
                        page.wait_for_load_state('networkidle', timeout=30000)

                        # Chercher les liens d'offres directement
                        page_opps = self._parse_listing_page(page)
                        if not page_opps:
                            self.log_info(f"No more opportunities on page {page_num}")
                            break

                        opportunities.extend(page_opps)
                        self.log_info(f"Found {len(page_opps)} opportunities on page {page_num}")

                    except Exception as e:
                        self.log_error(f"Error on page {page_num}: {e}")
                        # Essayer le fallback
                        if page_num == 1:
                            return self._fallback_scrape()
                        break

                browser.close()

        except ImportError:
            self.log_error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            return self._fallback_scrape()
        except Exception as e:
            self.log_error(f"Playwright error: {e}")
            return self._fallback_scrape()

        self.stats['opportunities_found'] = len(opportunities)
        self.log_info(f"Total: {len(opportunities)} opportunités trouvées")

        return opportunities

    def _parse_listing_page(self, page) -> List[ScrapedOpportunity]:
        """
        Parse la page de listing avec Playwright.
        Collecte les IDs uniques puis scrape les détails.
        """
        opportunities = []

        # Récupérer tous les liens d'offres
        offer_links = page.query_selector_all('a[href*="emploi.educarriere.ci/offre-"]')

        # Collecter les IDs uniques avec leurs meilleures infos
        offers_data = {}
        for link in offer_links:
            try:
                href = link.get_attribute('href')
                if not href:
                    continue

                match = re.search(r'offre-(\d+)', href)
                if not match:
                    continue

                offer_id = match.group(1)
                text = link.inner_text().strip()

                # Garder le meilleur titre pour chaque ID
                if offer_id not in offers_data:
                    offers_data[offer_id] = {'href': href, 'title': text}
                elif len(text) > len(offers_data[offer_id]['title']):
                    offers_data[offer_id]['title'] = text

            except Exception:
                continue

        self.log_info(f"Found {len(offers_data)} unique offers")

        # Scraper les détails de chaque offre
        max_to_scrape = self.config.get('max_offers_per_page', 20)
        context = page.context

        for offer_id, data in list(offers_data.items())[:max_to_scrape]:
            try:
                href = data['href']
                if not href.startswith('http'):
                    href = f"https://emploi.educarriere.ci{href}"

                external_id = f"educarriere_{offer_id}"
                title = data['title']

                # Si pas de titre, scraper la page de détail
                if not title or len(title) < 5 or title.upper() in ['EMPLOI', 'STAGE', 'VOIR']:
                    opp = self._scrape_offer_details(context, href, external_id)
                else:
                    opp_type = 'internship' if 'stage' in title.lower() else 'job'
                    opp = ScrapedOpportunity(
                        title=title[:255],
                        description=f"Offre publiée sur Educarriere.ci. Consultez le lien pour plus de détails.",
                        organization="Entreprise (via Educarriere.ci)",
                        opportunity_type=opp_type,
                        source_url=href,
                        application_link=href,
                        location="Côte d'Ivoire",
                        deadline=timezone.now() + timedelta(days=30),
                        publication_date=timezone.now(),
                        education_level='any',
                        external_id=external_id,
                    )

                if opp:
                    opportunities.append(opp)
                    self.log_info(f"  ✓ {opp.title[:40]}...")

            except Exception as e:
                self.log_error(f"Error processing offer {offer_id}: {e}")
                continue

        return opportunities

    def _scrape_offer_details(self, context, url: str, external_id: str) -> Optional[ScrapedOpportunity]:
        """
        Scrape les détails d'une offre spécifique.
        """
        try:
            detail_page = context.new_page()
            detail_page.goto(url, timeout=20000)
            detail_page.wait_for_load_state('domcontentloaded')

            # Titre - essayer plusieurs sélecteurs
            title = ""
            title_elem = detail_page.query_selector('h1, .titre-offre, .job-title, .title')
            if title_elem:
                title = title_elem.inner_text().strip()[:255]

            if not title:
                # Extraire du meta ou de l'URL
                title = detail_page.title() or f"Offre {external_id}"
                title = title.replace(' - Educarriere', '').strip()[:255]

            # Description
            description = ""
            desc_elem = detail_page.query_selector('.description, .content, .offre-content, article, main')
            if desc_elem:
                description = desc_elem.inner_text().strip()[:3000]

            # Organisation
            organization = "Entreprise (via Educarriere.ci)"
            org_elem = detail_page.query_selector('.entreprise, .company, .societe, .employeur')
            if org_elem:
                org_text = org_elem.inner_text().strip()
                if org_text and len(org_text) < 200:
                    organization = org_text[:255]

            # Localisation
            location = "Côte d'Ivoire"
            loc_elem = detail_page.query_selector('.localisation, .location, .lieu, .ville')
            if loc_elem:
                loc_text = loc_elem.inner_text().strip()
                if loc_text:
                    location = loc_text[:255]

            # Date limite - chercher dans le texte
            deadline = None
            body = detail_page.query_selector('body')
            if body:
                page_text = body.inner_text()
                deadline = self._parse_french_date(page_text)

            if not deadline:
                deadline = timezone.now() + timedelta(days=30)

            # Déterminer le type
            opp_type = 'job'
            if title:
                title_lower = title.lower()
                if 'stage' in title_lower or 'stagiaire' in title_lower:
                    opp_type = 'internship'

            detail_page.close()

            if not title or len(title) < 3:
                return None

            return ScrapedOpportunity(
                title=title,
                description=description or f"Offre publiée sur Educarriere.ci: {title}",
                organization=organization,
                opportunity_type=opp_type,
                source_url=url,
                application_link=url,
                location=location,
                deadline=deadline,
                publication_date=timezone.now(),
                education_level='any',
                external_id=external_id,
            )

        except Exception as e:
            self.log_error(f"Error scraping details for {url}: {e}")
            return None

    def _parse_french_date(self, text: str) -> Optional[datetime]:
        """
        Parse une date en français (ex: "27/03/2026" ou "27 mars 2026").
        """
        if not text:
            return None

        text = text.strip().lower()

        # Format JJ/MM/AAAA
        match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return datetime(year, month, day, 23, 59, tzinfo=tz.utc)
            except ValueError:
                pass

        # Format "JJ mois AAAA"
        months = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }

        for month_name, month_num in months.items():
            if month_name in text:
                match = re.search(rf'(\d{{1,2}})\s*{month_name}\s*(\d{{4}})', text)
                if match:
                    day, year = int(match.group(1)), int(match.group(2))
                    try:
                        return datetime(year, month_num, day, 23, 59, tzinfo=tz.utc)
                    except ValueError:
                        pass

        return None

    def _fallback_scrape(self) -> List[ScrapedOpportunity]:
        """
        Fallback si Playwright ne fonctionne pas - utilise requests.
        """
        self.log_info("Using fallback scraper (requests)")

        opportunities = []
        soup = self.fetch_page(f"{self.SOURCE_URL}/nos-offres")

        if not soup:
            return opportunities

        # Essayer de parser les offres sans JS
        offer_links = soup.select('a[href*="/offre-"]')

        for link in offer_links[:20]:  # Limiter à 20
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                if not href.startswith('http'):
                    href = f"{self.SOURCE_URL}{href}"

                match = re.search(r'offre-(\d+)', href)
                external_id = f"educarriere_{match.group(1)}" if match else None

                if not external_id:
                    continue

                opp_type = 'internship' if 'stage' in title.lower() else 'job'

                opportunities.append(ScrapedOpportunity(
                    title=title[:255],
                    description=f"Offre publiée sur Educarriere.ci: {title}",
                    organization="Entreprise (via Educarriere.ci)",
                    opportunity_type=opp_type,
                    source_url=href,
                    application_link=href,
                    location="Côte d'Ivoire",
                    deadline=timezone.now() + timedelta(days=30),
                    publication_date=timezone.now(),
                    external_id=external_id,
                ))

            except Exception as e:
                self.log_error(f"Fallback parse error: {e}")
                continue

        return opportunities
