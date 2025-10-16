# OpportuCI - Makefile
# =====================
# Commandes pour faciliter le développement

.PHONY: help install migrate run test clean lint format docker-up docker-down

# Couleurs pour l'output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[0;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Affiche cette aide
	@echo "$(BLUE)OpportuCI - Commandes Disponibles$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation & Setup
install: ## Installe toutes les dépendances
	@echo "$(BLUE)📦 Installation des dépendances...$(NC)"
	pip install --upgrade pip
	pip install -r requirements/development.txt
	@echo "$(GREEN)✅ Dépendances installées$(NC)"

setup-dev: install ## Setup complet environnement de développement
	@echo "$(BLUE)🔧 Configuration de l'environnement de développement...$(NC)"
	cp .env.example .env.local
	python manage.py migrate
	python manage.py collectstatic --noinput
	@echo "$(GREEN)✅ Environnement configuré$(NC)"
	@echo "$(YELLOW)⚠️  N'oubliez pas de configurer .env.local$(NC)"

# Database
migrate: ## Lance les migrations
	@echo "$(BLUE)🗄️  Migration de la base de données...$(NC)"
	python manage.py migrate
	@echo "$(GREEN)✅ Migrations appliquées$(NC)"

makemigrations: ## Crée de nouvelles migrations
	@echo "$(BLUE)📝 Création des migrations...$(NC)"
	python manage.py makemigrations
	@echo "$(GREEN)✅ Migrations créées$(NC)"

resetdb: ## Reset la base de données (⚠️ SUPPRIME TOUTES LES DONNÉES)
	@echo "$(RED)⚠️  ATTENTION: Ceci va supprimer toutes les données!$(NC)"
	@read -p "Êtes-vous sûr? [y/N] " -n 1 -r; \
	if [[ $REPLY =~ ^[Yy]$ ]]; then \
		echo ""; \
		python manage.py flush --noinput; \
		python manage.py migrate; \
		echo "$(GREEN)✅ Base de données réinitialisée$(NC)"; \
	fi

seed: ## Remplit la DB avec des données de test
	@echo "$(BLUE)🌱 Seeding de la base de données...$(NC)"
	python manage.py seed
	@echo "$(GREEN)✅ Données de test créées$(NC)"

# Serveur
run: ## Lance le serveur de développement
	@echo "$(BLUE)🚀 Démarrage du serveur...$(NC)"
	python manage.py runserver 0.0.0.0:8000

runplus: ## Lance le serveur avec Werkzeug debugger
	@echo "$(BLUE)🚀 Démarrage du serveur (mode debug)...$(NC)"
	python manage.py runserver_plus 0.0.0.0:8000

shell: ## Ouvre le shell Django
	@echo "$(BLUE)🐚 Ouverture du shell Django...$(NC)"
	python manage.py shell_plus --ipython

# Celery
celery-worker: ## Lance Celery worker
	@echo "$(BLUE)⚙️  Démarrage Celery worker...$(NC)"
	celery -A config worker -l info

celery-beat: ## Lance Celery beat (tâches périodiques)
	@echo "$(BLUE)⏰ Démarrage Celery beat...$(NC)"
	celery -A config beat -l info

celery-flower: ## Lance Flower (monitoring Celery)
	@echo "$(BLUE)🌸 Démarrage Flower...$(NC)"
	celery -A config flower

# Tests
test: ## Lance tous les tests
	@echo "$(BLUE)🧪 Exécution des tests...$(NC)"
	pytest -v --cov=apps --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Tests terminés$(NC)"

test-fast: ## Lance les tests (sans coverage)
	@echo "$(BLUE)🧪 Tests rapides...$(NC)"
	pytest -v -x
	@echo "$(GREEN)✅ Tests terminés$(NC)"

test-specific: ## Lance tests spécifiques (usage: make test-specific path=apps/learning)
	@echo "$(BLUE)🧪 Tests sur $(path)...$(NC)"
	pytest -v $(path)

coverage: ## Affiche le rapport de couverture
	@echo "$(BLUE)📊 Rapport de couverture...$(NC)"
	coverage report
	coverage html
	@echo "$(GREEN)✅ Rapport généré dans htmlcov/index.html$(NC)"

# Code Quality
lint: ## Vérifie le code (flake8, pylint)
	@echo "$(BLUE)🔍 Vérification du code...$(NC)"
	flake8 apps config --max-line-length=120
	pylint apps --disable=all --enable=E,F
	@echo "$(GREEN)✅ Code vérifié$(NC)"

format: ## Formate le code (black, isort)
	@echo "$(BLUE)✨ Formatage du code...$(NC)"
	black apps config --line-length=120
	isort apps config
	@echo "$(GREEN)✅ Code formaté$(NC)"

type-check: ## Vérifie les types (mypy)
	@echo "$(BLUE)🔎 Vérification des types...$(NC)"
	mypy apps --ignore-missing-imports
	@echo "$(GREEN)✅ Types vérifiés$(NC)"

check-all: format lint type-check test ## Vérifie tout (format, lint, types, tests)
	@echo "$(GREEN)✅ Toutes les vérifications passées!$(NC)"

# Docker
docker-build: ## Build les images Docker
	@echo "$(BLUE)🐳 Build Docker...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Images construites$(NC)"

docker-up: ## Lance tous les services Docker
	@echo "$(BLUE)🐳 Démarrage des services Docker...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Services démarrés$(NC)"
	@echo "$(YELLOW)📍 Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)📍 Frontend: http://localhost:3000$(NC)"

docker-down: ## Arrête tous les services Docker
	@echo "$(BLUE)🐳 Arrêt des services Docker...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Services arrêtés$(NC)"

docker-logs: ## Affiche les logs Docker
	docker-compose logs -f

docker-shell: ## Shell dans le container backend
	docker-compose exec backend bash

docker-psql: ## Connexion PostgreSQL
	docker-compose exec db psql -U opportunci_user -d opportunci

docker-redis: ## Connexion Redis CLI
	docker-compose exec redis redis-cli

# Nettoyage
clean: ## Nettoie les fichiers générés
	@echo "$(BLUE)🧹 Nettoyage...$(NC)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf staticfiles/ media/test/
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

clean-all: clean ## Nettoie tout (inclut venv, node_modules)
	@echo "$(RED)⚠️  Nettoyage complet...$(NC)"
	rm -rf venv/ .venv/
	rm -rf node_modules/
	@echo "$(GREEN)✅ Nettoyage complet terminé$(NC)"

# Documentation
docs: ## Génère la documentation
	@echo "$(BLUE)📚 Génération de la documentation...$(NC)"
	cd docs && mkdocs build
	@echo "$(GREEN)✅ Documentation générée dans docs/site/$(NC)"

docs-serve: ## Serve la documentation localement
	@echo "$(BLUE)📚 Documentation servie sur http://localhost:8001$(NC)"
	cd docs && mkdocs serve -a localhost:8001

# Utilitaires
create-superuser: ## Crée un superutilisateur
	@echo "$(BLUE)👤 Création d'un superutilisateur...$(NC)"
	python manage.py createsuperuser

show-urls: ## Affiche toutes les URLs de l'application
	@echo "$(BLUE)🔗 URLs disponibles:$(NC)"
	python manage.py show_urls

check-deploy: ## Vérifie la configuration pour le déploiement
	@echo "$(BLUE)🔍 Vérification de la configuration de déploiement...$(NC)"
	python manage.py check --deploy
	@echo "$(GREEN)✅ Configuration vérifiée$(NC)"

# CI/CD
ci-test: ## Tests pour CI (utilisé dans GitHub Actions)
	pip install -r requirements/test.txt
	pytest -v --cov=apps --cov-report=xml
	coverage report

ci-lint: ## Lint pour CI
	pip install -r requirements/test.txt
	flake8 apps config --max-line-length=120 --count --show-source --statistics

# Production
collect-static: ## Collecte les fichiers statiques
	@echo "$(BLUE)📦 Collecte des fichiers statiques...$(NC)"
	python manage.py collectstatic --noinput --clear
	@echo "$(GREEN)✅ Fichiers statiques collectés$(NC)"

compress: ## Compresse les fichiers statiques
	@echo "$(BLUE)🗜️  Compression des fichiers statiques...$(NC)"
	python manage.py compress
	@echo "$(GREEN)✅ Fichiers compressés$(NC)"

deploy-check: check-deploy collect-static compress ## Prépare pour le déploiement
	@echo "$(GREEN)✅ Prêt pour le déploiement!$(NC)"

# Monitoring
logs: ## Affiche les logs de l'application
	tail -f logs/opportunci.log

logs-error: ## Affiche uniquement les erreurs
	tail -f logs/opportunci.log | grep ERROR

logs-clear: ## Vide les logs
	> logs/opportunci.log
	@echo "$(GREEN)✅ Logs vidés$(NC)"

# Base de données - Backup & Restore
backup-db: ## Backup de la base de données
	@echo "$(BLUE)💾 Backup de la base de données...$(NC)"
	python manage.py dumpdata --natural-foreign --natural-primary --indent 2 > backup_$(date +%Y%m%d_%H%M%S).json
	@echo "$(GREEN)✅ Backup créé$(NC)"

restore-db: ## Restore la base de données (usage: make restore-db file=backup.json)
	@echo "$(RED)⚠️  Restauration de la base de données...$(NC)"
	python manage.py loaddata $(file)
	@echo "$(GREEN)✅ Base de données restaurée$(NC)"

# Développement rapide
dev: ## Workflow dev complet (format, lint, test)
	@echo "$(BLUE)🚀 Workflow de développement...$(NC)"
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test-fast
	@echo "$(GREEN)✅ Workflow terminé!$(NC)"

quick-start: ## Démarrage rapide (migrate + seed + run)
	@echo "$(BLUE)⚡ Démarrage rapide...$(NC)"
	$(MAKE) migrate
	$(MAKE) seed
	$(MAKE) run

# Requirements
requirements-update: ## Met à jour requirements.txt
	@echo "$(BLUE)📦 Mise à jour des requirements...$(NC)"
	pip freeze > requirements/base.txt
	@echo "$(GREEN)✅ Requirements mis à jour$(NC)"

requirements-check: ## Vérifie les dépendances obsolètes
	@echo "$(BLUE)🔍 Vérification des dépendances...$(NC)"
	pip list --outdated
	@echo "$(GREEN)✅ Vérification terminée$(NC)"

# Git hooks
install-hooks: ## Installe les pre-commit hooks
	@echo "$(BLUE)🪝 Installation des hooks Git...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ Hooks installés$(NC)"

run-hooks: ## Exécute les hooks sur tous les fichiers
	@echo "$(BLUE)🪝 Exécution des hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✅ Hooks exécutés$(NC)"

# Version & Release
version: ## Affiche la version actuelle
	@python -c "import config; print(f'OpportuCI v{config.__version__}')"

bump-version: ## Incrémente la version (usage: make bump-version type=patch|minor|major)
	@echo "$(BLUE)📈 Incrémentation de version ($(type))...$(NC)"
	bump2version $(type)
	@echo "$(GREEN)✅ Version incrémentée$(NC)"

# Sécurité
security-check: ## Vérifie les vulnérabilités de sécurité
	@echo "$(BLUE)🔒 Vérification de sécurité...$(NC)"
	safety check
	bandit -r apps/
	@echo "$(GREEN)✅ Vérification terminée$(NC)"

# Performances
profile: ## Profile l'application
	@echo "$(BLUE)📊 Profiling de l'application...$(NC)"
	python -m cProfile -o profile.stats manage.py runserver
	@echo "$(GREEN)✅ Stats sauvegardées dans profile.stats$(NC)"

# Status
status: ## Affiche le statut du projet
	@echo "$(BLUE)📊 Statut du Projet OpportuCI$(NC)"
	@echo ""
	@echo "$(YELLOW)Git:$(NC)"
	@git status -s
	@echo ""
	@echo "$(YELLOW)Base de données:$(NC)"
	@python manage.py showmigrations | grep '\[ \]' | wc -l | xargs -I {} echo "  {} migrations en attente"
	@echo ""
	@echo "$(YELLOW)Tests:$(NC)"
	@pytest --collect-only -q 2>/dev/null | tail -1
	@echo ""
	@echo "$(YELLOW)Serveur:$(NC)"
	@ps aux | grep "manage.py runserver" | grep -v grep >/dev/null && echo "  ✅ Serveur actif" || echo "  ❌ Serveur arrêté"

# Informations
info: ## Affiche les informations du projet
	@echo "$(BLUE)ℹ️  Informations OpportuCI$(NC)"
	@echo ""
	@echo "$(YELLOW)Version Python:$(NC) $(python --version)"
	@echo "$(YELLOW)Version Django:$(NC) $(python -c 'import django; print(django.get_version())')"
	@echo "$(YELLOW)Base de données:$(NC) PostgreSQL"
	@echo "$(YELLOW)Cache:$(NC) Redis"
	@echo "$(YELLOW)Queue:$(NC) Celery"
	@echo ""
	@echo "$(YELLOW)URLs importantes:$(NC)"
	@echo "  Backend API: http://localhost:8000/api/"
	@echo "  Admin: http://localhost:8000/admin/"
	@echo "  Swagger: http://localhost:8000/api/docs/"
	@echo "  Frontend: http://localhost:3000"