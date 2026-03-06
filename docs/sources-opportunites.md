# Sources d'Opportunités - OpportuCI

## Sources Gouvernementales Ivoiriennes

| Source | Type | Description |
|--------|------|-------------|
| **Agence Emploi Jeunes (CI)** | Emploi, Formation | Portail officiel du gouvernement ivoirien. Offres d'emploi et formations avec filtres. |
| **Portail des bourses du MAE** | Bourses | Ministère des Affaires Étrangères - bourses de coopération internationale (Chine, Iran, etc.) |
| **MESRS (Enseignement Supérieur)** | Bourses | Appels à candidature pour bourses gouvernementales (ex: bourses Chine 2026-2027) |

## Plateformes Locales

| Source | Type | Description |
|--------|------|-------------|
| **Educarrière.ci** | Emploi, Formation, Entrepreneuriat | Première plateforme ivoirienne généraliste. Offres d'emploi, appels d'offres publics, formations. |
| **Emploi.ci** | Emploi | Grand site d'annonces d'emploi ivoirien par secteur et niveau. |
| **ANSUT/ANADER** | Formations | Centres de formation agréés, formations spécialisées, concours. |

## Plateformes Africaines & Francophones

| Source | Type | Description |
|--------|------|-------------|
| **GreatYop** | Bourses, Stages, Formations, Concours | Site francophone global avec page dédiée Côte d'Ivoire. |
| **L'Étudiant Africain** | Bourses, Conférences, Formations | Plateforme panafricaine pour étudiants et chercheurs. Appels OIF, bourses de mobilité. |
| **Afri-Carrières** | Toutes catégories | Portail panafricain: bourses, concours, appels à projets, conférences, stages, volontariat. |
| **AFRIJEUNES** | Emploi, Stage, Bénévolat, Bourses | Association ouest-africaine. Offres classiques + initiatives (incubateurs, concours d'idées). |
| **Portail Jeunesse OIF** | Bourses, Concours, Prix | Organisation internationale de la Francophonie. Ex: Prix Ibn Khaldoun-Senghor 2026. |

## Stratégie de Veille

### Méthodes de collecte
- **RSS Feeds** - Pour les sites qui en proposent
- **Newsletter** - Inscription aux alertes
- **Scraping** - Pour les sites sans API/RSS
- **API** - Si disponible

### Fréquence de mise à jour recommandée
- Sources gouvernementales: **Quotidienne**
- Plateformes emploi: **Toutes les 6h**
- Bourses internationales: **Quotidienne**
- Concours/événements: **Hebdomadaire**

### Catégories OpportuCI
- `scholarship` - Bourses d'études
- `internship` - Stages
- `job` - Emplois
- `training` - Formations
- `competition` - Concours
- `conference` - Conférences
- `grant` - Appels à projets

## URLs à Implémenter

```python
OPPORTUNITY_SOURCES = {
    # Gouvernement CI
    'agence_emploi_jeunes': 'https://agenceemploijeunes.ci/',
    'mae_bourses': 'https://diplomatie.gouv.ci/bourses/',
    'mesrs': 'https://enseignement.gouv.ci/',

    # Plateformes locales
    'educarriere': 'https://educarriere.ci/',
    'emploi_ci': 'https://emploi.ci/',

    # Plateformes africaines
    'greatyop': 'https://greatyop.com/cote-divoire/',
    'etudiant_africain': 'https://letudiantafricain.com/',
    'africarrieres': 'https://africarrieres.com/',
    'afrijeunes': 'https://afrijeunes.org/',
    'oif_jeunesse': 'https://jeunesse.francophonie.org/',
}
```
