# Directive: Audit du Code Existant

## Objectif
Inventorier le code existant et décider ce qu'on garde, adapte, ou supprime.

## Critères de Décision

### On GARDE si :
- Code core pour le MVP (auth, opportunities)
- Code bien écrit et testé
- Modèles de données réutilisables

### On ADAPTE si :
- Bon concept mais trop complexe
- Besoin de simplification
- Peut être fusionné avec autre chose

### On SUPPRIME si :
- Feature Phase 2/3 (pas MVP)
- Code mort ou non utilisé
- Complexité sans valeur ajoutée

---

## Inventaire par App

### 1. `accounts` ✅ GARDER + SIMPLIFIER

**Modèles actuels:**
- `User` - Custom user avec beaucoup de champs
- `UserProfile` - Profil détaillé

**Verdict:** GARDER mais SIMPLIFIER

**Ce qu'on garde:**
- Custom User avec email comme username
- Auth JWT (SimpleJWT déjà configuré)
- Structure de base du profil

**Ce qu'on simplifie:**
- User: Retirer les champs non essentiels pour MVP
- Profile: Garder uniquement ce qui sert au matching

**Champs User MVP:**
```python
- email (required, unique)
- password
- first_name, last_name
- user_type (student/professional/organization)
- is_verified
- created_at
```

**Champs Profile MVP:**
```python
- education_level
- field_of_study
- skills (JSONField - liste simple)
- interests (JSONField - liste simple)
- city
- cv (FileField)
- linkedin_url
```

---

### 2. `opportunities` ✅ GARDER + ENRICHIR

**Modèles actuels:**
- `OpportunityCategory` - Catégories
- `Opportunity` - Opportunités
- `UserOpportunity` - Relations user/opportunity

**Verdict:** GARDER et ENRICHIR

**Ce qu'on garde:**
- Structure Opportunity complète (bien pensée)
- UserOpportunity pour tracking

**Ce qu'on ajoute:**
- `OpportunitySource` - D'où vient l'opportunité (merger content app)
- `ApplicationStatus` - États de candidature détaillés
- Champs pour le matching IA (skills_required, etc.)

**Nouveau modèle ApplicationTracking:**
```python
- user
- opportunity
- status (discovered/saved/applying/applied/interviewing/accepted/rejected)
- applied_at
- notes
- documents (CV utilisé, lettre motivation)
- ai_match_score
- next_action
- next_action_date
```

---

### 3. `ai` → TRANSFORMER en `services/`

**Code actuel:**
- `GeminiAIService` - Service complet

**Verdict:** GARDER le service, DÉPLACER vers `services/`

**Ce qu'on garde:**
- `GeminiAIService` → `services/ai/gemini.py`
- Méthodes de matching et recommandation

**Ce qu'on simplifie:**
- Retirer les méthodes non MVP (learning_path, etc.)
- Focus sur: matching, interview_simulation, cv_review

---

### 4. `simulations` → RENOMMER `prep`

**Modèles actuels:**
- `InterviewSimulation` - Bien conçu

**Verdict:** GARDER, RENOMMER app en `prep`

**Ce qu'on garde:**
- `InterviewSimulation` complet
- Structure conversation JSON

**Ce qu'on ajoute:**
- `CVReview` - Feedback IA sur CV
- `CoverLetterReview` - Feedback lettre motivation

---

### 5. `learning` ⏸️ REPORTER Phase 3

**Modèles actuels:**
- `Formation`, `Course`, `Lesson`, `Question`, `Answer`, `UserProgress`

**Verdict:** ARCHIVER, pas dans MVP

**Action:**
- Déplacer vers `backend/apps/_archive/learning/`
- Réintégrer en Phase 3

---

### 6. `credibility` ⏸️ REPORTER Phase 3

**Modèles actuels:**
- `Badge`, `Achievement`, `CredibilityPoints`, `PointsHistory`

**Verdict:** ARCHIVER, pas dans MVP

**Action:**
- Déplacer vers `backend/apps/_archive/credibility/`
- Réintégrer en Phase 3

---

### 7. `analytics` ❌ SUPPRIMER

**Code actuel:**
- Services de dashboard/reporting (vides ou basiques)

**Verdict:** SUPPRIMER

**Raison:**
- Pas de valeur pour MVP
- Analytics = Django Admin + outils externes (Mixpanel, etc.)

---

### 8. `content` → MERGER dans `opportunities`

**Modèles actuels:**
- `ContentSource` - Sources de contenu
- `ScrapedContent` - Contenu scrapé

**Verdict:** MERGER dans `opportunities`

**Action:**
- `ContentSource` → `OpportunitySource`
- Scraping tasks → `opportunities/tasks/`

---

### 9. `notifications` ✅ GARDER + SIMPLIFIER

**Modèles actuels:**
- `Notification` - Système générique

**Verdict:** GARDER

**Ce qu'on garde:**
- Modèle Notification
- Types: deadline_reminder, status_update, new_opportunity

**Ce qu'on simplifie:**
- Retirer ContentType générique (overkill pour MVP)
- Lien direct vers Opportunity

---

## Structure Cible Post-Audit

```
backend/apps/
├── accounts/           # ✅ Simplifié
├── opportunities/      # ✅ Enrichi (+ content merger)
├── prep/              # ✅ Renommé (ex-simulations)
├── notifications/     # ✅ Simplifié
└── _archive/          # ⏸️ Code Phase 2/3
    ├── learning/
    ├── credibility/
    └── analytics/
```

## Scripts d'Exécution Nécessaires

- `execution/audit_models.py` - Lister tous les modèles et leurs champs
- `execution/archive_apps.py` - Déplacer apps vers _archive
- `execution/generate_migration_plan.py` - Plan de migration DB

## Prochaines Étapes

1. Exécuter l'audit automatisé
2. Valider les décisions avec l'utilisateur
3. Procéder à la restructuration
4. Créer les nouvelles migrations

---
*Dernière mise à jour: 2025-03-05*
*Statut: En cours*
