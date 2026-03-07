"""
OpportuCI - Scrapers Package
============================
Scrapers modulaires pour chaque source d'opportunités.
"""
from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry

# Import all scrapers to register them
from .greatyop_scraper import GreatYopScraper
from .educarriere_scraper import EducarriereScraper
from .stageci_scraper import StageCIScraper

__all__ = [
    'BaseScraper',
    'ScrapedOpportunity',
    'ScraperRegistry',
    'GreatYopScraper',
    'EducarriereScraper',
    'StageCIScraper',
]
