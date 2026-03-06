"""
OpportuCI - Scraper Registry
============================
Registre central pour tous les scrapers disponibles.
"""
import logging
from typing import Dict, Type, Optional, List
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """
    Registre singleton pour tous les scrapers.

    Permet de découvrir et instancier les scrapers dynamiquement
    depuis leur identifiant (stocké dans OpportunitySource).
    """

    _scrapers: Dict[str, Type[BaseScraper]] = {}

    @classmethod
    def register(cls, scraper_class: Type[BaseScraper]) -> Type[BaseScraper]:
        """
        Décorateur pour enregistrer un scraper.

        Usage:
            @ScraperRegistry.register
            class GreatYopScraper(BaseScraper):
                SCRAPER_ID = 'greatyop'
                ...
        """
        scraper_id = scraper_class.SCRAPER_ID
        if scraper_id in cls._scrapers:
            logger.warning(f"Scraper {scraper_id} déjà enregistré, remplacement")
        cls._scrapers[scraper_id] = scraper_class
        logger.debug(f"Scraper enregistré: {scraper_id}")
        return scraper_class

    @classmethod
    def get(cls, scraper_id: str) -> Optional[Type[BaseScraper]]:
        """
        Récupère une classe de scraper par son ID.
        """
        return cls._scrapers.get(scraper_id)

    @classmethod
    def create(cls, scraper_id: str, config: dict = None) -> Optional[BaseScraper]:
        """
        Crée une instance de scraper.

        Args:
            scraper_id: Identifiant du scraper
            config: Configuration personnalisée

        Returns:
            Instance du scraper ou None
        """
        scraper_class = cls.get(scraper_id)
        if scraper_class:
            return scraper_class(config=config)
        logger.error(f"Scraper non trouvé: {scraper_id}")
        return None

    @classmethod
    def list_available(cls) -> List[Dict]:
        """
        Liste tous les scrapers disponibles.
        """
        return [
            {
                'id': scraper_id,
                'name': scraper_class.SCRAPER_NAME,
                'url': scraper_class.SOURCE_URL,
            }
            for scraper_id, scraper_class in cls._scrapers.items()
        ]

    @classmethod
    def get_all_ids(cls) -> List[str]:
        """Retourne tous les IDs de scrapers."""
        return list(cls._scrapers.keys())


# Auto-import des scrapers pour les enregistrer
def _auto_register_scrapers():
    """Importe automatiquement les scrapers pour les enregistrer."""
    try:
        from . import greatyop_scraper  # noqa
        from . import africarrieres_scraper  # noqa
        from . import manual_scraper  # noqa
    except ImportError as e:
        logger.debug(f"Import scrapers: {e}")


_auto_register_scrapers()
