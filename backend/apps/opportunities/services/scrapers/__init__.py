"""
OpportuCI - Scrapers Package
============================
Scrapers modulaires pour chaque source d'opportunités.
"""
from .base import BaseScraper, ScrapedOpportunity
from .registry import ScraperRegistry

__all__ = ['BaseScraper', 'ScrapedOpportunity', 'ScraperRegistry']
