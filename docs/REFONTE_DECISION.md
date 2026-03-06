# Décisions de Refonte - OpportuCI

## État Actuel (Audit)

| Métrique | Valeur |
|----------|--------|
| Apps Django | 9 |
| Fichiers Python | 172 |
| Lignes de code | ~14,500 |
| Apps avec tests | 1/9 (accounts) |
| Modèles estimés | ~25 |

## Décisions Stratégiques

### Apps : Garder / Archiver / Supprimer

| App | Décision | Raison | Action |
|-----|----------|--------|--------|
| `accounts` | ✅ GARDER | Core - Auth & Profil | Simplifier le modèle User |
| `opportunities` | ✅ GARDER | Core - Raison d'être du produit | Enrichir avec tracking |
| `simulations` | ✅ GARDER | Différenciation IA | Renommer → `prep` |
| `notifications` | ✅ GARDER | Engagement utilisateur | Simplifier |
| `ai` | 🔄 TRANSFORMER | Utile mais mal placé | → `services/ai/` |
| `content` | 🔄 MERGER | Sources d'opportunités | → dans `opportunities` |
| `learning` | ⏸️ ARCHIVER | Phase 3 | → `_archive/` |
| `credibility` | ⏸️ ARCHIVER | Phase 3 | → `_archive/` |
| `analytics` | ❌ SUPPRIMER | Pas de valeur MVP | Admin Django suffit |

### Structure Cible

```
backend/
├── apps/
│   ├── accounts/         # Auth, User, Profile (simplifié)
│   ├── opportunities/    # Opportunity, Source, Tracking
│   ├── prep/            # InterviewSimulation, CVReview
│   ├── notifications/   # Notifications (simplifié)
│   └── _archive/        # Code Phase 2/3
│       ├── learning/
│       └── credibility/
├── services/
│   ├── ai/              # GeminiService
│   └── scraping/        # ScraperService
├── core/                # Utils, Pagination, Permissions
└── config/              # Settings Django
```

## Modèles MVP Simplifiés

### User (accounts)
```python
class User:
    email              # PK, unique
    password
    first_name
    last_name
    user_type          # student | professional | organization
    is_verified
    created_at
```

### Profile (accounts)
```python
class Profile:
    user               # OneToOne
    education_level    # secondary | bts | license | master | phd
    field_of_study
    skills             # JSONField ["python", "excel", ...]
    interests          # JSONField ["tech", "finance", ...]
    city               # Choix villes ivoiriennes
    cv                 # FileField
    linkedin_url
```

### Opportunity (opportunities)
```python
class Opportunity:
    id                 # UUID
    title
    slug
    description
    opportunity_type   # scholarship | internship | job | training
    organization
    location
    is_remote
    deadline
    requirements
    skills_required    # JSONField - pour matching
    education_level
    application_link
    source             # FK → OpportunitySource
    status             # draft | published | expired
    created_at
```

### ApplicationTracker (opportunities)
```python
class ApplicationTracker:
    user               # FK
    opportunity        # FK
    status             # discovered | saved | applying | applied | interviewing | accepted | rejected
    ai_match_score     # 0-100
    applied_at
    notes
    next_action
    next_action_date
    cv_used            # FK → document utilisé
```

### InterviewSimulation (prep)
```python
class InterviewSimulation:
    id                 # UUID
    user               # FK
    opportunity        # FK
    interview_type     # phone | video | technical | behavioral
    difficulty
    status             # scheduled | in_progress | completed
    conversation       # JSONField
    overall_score
    detailed_scores    # JSONField
    ai_feedback
    strengths          # JSONField
    improvements       # JSONField
    created_at
    completed_at
```

## Ordre d'Exécution

### Sprint 1 (Semaine 1-2) : Foundation
1. [ ] Créer `_archive/` et déplacer learning, credibility
2. [ ] Simplifier modèle User/Profile
3. [ ] Nettoyer app analytics
4. [ ] Déplacer AI service vers `services/`
5. [ ] Setup tests de base

### Sprint 2 (Semaine 3-4) : Core Features
1. [ ] Enrichir modèle Opportunity (skills_required, source)
2. [ ] Créer ApplicationTracker
3. [ ] API endpoints MVP
4. [ ] Matching IA basique
5. [ ] Notifications deadline

### Sprint 3 (Semaine 5-6) : Prep Features
1. [ ] Renommer simulations → prep
2. [ ] Affiner InterviewSimulation
3. [ ] Ajouter CVReview
4. [ ] Tests complets

---

## Validation

- [ ] **Technique** : Architecture réalisable
- [ ] **Produit** : Focus sur le core value
- [ ] **Timeline** : 6 semaines réaliste

**Approuvé par :** _______________
**Date :** _______________
