"""
OpportuCI - Stage.ci Scraper
============================
Scraper pour stage.ci (stages en Côte d'Ivoire)
Utilise Playwright pour gérer le JavaScript.
"""
import re
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry

logger = logging.getLogger(__name__)


@ScraperRegistry.register
class StageCIScraper(BaseScraper):
    """
    Scraper pour Stage.ci - Plateforme de stages en Côte d'Ivoire.

    Source: https://www.stage.ci/
    Types: Stages uniquement
    """

    SCRAPER_ID = 'stageci'
    SCRAPER_NAME = 'Stage.ci'
    SOURCE_URL = 'https://www.stage.ci'

    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Scrape les stages depuis Stage.ci avec Playwright.
        """
        opportunities = []

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                jobs_url = f"{self.SOURCE_URL}/latest-jobs"
                self.log_info(f"Scraping: {jobs_url}")

                try:
                    page.goto(jobs_url, timeout=30000)
                    page.wait_for_load_state('networkidle', timeout=15000)

                    opportunities = self._parse_jobs_page(page, context)

                except Exception as e:
                    self.log_error(f"Error scraping Stage.ci: {e}")

                browser.close()

        except ImportError:
            self.log_error("Playwright not installed")
            return self._fallback_scrape()
        except Exception as e:
            self.log_error(f"Playwright error: {e}")
            return self._fallback_scrape()

        self.stats['opportunities_found'] = len(opportunities)
        self.log_info(f"Total: {len(opportunities)} stages trouvés")

        return opportunities

    def _parse_jobs_page(self, page, context) -> List[ScrapedOpportunity]:
        """
        Parse la page des offres de Stage.ci (/latest-jobs).
        """
        opportunities = []

        # Chercher les liens d'offres avec le pattern /ID-slug
        offer_links = page.query_selector_all('a[href*="stage.ci/"]')

        seen_ids = set()
        for link in offer_links:
            try:
                href = link.get_attribute('href')
                if not href:
                    continue

                # Filtrer pour ne garder que les offres (URLs avec /ID-slug)
                match = re.search(r'/(\d+)-([a-z0-9-]+)$', href, re.I)
                if not match:
                    continue

                offer_id = match.group(1)
                if offer_id in seen_ids:
                    continue
                seen_ids.add(offer_id)

                # Recuperer le titre depuis le texte du lien
                title = link.inner_text().strip()

                # Si le titre est vide ou trop court, extraire du slug
                if not title or len(title) < 3:
                    slug = match.group(2)
                    title = slug.replace('-', ' ').title()

                external_id = f"stageci_{offer_id}"

                # URL complete
                if not href.startswith('http'):
                    href = f"{self.SOURCE_URL}/{offer_id}-{match.group(2)}"

                self.log_info(f"  Found: {title[:40]}... ({external_id})")

                # Creer l'opportunite avec infos de base (sans scraper les details)
                opp = ScrapedOpportunity(
                    title=title[:255],
                    description=f"Stage propose sur Stage.ci. Consultez le lien pour plus de details.",
                    organization="Entreprise (via Stage.ci)",
                    opportunity_type='internship',
                    source_url=href,
                    application_link=href,
                    location="Abidjan, Cote d'Ivoire",
                    deadline=timezone.now() + timedelta(days=60),
                    publication_date=timezone.now(),
                    education_level='bts',
                    external_id=external_id,
                )
                opportunities.append(opp)

            except Exception as e:
                self.log_error(f"Error parsing link: {e}")
                continue

        return opportunities

    def _scrape_offer_details(self, context, url: str, title: str, external_id: str) -> Optional[ScrapedOpportunity]:
        """
        Scrape les détails d'une offre de stage.
        """
        try:
            detail_page = context.new_page()
            detail_page.goto(url, timeout=20000)
            detail_page.wait_for_load_state('domcontentloaded')

            # Description
            description = ""
            desc_elem = detail_page.query_selector('.description, .content, main, article')
            if desc_elem:
                description = desc_elem.inner_text().strip()[:3000]

            # Organisation
            organization = "Entreprise (via Stage.ci)"
            org_elem = detail_page.query_selector('.company, .entreprise, .societe, h2')
            if org_elem:
                org_text = org_elem.inner_text().strip()
                if org_text and len(org_text) < 100:
                    organization = org_text

            # Localisation - par défaut Abidjan
            location = "Abidjan, Côte d'Ivoire"
            loc_elem = detail_page.query_selector('.location, .lieu, .localisation')
            if loc_elem:
                loc_text = loc_elem.inner_text().strip()
                if loc_text:
                    location = loc_text[:255]

            # Domaine/Catégorie
            skills = []
            cat_elem = detail_page.query_selector('.category, .domaine, .secteur')
            if cat_elem:
                cat_text = cat_elem.inner_text().strip()
                if cat_text:
                    skills = [cat_text]

            detail_page.close()

            return ScrapedOpportunity(
                title=title[:255],
                description=description or f"Stage proposé sur Stage.ci: {title}",
                organization=organization,
                opportunity_type='internship',
                source_url=url,
                application_link=url,
                location=location,
                deadline=timezone.now() + timedelta(days=60),  # Stages généralement ouverts longtemps
                publication_date=timezone.now(),
                education_level='bts',
                skills_required=skills,
                external_id=external_id,
            )

        except Exception as e:
            self.log_error(f"Error scraping details for {url}: {e}")
            return None

    def _fallback_scrape(self) -> List[ScrapedOpportunity]:
        """
        Fallback sans Playwright.
        """
        self.log_info("Using fallback scraper")

        opportunities = []
        soup = self.fetch_page(self.SOURCE_URL)

        if not soup:
            return opportunities

        # Parser les liens
        for link in soup.select('a[href*="/"]')[:30]:
            try:
                href = link.get('href', '')
                title = link.get_text(strip=True)

                match = re.search(r'/(\d+)-', href)
                if not match:
                    continue

                external_id = f"stageci_{match.group(1)}"

                if not href.startswith('http'):
                    href = f"{self.SOURCE_URL}{href}"

                opportunities.append(ScrapedOpportunity(
                    title=title[:255] if title else f"Stage #{match.group(1)}",
                    description=f"Stage proposé sur Stage.ci",
                    organization="Entreprise (via Stage.ci)",
                    opportunity_type='internship',
                    source_url=href,
                    application_link=href,
                    location="Abidjan, Côte d'Ivoire",
                    deadline=timezone.now() + timedelta(days=60),
                    publication_date=timezone.now(),
                    external_id=external_id,
                ))

            except Exception as e:
                continue

        return opportunities
