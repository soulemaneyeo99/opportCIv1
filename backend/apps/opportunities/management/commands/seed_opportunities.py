"""
OpportuCI - Seed Opportunities Command
======================================
Commande Django pour peupler la base avec des opportunités réalistes.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from apps.opportunities.models import (
    Opportunity,
    OpportunitySource,
    OpportunityCategory
)


class Command(BaseCommand):
    help = 'Peuple la base de données avec des opportunités réalistes pour le MVP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime les opportunités existantes avant le seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des opportunités existantes...')
            Opportunity.objects.all().delete()

        self.stdout.write('Création des catégories...')
        categories = self._create_categories()

        self.stdout.write('Création des sources...')
        sources = self._create_sources()

        self.stdout.write('Création des opportunités...')
        count = self._create_opportunities(categories, sources)

        self.stdout.write(
            self.style.SUCCESS(f'✓ {count} opportunités créées avec succès!')
        )

    def _create_categories(self):
        """Crée les catégories de base."""
        categories_data = [
            ('Bourses', 'bourses', '🎓'),
            ('Stages', 'stages', '💼'),
            ('Emplois', 'emplois', '👔'),
            ('Formations', 'formations', '📚'),
            ('Concours', 'concours', '🏆'),
            ('Événements', 'evenements', '📅'),
        ]

        categories = {}
        for name, slug, icon in categories_data:
            cat, _ = OpportunityCategory.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'icon': icon}
            )
            categories[slug] = cat

        return categories

    def _create_sources(self):
        """Crée les sources de données."""
        sources_data = [
            {
                'name': 'OpportuCI',
                'source_type': 'manual',
                'url': 'https://opportuci.ci',
            },
            {
                'name': 'GreatYop',
                'source_type': 'website',
                'url': 'https://greatyop.com',
                'scrape_config': {
                    'scraper_id': 'greatyop',
                    'categories': ['scholarships', 'internships'],
                    'max_pages': 3,
                }
            },
            {
                'name': 'Afri-Carrières',
                'source_type': 'website',
                'url': 'https://africarrieres.com',
                'scrape_config': {
                    'scraper_id': 'africarrieres',
                    'categories': ['bourses', 'emplois', 'stages'],
                }
            },
            {
                'name': 'Agence Emploi Jeunes CI',
                'source_type': 'website',
                'url': 'https://agenceemploijeunes.ci',
            },
            {
                'name': 'MESRS Côte d\'Ivoire',
                'source_type': 'website',
                'url': 'https://enseignement.gouv.ci',
            },
        ]

        sources = {}
        for data in sources_data:
            source, _ = OpportunitySource.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            sources[data['name']] = source

        return sources

    def _create_opportunities(self, categories, sources):
        """Crée les opportunités de seed."""
        now = timezone.now()

        opportunities_data = [
            # === BOURSES ===
            {
                'title': 'Bourse d\'Excellence du Gouvernement Chinois 2026-2027',
                'description': '''Le Gouvernement de la République Populaire de Chine offre des bourses complètes aux étudiants ivoiriens pour des études de Licence, Master et Doctorat dans les universités chinoises.

La bourse couvre:
- Les frais de scolarité
- L'hébergement sur le campus
- Une allocation mensuelle (2,500-3,500 CNY selon le niveau)
- L'assurance médicale

Domaines éligibles: Sciences, Ingénierie, Médecine, Économie, Droit, Arts.

Conditions:
- Être de nationalité ivoirienne
- Avoir moins de 25 ans (Licence), 35 ans (Master), 40 ans (Doctorat)
- Être en bonne santé
- Avoir un excellent dossier académique''',
                'organization': 'Ambassade de Chine en Côte d\'Ivoire',
                'opportunity_type': 'scholarship',
                'category': 'bourses',
                'source': 'MESRS Côte d\'Ivoire',
                'location': 'Chine',
                'deadline': now + timedelta(days=45),
                'education_level': 'bac',
                'skills_required': ['Chinois (formation offerte)', 'Anglais'],
                'compensation': 'Bourse complète + allocation mensuelle',
                'application_link': 'https://www.campuschina.org',
                'featured': True,
            },
            {
                'title': 'Bourse Mastercard Foundation Scholars Program - Sciences Po',
                'description': '''Le programme Mastercard Foundation Scholars offre des bourses complètes à de jeunes Africains talentueux pour étudier à Sciences Po Paris.

La bourse inclut:
- Frais de scolarité complets
- Hébergement et repas
- Allocation mensuelle
- Billet d'avion aller-retour
- Mentorat et développement de carrière
- Soutien au projet entrepreneurial après les études

Programme: Master en Affaires Publiques, Développement International, ou Management.

Profil recherché:
- Jeune Africain engagé dans sa communauté
- Potentiel de leadership démontré
- Engagement à retourner contribuer au développement de l'Afrique''',
                'organization': 'Sciences Po Paris / Mastercard Foundation',
                'opportunity_type': 'scholarship',
                'category': 'bourses',
                'source': 'GreatYop',
                'location': 'France (Paris)',
                'deadline': now + timedelta(days=60),
                'education_level': 'license',
                'skills_required': ['Leadership', 'Anglais', 'Engagement communautaire'],
                'compensation': 'Bourse complète (70,000€/an)',
                'application_link': 'https://www.sciencespo.fr/admissions/fr/mastercard-foundation-scholars-program',
                'featured': True,
            },
            {
                'title': 'Bourse de la Francophonie - Master et Doctorat',
                'description': '''L'Organisation Internationale de la Francophonie (OIF) offre des bourses pour des études de Master et Doctorat dans l'espace francophone.

Domaines prioritaires:
- Environnement et développement durable
- Technologies de l'information
- Gouvernance et État de droit
- Économie et entrepreneuriat

Avantages:
- Prise en charge des frais de scolarité
- Allocation mensuelle
- Couverture sociale

Pays d'accueil: France, Belgique, Canada, Suisse.''',
                'organization': 'Organisation Internationale de la Francophonie',
                'opportunity_type': 'scholarship',
                'category': 'bourses',
                'source': 'GreatYop',
                'location': 'International (Francophonie)',
                'deadline': now + timedelta(days=75),
                'education_level': 'license',
                'skills_required': ['Français', 'Recherche académique'],
                'compensation': 'Bourse partielle à complète',
                'application_link': 'https://www.auf.org/les-services-de-lauf/bourses/',
            },

            # === STAGES ===
            {
                'title': 'Stage Développeur Full Stack - Orange Côte d\'Ivoire',
                'description': '''Orange Côte d'Ivoire recrute des stagiaires développeurs pour rejoindre son équipe Digital Factory.

Missions:
- Développement d'applications web et mobiles
- Intégration d'APIs REST
- Tests et documentation
- Participation aux sprints Agile

Stack technique: React, Node.js, Python, PostgreSQL, Docker.

Profil:
- Étudiant(e) en fin de cycle Licence ou Master
- Passion pour le développement logiciel
- Esprit d'équipe et curiosité technique

Durée: 6 mois (possibilité d'embauche)
Lieu: Abidjan, Plateau''',
                'organization': 'Orange Côte d\'Ivoire',
                'opportunity_type': 'internship',
                'category': 'stages',
                'source': 'OpportuCI',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=21),
                'education_level': 'license',
                'skills_required': ['React', 'Node.js', 'Python', 'Git'],
                'experience_years': 0,
                'compensation': '150,000 - 200,000 FCFA/mois',
                'application_link': 'https://orange.jobs/jobs/v3/offers?location=C%C3%B4te%20d%27Ivoire',
                'featured': True,
            },
            {
                'title': 'Stage Marketing Digital - Jumia Côte d\'Ivoire',
                'description': '''Jumia, leader du e-commerce en Afrique, recherche un(e) stagiaire Marketing Digital.

Missions:
- Gestion des campagnes publicitaires digitales
- Analyse des performances (Google Analytics, Meta Ads)
- Création de contenus pour les réseaux sociaux
- Support aux campagnes promotionnelles

Profil recherché:
- Étudiant(e) en Marketing, Communication ou équivalent
- Maîtrise des outils digitaux
- Créativité et sens de l'analyse
- Maîtrise du français et de l'anglais

Durée: 4-6 mois
Avantages: Formation continue, environnement startup''',
                'organization': 'Jumia Côte d\'Ivoire',
                'opportunity_type': 'internship',
                'category': 'stages',
                'source': 'OpportuCI',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=14),
                'education_level': 'bts',
                'skills_required': ['Marketing Digital', 'Google Analytics', 'Réseaux sociaux', 'Anglais'],
                'compensation': '100,000 FCFA/mois',
                'application_link': 'https://group.jumia.com/careers',
            },
            {
                'title': 'Stage Analyste Financier - BIAO Côte d\'Ivoire',
                'description': '''La BIAO-CI recrute un(e) stagiaire pour son département Analyse Financière.

Missions:
- Analyse des dossiers de crédit entreprises
- Études sectorielles
- Participation aux due diligences
- Reporting financier

Profil:
- Master 1 ou 2 en Finance, Comptabilité ou Économie
- Excellente maîtrise d'Excel
- Capacités analytiques et rigueur
- Connaissance du secteur bancaire appréciée

Durée: 6 mois avec possibilité de pré-embauche''',
                'organization': 'BIAO Côte d\'Ivoire',
                'opportunity_type': 'internship',
                'category': 'stages',
                'source': 'Agence Emploi Jeunes CI',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=30),
                'education_level': 'master',
                'skills_required': ['Finance', 'Excel avancé', 'Analyse financière'],
                'compensation': '180,000 FCFA/mois',
                'application_link': 'https://www.bfrgroup.com/carrieres',
            },

            # === EMPLOIS ===
            {
                'title': 'Développeur Backend Senior - Djamo',
                'description': '''Djamo, la fintech ivoirienne en pleine croissance, recrute un Développeur Backend Senior.

Missions:
- Architecture et développement des services backend
- Optimisation des performances et de la scalabilité
- Mentorat des développeurs juniors
- Participation aux décisions techniques

Stack: Python/Django, PostgreSQL, Redis, Kubernetes, AWS

Exigences:
- 4+ ans d'expérience en développement backend
- Expérience avec les systèmes distribués
- Connaissance du secteur fintech appréciée

Avantages:
- Salaire compétitif
- Stock options
- Assurance santé
- Travail flexible''',
                'organization': 'Djamo',
                'opportunity_type': 'job',
                'category': 'emplois',
                'source': 'OpportuCI',
                'location': 'Abidjan, Côte d\'Ivoire',
                'is_remote': True,
                'deadline': now + timedelta(days=45),
                'education_level': 'license',
                'skills_required': ['Python', 'Django', 'PostgreSQL', 'Kubernetes', 'AWS'],
                'experience_years': 4,
                'compensation': '2,000,000 - 3,500,000 FCFA/mois',
                'application_link': 'https://www.linkedin.com/company/djamo/jobs/',
                'featured': True,
            },
            {
                'title': 'Chargé(e) de Communication - UNICEF Côte d\'Ivoire',
                'description': '''L'UNICEF Côte d'Ivoire recrute un(e) Chargé(e) de Communication.

Responsabilités:
- Élaboration de stratégies de communication
- Production de contenus (articles, vidéos, infographies)
- Relations avec les médias
- Gestion des réseaux sociaux
- Organisation d'événements

Profil:
- Diplôme en Communication, Journalisme ou Relations Publiques
- 3 ans minimum d'expérience
- Excellentes capacités rédactionnelles
- Maîtrise du français et de l'anglais

Contrat: CDD 1 an renouvelable
Lieu: Abidjan avec déplacements''',
                'organization': 'UNICEF Côte d\'Ivoire',
                'opportunity_type': 'job',
                'category': 'emplois',
                'source': 'Afri-Carrières',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=20),
                'education_level': 'license',
                'skills_required': ['Communication', 'Rédaction', 'Réseaux sociaux', 'Anglais'],
                'experience_years': 3,
                'compensation': 'Selon grille UNICEF',
                'application_link': 'https://www.unicef.org/careers',
            },
            {
                'title': 'Comptable Senior - Nestlé Côte d\'Ivoire',
                'description': '''Nestlé Côte d'Ivoire recrute un(e) Comptable Senior.

Missions:
- Gestion de la comptabilité générale et analytique
- Préparation des états financiers
- Déclarations fiscales et sociales
- Audit interne et contrôle de gestion
- Management d'équipe (2-3 personnes)

Profil requis:
- BAC+4/5 en Comptabilité, Finance ou Audit
- 5 ans d'expérience minimum
- Maîtrise des normes IFRS
- Expérience avec SAP appréciée

Avantages: Salaire attractif, assurance, formation continue''',
                'organization': 'Nestlé Côte d\'Ivoire',
                'opportunity_type': 'job',
                'category': 'emplois',
                'source': 'Agence Emploi Jeunes CI',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=25),
                'education_level': 'master',
                'skills_required': ['Comptabilité', 'IFRS', 'SAP', 'Management'],
                'experience_years': 5,
                'compensation': '1,500,000 - 2,500,000 FCFA/mois',
                'application_link': 'https://www.nestle.com/jobs',
            },

            # === FORMATIONS ===
            {
                'title': 'Formation Gratuite - Google Digital Skills for Africa',
                'description': '''Google propose une formation gratuite en compétences numériques pour les jeunes Africains.

Programme:
- Marketing Digital (certification Google)
- Développement de carrière
- E-commerce et vente en ligne
- Data Analytics
- Cloud Computing

Format: 100% en ligne, à votre rythme
Durée: 40 heures
Certification: Certificat Google reconnu

Aucun prérequis technique nécessaire.
Accessible à tous les niveaux.''',
                'organization': 'Google',
                'opportunity_type': 'training',
                'category': 'formations',
                'source': 'GreatYop',
                'location': 'En ligne',
                'is_remote': True,
                'deadline': now + timedelta(days=365),
                'education_level': 'any',
                'skills_required': [],
                'compensation': 'Gratuit + Certification',
                'application_link': 'https://grow.google/intl/africa/digitalskills/',
            },
            {
                'title': 'Programme D-CLIC Numérique - OIF',
                'description': '''Le programme D-CLIC de l'Organisation Internationale de la Francophonie forme les jeunes aux métiers du numérique.

Modules:
- Développement web (HTML, CSS, JavaScript)
- Design graphique
- Marketing digital
- Gestion de projet numérique
- Entrepreneuriat tech

Formation de 6 mois incluant un stage en entreprise.

Cibles:
- Jeunes de 18-35 ans
- Francophones
- Motivés par le secteur numérique

Places limitées: 100 participants par pays.''',
                'organization': 'Organisation Internationale de la Francophonie',
                'opportunity_type': 'training',
                'category': 'formations',
                'source': 'GreatYop',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=35),
                'education_level': 'bac',
                'skills_required': ['Français', 'Motivation'],
                'compensation': 'Gratuit + Allocation',
                'application_link': 'https://dclic.francophonie.org/',
                'featured': True,
            },

            # === CONCOURS ===
            {
                'title': 'Prix de l\'Innovation Numérique Africaine 2026',
                'description': '''Le Prix de l'Innovation Numérique Africaine récompense les startups tech les plus prometteuses du continent.

Catégories:
- FinTech
- HealthTech
- AgriTech
- EdTech
- CleanTech

Prix:
- 1er: 50,000 USD + Accompagnement
- 2ème: 25,000 USD
- 3ème: 10,000 USD
- Prix spécial impact social: 15,000 USD

Critères:
- Startup africaine (moins de 5 ans)
- Solution technologique innovante
- Impact mesurable
- Équipe constituée''',
                'organization': 'African Innovation Foundation',
                'opportunity_type': 'competition',
                'category': 'concours',
                'source': 'Afri-Carrières',
                'location': 'Afrique',
                'deadline': now + timedelta(days=90),
                'education_level': 'any',
                'skills_required': ['Entrepreneuriat', 'Innovation', 'Tech'],
                'compensation': 'Jusqu\'à 50,000 USD',
                'application_link': 'https://africaninnovation.org/programs/innovation-prize/',
            },
            {
                'title': 'Concours d\'Entrée à l\'ENA Côte d\'Ivoire 2026',
                'description': '''L'École Nationale d'Administration de Côte d'Ivoire organise son concours d'entrée pour la promotion 2026.

Cycles:
- Cycle Supérieur (Administrateurs civils)
- Cycle Moyen (Attachés d'administration)

Conditions:
- Nationalité ivoirienne
- Âge: 21-35 ans
- Diplôme requis selon le cycle

Épreuves:
- Culture générale
- Droit constitutionnel
- Économie
- Langues (Français, Anglais)
- Entretien de motivation

Inscription: 50,000 FCFA''',
                'organization': 'École Nationale d\'Administration - Côte d\'Ivoire',
                'opportunity_type': 'competition',
                'category': 'concours',
                'source': 'MESRS Côte d\'Ivoire',
                'location': 'Abidjan, Côte d\'Ivoire',
                'deadline': now + timedelta(days=40),
                'education_level': 'license',
                'skills_required': ['Droit', 'Économie', 'Culture générale'],
                'application_link': 'https://ena.gouv.ci/concours',
            },
        ]

        count = 0
        for data in opportunities_data:
            try:
                category = categories.get(data.pop('category', None))
                source = sources.get(data.pop('source', 'OpportuCI'))

                # Vérifier si existe déjà (par titre)
                if Opportunity.objects.filter(title=data['title']).exists():
                    self.stdout.write(f"  → Existant: {data['title'][:50]}...")
                    continue

                opportunity = Opportunity.objects.create(
                    category=category,
                    source=source,
                    status='published',
                    publication_date=now,
                    **data
                )

                count += 1
                self.stdout.write(f"  ✓ {opportunity.title[:50]}...")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Erreur: {data.get('title', '?')}: {e}")
                )

        return count
