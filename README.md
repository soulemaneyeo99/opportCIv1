# OpportuCI

**La plateforme IA qui connecte les jeunes ivoiriens aux meilleures opportunités.**

OpportuCI agrège bourses, stages, emplois et formations, puis utilise l'intelligence artificielle (Gemini) pour recommander les opportunités les plus pertinentes selon le profil de chaque utilisateur.

## Quick Start (5 minutes)

### Prérequis
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (optionnel)

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/your-org/opportuci.git
cd opportuci

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
cp .env.example .env.local  # Configurer les variables
python manage.py migrate --settings=settings.development
python manage.py seed_opportunities --settings=settings.development

# 3. Frontend
cd ../frontend
npm install
cp .env.example .env.local  # Configurer NEXT_PUBLIC_API_URL

# 4. Lancer
# Terminal 1 - Backend
cd backend && python manage.py runserver --settings=settings.development

# Terminal 2 - Frontend
cd frontend && npm run dev
```

### Accès
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Django**: http://localhost:8000/admin/

## Architecture

```
opportuci/
├── backend/                 # Django 4.2 + DRF
│   ├── apps/
│   │   ├── accounts/       # Auth + Profil utilisateur
│   │   ├── opportunities/  # Opportunités + Matching
│   │   ├── prep/           # Simulations d'entretien
│   │   ├── ai/             # Service Gemini
│   │   └── notifications/  # Notifications
│   ├── services/           # Business logic
│   └── config/             # Django config
│
├── frontend/               # Next.js 14 + TypeScript
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # Composants React
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # API client
│
└── infrastructure/         # Docker, Nginx
```

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 4.2, Django REST Framework |
| Frontend | Next.js 14, React 18, TypeScript |
| Base de données | PostgreSQL 15 (SQLite en dev) |
| Cache | Redis 7 |
| IA | Google Gemini API |
| Auth | JWT (SimpleJWT) |
| Styles | Tailwind CSS |
| Async | Celery + Redis |

## Fonctionnalités

### MVP (Phase Pilote)
- [x] Inscription / Connexion (JWT)
- [x] Profil utilisateur (compétences, intérêts, éducation)
- [x] Liste des opportunités avec filtres
- [x] Détail d'une opportunité
- [x] Recommandations IA personnalisées
- [x] Dashboard utilisateur
- [x] Scraping automatique des sources

### À venir
- [ ] Notifications push
- [ ] Simulation d'entretien IA
- [ ] Application tracking
- [ ] Mobile app (React Native)

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health/` | Health check |
| `POST /api/accounts/auth/register/` | Inscription |
| `POST /api/accounts/auth/login/` | Connexion |
| `GET /api/accounts/users/me/` | Profil utilisateur |
| `PATCH /api/accounts/users/update_profile/` | Mise à jour profil |
| `GET /api/opportunities/` | Liste opportunités |
| `GET /api/opportunities/{slug}/` | Détail opportunité |
| `GET /api/opportunities/recommendations/` | Recommandations IA |

## Variables d'Environnement

### Backend (.env.local)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your-gemini-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Commandes Utiles

```bash
# Tests
cd backend && pytest

# Seed des données
python manage.py seed_opportunities

# Linting
make lint  # ou: black . && isort .

# Docker (full stack)
docker-compose up -d
docker-compose logs -f
```

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

**OpportuCI** - Fait avec ❤️ pour la jeunesse ivoirienne
