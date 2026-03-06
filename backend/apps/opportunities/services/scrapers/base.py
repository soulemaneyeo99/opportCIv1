"""
OpportuCI - Base Scraper
========================
Classe abstraite pour tous les scrapers d'opportunités.
"""
import logging
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class ScrapedOpportunity:
    """Structure de données normalisée pour une opportunité scrapée."""

    # Identification (requis)
    title: str
    description: str
    organization: str

    # Classification
    opportunity_type: str = 'other'  # scholarship, internship, job, training, competition, event

    # URLs
    source_url: str = ''
    application_link: str = ''

    # Localisation
    location: str = ''
    is_remote: bool = False

    # Dates
    deadline: Optional[datetime] = None
    publication_date: Optional[datetime] = None
    start_date: Optional[datetime] = None

    # Exigences
    education_level: str = 'any'
    skills_required: List[str] = field(default_factory=list)
    experience_years: int = 0
    requirements: str = ''

    # Financier
    compensation: str = ''

    # Métadonnées source
    external_id: str = ''
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def generate_external_id(self) -> str:
        """Génère un ID unique basé sur le contenu."""
        if self.external_id:
            return self.external_id
        content = f"{self.title}|{self.organization}|{self.source_url}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour création de modèle."""
        return {
            'title': self.title[:255],
            'description': self.description,
            'organization': self.organization[:255],
            'opportunity_type': self.opportunity_type,
            'application_link': self.application_link or self.source_url,
            'location': self.location[:255] if self.location else '',
            'is_remote': self.is_remote,
            'deadline': self.deadline,
            'publication_date': self.publication_date or timezone.now(),
            'start_date': self.start_date,
            'education_level': self.education_level,
            'skills_required': self.skills_required,
            'experience_years': self.experience_years,
            'requirements': self.requirements,
            'compensation': self.compensation[:255] if self.compensation else '',
            'external_id': self.generate_external_id(),
        }


class BaseScraper(ABC):
    """
    Classe de base abstraite pour tous les scrapers.

    Chaque source (GreatYop, Educarrière, etc.) hérite de cette classe
    et implémente ses propres méthodes d'extraction.
    """

    # Identifiant unique du scraper
    SCRAPER_ID: str = 'base'
    SCRAPER_NAME: str = 'Base Scraper'
    SOURCE_URL: str = ''

    # Configuration par défaut
    DEFAULT_TIMEOUT: int = 60
    DEFAULT_HEADERS: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: Configuration personnalisée (depuis OpportunitySource.scrape_config)
        """
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.errors: List[str] = []
        self.stats = {
            'pages_fetched': 0,
            'opportunities_found': 0,
            'opportunities_saved': 0,
            'errors': 0,
        }

    @abstractmethod
    def scrape(self) -> List[ScrapedOpportunity]:
        """
        Méthode principale de scraping.

        Returns:
            Liste d'opportunités scrapées et normalisées
        """
        pass

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Récupère et parse une page HTML.

        Args:
            url: URL à scraper

        Returns:
            BeautifulSoup object ou None en cas d'erreur
        """
        try:
            timeout = self.config.get('timeout', self.DEFAULT_TIMEOUT)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            self.stats['pages_fetched'] += 1

            return BeautifulSoup(response.text, 'html.parser')

        except requests.RequestException as e:
            self.log_error(f"Erreur fetch {url}: {e}")
            return None

    def fetch_json(self, url: str) -> Optional[Dict]:
        """
        Récupère des données JSON (pour les APIs).
        """
        try:
            timeout = self.config.get('timeout', self.DEFAULT_TIMEOUT)
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()

            self.stats['pages_fetched'] += 1

            return response.json()

        except (requests.RequestException, ValueError) as e:
            self.log_error(f"Erreur fetch JSON {url}: {e}")
            return None

    def parse_date(self, date_str: str, formats: List[str] = None) -> Optional[datetime]:
        """
        Parse une date depuis différents formats.

        Args:
            date_str: Chaîne de date
            formats: Liste de formats à essayer
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        default_formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d %B %Y',
            '%d %b %Y',
            '%B %d, %Y',
            '%Y-%m-%dT%H:%M:%S',
        ]

        formats = formats or default_formats

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except ValueError:
                continue

        self.log_error(f"Format de date non reconnu: {date_str}")
        return None

    def detect_opportunity_type(self, text: str) -> str:
        """
        Détecte le type d'opportunité depuis le texte.
        """
        text_lower = text.lower()

        type_keywords = {
            'scholarship': ['bourse', 'scholarship', 'fellowship', 'grant', 'financement'],
            'internship': ['stage', 'internship', 'stagiaire', 'apprentissage'],
            'job': ['emploi', 'job', 'cdi', 'cdd', 'recrutement', 'poste', 'hiring'],
            'training': ['formation', 'training', 'cours', 'certification', 'atelier'],
            'competition': ['concours', 'competition', 'challenge', 'prix', 'award'],
            'event': ['événement', 'conférence', 'séminaire', 'webinaire', 'forum'],
        }

        for opp_type, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return opp_type

        return 'other'

    def detect_education_level(self, text: str) -> str:
        """
        Détecte le niveau d'éducation requis.
        """
        text_lower = text.lower()

        level_keywords = {
            'phd': ['doctorat', 'phd', 'thèse', 'bac+8'],
            'master': ['master', 'bac+5', 'mba', 'ingénieur'],
            'license': ['licence', 'bac+3', 'bachelor'],
            'bts': ['bts', 'dut', 'bac+2'],
            'bac': ['baccalauréat', 'bac', 'terminale'],
        }

        for level, keywords in level_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return level

        return 'any'

    def clean_text(self, text: str) -> str:
        """Nettoie le texte (espaces, HTML, etc.)"""
        if not text:
            return ''
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def log_error(self, message: str) -> None:
        """Log une erreur et l'ajoute aux stats."""
        logger.error(f"[{self.SCRAPER_ID}] {message}")
        self.errors.append(message)
        self.stats['errors'] += 1

    def log_info(self, message: str) -> None:
        """Log une info."""
        logger.info(f"[{self.SCRAPER_ID}] {message}")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du scraping."""
        return {
            **self.stats,
            'scraper_id': self.SCRAPER_ID,
            'scraper_name': self.SCRAPER_NAME,
            'errors_list': self.errors[-10:],  # Last 10 errors
        }
