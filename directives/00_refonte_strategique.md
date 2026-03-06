# Directive: Refonte Stratégique OpportuCI

## Objectif
Transformer OpportuCI d'un projet technique dispersé en un SaaS focalisé qui aide les jeunes ivoiriens à décrocher des opportunités (bourses, stages, emplois).

## Vision Produit

### Le Problème
Les opportunités (bourses, stages, emplois) pour les jeunes ivoiriens sont :
- Dispersées sur de multiples sources (sites, réseaux sociaux, bouche-à-oreille)
- Difficiles à filtrer selon son profil
- Sans accompagnement pour maximiser ses chances

### La Solution OpportuCI
Une plateforme qui :
1. **Agrège** les opportunités pertinentes
2. **Matche** avec le profil utilisateur via IA
3. **Accompagne** jusqu'à la réussite (préparation entretien, CV review)

### Positionnement
> "LinkedIn + Indeed + Coach carrière, adapté au contexte ivoirien et africain"

## Personas Cibles

### Persona 1: Étudiant Ambitieux
- **Nom:** Kouadio, 22 ans
- **Situation:** Étudiant en L3 Informatique à l'INP-HB
- **Objectif:** Décrocher un stage de fin d'études, idéalement à l'étranger
- **Frustration:** Passe des heures à chercher des bourses/stages sans savoir lesquels correspondent à son profil
- **Besoin:** Un flux personnalisé d'opportunités avec rappels de deadlines

### Persona 2: Jeune Diplômé
- **Nom:** Aminata, 25 ans
- **Situation:** Diplômée en Gestion, 1 an d'expérience
- **Objectif:** Premier CDI dans une grande entreprise
- **Frustration:** Postule beaucoup, peu de retours, ne sait pas pourquoi
- **Besoin:** Feedback sur ses candidatures + préparation entretiens

### Persona 3: Reconversion
- **Nom:** Ibrahim, 28 ans
- **Situation:** Travaille mais veut changer de domaine (vers Tech)
- **Objectif:** Formation/certification puis nouvel emploi
- **Frustration:** Ne sait pas par où commencer
- **Besoin:** Parcours guidé avec étapes claires

## Core User Journey

```
DÉCOUVRIR ──→ MATCHER ──→ SAUVEGARDER ──→ POSTULER ──→ PRÉPARER ──→ SUIVRE
    │            │             │              │            │           │
    ▼            ▼             ▼              ▼            ▼           ▼
  Feed       Score IA      Wishlist      Tracker     Simulations   Status
opportunités  matching    personnelle   candidatures  entretien   updates
```

## Architecture Simplifiée (Cible)

### Apps Django à GARDER (4 apps core)
1. **accounts** - Auth + Profil simplifié
2. **opportunities** - Opportunités + Matching + Tracking
3. **prep** - Simulations entretien + CV Review (fusion ai + simulations)
4. **notifications** - Alertes deadlines + Updates

### Apps à SUPPRIMER ou REPORTER
- `learning` → Phase 3 (pas core pour MVP)
- `credibility` → Phase 3 (gamification = nice-to-have)
- `analytics` → Intégrer dans admin, pas une app séparée
- `content` → Merger dans `opportunities` (scraping = source d'opportunités)

### Nouvelle Structure Backend
```
backend/
├── apps/
│   ├── accounts/        # Auth, Profil simplifié
│   ├── opportunities/   # Core: CRUD, matching, tracking, sources
│   ├── prep/           # Simulations, CV review, coaching IA
│   └── notifications/  # Alertes, rappels
├── core/               # Utils partagés
├── config/             # Settings Django
└── services/           # Services externes (Gemini, scraping)
```

## Phases de Développement

### Phase 1: MVP Core (Semaines 1-4)
**Objectif:** Loop de base fonctionnel

- [ ] Refonte modèle User (5 champs essentiels)
- [ ] Modèle Opportunity simplifié
- [ ] API endpoints CRUD opportunités
- [ ] Matching IA basique (score de compatibilité)
- [ ] Système de tracking (saved/applied/status)
- [ ] Notifications deadline
- [ ] Landing page + Auth flows

**Métrique de succès:** Un utilisateur peut s'inscrire, voir des opportunités matchées, sauvegarder, et recevoir un rappel deadline.

### Phase 2: Différenciation (Semaines 5-8)
**Objectif:** Ce qui nous rend uniques

- [ ] Simulation entretien IA
- [ ] CV Review IA
- [ ] Feedback personnalisé post-candidature
- [ ] Intégration sources d'opportunités (scraping)

**Métrique de succès:** Un utilisateur fait une simulation d'entretien et reçoit un feedback actionnable.

### Phase 3: Engagement (Semaines 9-12)
**Objectif:** Rétention et croissance

- [ ] Parcours d'apprentissage liés aux opportunités
- [ ] Système de crédibilité/gamification
- [ ] Fonctionnalités communautaires
- [ ] Analytics utilisateur

**Métrique de succès:** DAU/MAU > 30%

## Métriques Clés (North Star)

| Métrique | Description | Cible MVP |
|----------|-------------|-----------|
| **Activation** | % users qui sauvegardent 1+ opportunité | > 40% |
| **Rétention J7** | % users actifs après 7 jours | > 25% |
| **Applications** | # candidatures trackées / user / mois | > 3 |
| **Success Rate** | % users qui décrochent une opportunité | Mesurer |

## Prochaines Actions

1. `directives/01_audit_code_existant.md` - Inventaire de ce qu'on garde/jette
2. `directives/02_modeles_core.md` - Nouveaux modèles simplifiés
3. `directives/03_api_opportunities.md` - Endpoints MVP
4. `directives/04_matching_ia.md` - Algorithme de matching

## Notes & Learnings

*(Section mise à jour au fur et à mesure)*

---
*Dernière mise à jour: 2025-03-05*
*Statut: Draft - En attente validation*
