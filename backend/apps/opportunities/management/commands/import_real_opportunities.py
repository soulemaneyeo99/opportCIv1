"""
OpportuCI - Import Real Opportunities
=====================================
Importe de vraies opportunités vérifiées pour la phase pilote.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.opportunities.models import Opportunity, OpportunitySource, OpportunityCategory


class Command(BaseCommand):
    help = 'Importe de vraies opportunités vérifiées pour la phase pilote'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-demo',
            action='store_true',
            help='Supprimer les données de démo (sans external_id)',
        )

    def handle(self, *args, **options):
        if options['clear_demo']:
            count = Opportunity.objects.filter(external_id__isnull=True).count()
            count += Opportunity.objects.filter(external_id='').count()
            Opportunity.objects.filter(external_id__isnull=True).delete()
            Opportunity.objects.filter(external_id='').delete()
            self.stdout.write(
                self.style.SUCCESS(f'✓ {count} opportunités de démo supprimées')
            )

        # Créer les sources
        sources = self._create_sources()
        categories = self._create_categories()

        # Importer les vraies opportunités
        now = timezone.now()
        opportunities = self._get_real_opportunities(now)

        created = 0
        for opp_data in opportunities:
            source_name = opp_data.pop('source_name')
            category_slug = opp_data.pop('category_slug')

            source = sources.get(source_name)
            category = categories.get(category_slug)

            # Vérifier si existe déjà
            if Opportunity.objects.filter(external_id=opp_data['external_id']).exists():
                self.stdout.write(f"  → Existe: {opp_data['title'][:40]}...")
                continue

            Opportunity.objects.create(
                source=source,
                category=category,
                status='published',
                publication_date=now,
                **opp_data
            )
            created += 1
            self.stdout.write(f"  ✓ {opp_data['title'][:50]}...")

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ {created} vraies opportunités importées!')
        )

    def _create_sources(self):
        """Crée les sources."""
        sources_data = [
            ('GreatYop', 'website', 'https://greatyop.com'),
            ('Sciences Po', 'website', 'https://www.sciencespo.fr'),
            ('Google', 'website', 'https://grow.google'),
            ('Campus France', 'website', 'https://www.campusfrance.org'),
            ('AUF', 'website', 'https://www.auf.org'),
        ]
        sources = {}
        for name, stype, url in sources_data:
            source, _ = OpportunitySource.objects.get_or_create(
                name=name,
                defaults={'source_type': stype, 'url': url}
            )
            sources[name] = source
        return sources

    def _create_categories(self):
        """Crée les catégories."""
        cats = [
            ('Bourses', 'bourses'),
            ('Stages', 'stages'),
            ('Emplois', 'emplois'),
            ('Formations', 'formations'),
        ]
        categories = {}
        for name, slug in cats:
            cat, _ = OpportunityCategory.objects.get_or_create(
                slug=slug, defaults={'name': name}
            )
            categories[slug] = cat
        return categories

    def _get_real_opportunities(self, now):
        """
        Vraies opportunités vérifiées (sources réelles).
        Les liens application_link sont les vrais liens vers les candidatures.
        """
        return [
            # === BOURSES RÉELLES ===
            {
                'external_id': 'gyop_heinrich-boll-2026',
                'title': 'Bourse Heinrich Böll Foundation - Allemagne 2026-2027',
                'description': '''La Fondation Heinrich Böll offre des bourses d'études aux étudiants internationaux pour des études de Master et Doctorat en Allemagne.

Programme:
- Allocation mensuelle de 934€ (Master) ou 1,350€ (Doctorat)
- Allocation familiale si applicable
- Cours d'allemand gratuits
- Soutien académique et professionnel

La fondation recherche des candidats engagés dans les domaines:
- Écologie et durabilité
- Démocratie et droits humains
- Égalité des genres
- Migration et réfugiés

Conditions:
- Excellent dossier académique
- Engagement social/politique démontré
- Admission dans une université allemande
- Niveau d'allemand ou d'anglais selon le programme''',
                'organization': 'Heinrich Böll Foundation',
                'opportunity_type': 'scholarship',
                'source_name': 'GreatYop',
                'category_slug': 'bourses',
                'location': 'Allemagne',
                'deadline': now + timedelta(days=179),
                'education_level': 'master',
                'skills_required': ['Allemand ou Anglais', 'Engagement social'],
                'compensation': '934€ - 1,350€/mois',
                'application_link': 'https://www.boell.de/en/scholarships',
                'featured': True,
            },
            {
                'external_id': 'gyop_mistral-france-2026',
                'title': 'Bourse MISTRAL Excellence - France 2026-2027',
                'description': '''L'Université d'Avignon propose la bourse MISTRAL pour les étudiants internationaux souhaitant poursuivre un Master en France.

Avantages:
- Exonération des frais de scolarité
- Allocation de vie mensuelle
- Accompagnement à l'installation

Domaines d'études:
- Sciences et Technologies
- Patrimoine et Culture
- Agrosciences
- Numérique

Critères:
- Excellence académique (minimum 14/20 ou équivalent)
- Motivation pour étudier en France
- Projet professionnel clair''',
                'organization': 'Université d\'Avignon',
                'opportunity_type': 'scholarship',
                'source_name': 'GreatYop',
                'category_slug': 'bourses',
                'location': 'France (Avignon)',
                'deadline': now + timedelta(days=16),
                'education_level': 'master',
                'skills_required': ['Français', 'Excellence académique'],
                'compensation': 'Bourse complète',
                'application_link': 'https://univ-avignon.fr/formation/candidater-sinscrire/bourses-et-aides-financieres/',
            },
            {
                'external_id': 'spo_mastercard-2026',
                'title': 'Mastercard Foundation Scholars Program - Sciences Po Paris',
                'description': '''Le programme Mastercard Foundation Scholars offre des bourses complètes à des jeunes Africains talentueux pour étudier à Sciences Po Paris.

La bourse couvre:
- Frais de scolarité intégraux (15,000€/an)
- Logement et repas
- Allocation mensuelle de vie
- Billet d'avion aller-retour
- Assurance maladie
- Soutien académique et mentorat
- Programme de leadership

Masters éligibles:
- Master in International Public Management
- Master in Human Rights and Humanitarian Action
- Master in International Development
- Master in International Economic Policy

Profil recherché:
- Citoyen africain
- Moins de 35 ans
- Excellence académique
- Engagement communautaire démontré
- Leadership potentiel''',
                'organization': 'Sciences Po Paris / Mastercard Foundation',
                'opportunity_type': 'scholarship',
                'source_name': 'Sciences Po',
                'category_slug': 'bourses',
                'location': 'France (Paris)',
                'deadline': now + timedelta(days=90),
                'education_level': 'license',
                'skills_required': ['Anglais', 'Leadership', 'Engagement communautaire'],
                'compensation': 'Bourse complète (~70,000€ sur 2 ans)',
                'application_link': 'https://www.sciencespo.fr/admissions/en/mcfsp',
                'featured': True,
            },
            {
                'external_id': 'auf_bourses-2026',
                'title': 'Bourses de mobilité AUF 2026',
                'description': '''L'Agence Universitaire de la Francophonie (AUF) offre des bourses de mobilité pour les étudiants et chercheurs francophones.

Types de bourses:
- Mobilité de Master (1-2 semestres)
- Mobilité doctorale (3-10 mois)
- Stages professionnels (1-3 mois)

Avantages:
- Allocation mensuelle selon le pays d'accueil
- Prise en charge du voyage
- Assurance maladie
- Accompagnement administratif

Pays d'accueil:
- France, Belgique, Canada, Suisse
- Maroc, Tunisie, Sénégal
- Et autres pays francophones

Conditions:
- Être inscrit dans un établissement membre de l'AUF
- Maîtrise du français
- Projet d'études/recherche clair''',
                'organization': 'Agence Universitaire de la Francophonie',
                'opportunity_type': 'scholarship',
                'source_name': 'AUF',
                'category_slug': 'bourses',
                'location': 'International (Francophonie)',
                'deadline': now + timedelta(days=60),
                'education_level': 'license',
                'skills_required': ['Français', 'Projet académique'],
                'compensation': 'Bourse variable selon destination',
                'application_link': 'https://www.auf.org/les-services-de-lauf/bourses/',
            },

            # === FORMATIONS RÉELLES ===
            {
                'external_id': 'google_digital-skills-africa',
                'title': 'Google Digital Skills for Africa',
                'description': '''Google propose une formation gratuite et certifiante en compétences numériques pour les jeunes Africains.

Modules disponibles:
- Fondamentaux du marketing numérique (40 heures)
- Créer sa présence en ligne
- Développement d'applications mobiles
- Google Cloud essentials
- Data Analytics fundamentals
- Machine Learning crash course

Avantages:
- 100% gratuit et en ligne
- À votre rythme
- Certification Google reconnue
- Accessible sur mobile

Après la formation:
- Certificat Google à ajouter sur LinkedIn
- Compétences recherchées par les employeurs
- Accès à la communauté Google Developers''',
                'organization': 'Google',
                'opportunity_type': 'training',
                'source_name': 'Google',
                'category_slug': 'formations',
                'location': 'En ligne',
                'is_remote': True,
                'deadline': now + timedelta(days=365),  # Permanent
                'education_level': 'any',
                'skills_required': [],
                'compensation': 'Gratuit + Certification',
                'application_link': 'https://grow.google/intl/africa/',
                'featured': True,
            },
            {
                'external_id': 'cf_campus-france-bourses',
                'title': 'Bourses du Gouvernement Français 2026-2027',
                'description': '''Le Gouvernement français offre plusieurs programmes de bourses pour les étudiants étrangers souhaitant étudier en France.

Programmes disponibles:
- Bourse Eiffel Excellence (Master et Doctorat)
- Bourses d'excellence Major
- Bourses de couverture sociale

Bourse Eiffel:
- Master: 1,181€/mois
- Doctorat: 1,700€/mois
- Voyage, assurance, activités culturelles inclus

Domaines prioritaires:
- Droit et sciences politiques
- Économie et gestion
- Sciences de l'ingénieur
- Sciences exactes (mathématiques, physique, chimie)

Conditions:
- Moins de 25 ans (Master) ou 30 ans (Doctorat)
- Non-français
- Pas de double nationalité française''',
                'organization': 'Campus France / Ministère de l\'Europe et des Affaires étrangères',
                'opportunity_type': 'scholarship',
                'source_name': 'Campus France',
                'category_slug': 'bourses',
                'location': 'France',
                'deadline': now + timedelta(days=120),
                'education_level': 'license',
                'skills_required': ['Français ou Anglais', 'Excellence académique'],
                'compensation': '1,181€ - 1,700€/mois',
                'application_link': 'https://www.campusfrance.org/fr/bourses-eiffel-doctorat-master',
            },
        ]
