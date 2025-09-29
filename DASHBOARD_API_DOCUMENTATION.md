# 📊 API Dashboard ASDM - Documentation Complète

## 🎯 Vue d'ensemble

L'API Dashboard ASDM fournit une interface complète pour gérer toutes les fonctionnalités du système de subventions depuis un tableau de bord. Elle inclut des statistiques, des graphiques, et des opérations CRUD complètes.

## 🚀 Endpoints Principaux

### 📈 **Statistiques et Métriques**

#### 1. Statistiques Générales
```http
GET /dashboard/stats/
```
**Réponse :**
```json
{
  "utilisateurs": {
    "total": 150,
    "agents": 8,
    "admins": 2,
    "demandeurs": 140
  },
  "demandes": {
    "total": 89,
    "en_attente": 23,
    "en_etude": 15,
    "acceptees": 35,
    "refusees": 16,
    "derniers_30_jours": 12
  },
  "financier": {
    "montant_total_demande": 1250000.00,
    "montant_total_paye": 850000.00,
    "montant_en_cours": 400000.00
  },
  "documents": {
    "total": 245
  },
  "paiements": {
    "total": 67,
    "en_attente": 8,
    "traites": 59
  },
  "notifications": {
    "non_lues": 12
  }
}
```

#### 2. Données pour Graphiques
```http
GET /dashboard/graphs/
```
**Réponse :**
```json
{
  "evolution_demandes": [
    {"mois": "2024-01-01", "total": 15},
    {"mois": "2024-02-01", "total": 23}
  ],
  "repartition_type": [
    {"type": "formation", "total": 45, "montant_total": 450000},
    {"type": "equipement", "total": 30, "montant_total": 600000}
  ],
  "repartition_statut": [
    {"statut": "en_attente", "total": 23},
    {"statut": "accepte", "total": 35}
  ],
  "performance_agents": [
    {
      "agent_traitant__prenom": "Marie",
      "agent_traitant__nom": "Martin",
      "total_traitees": 25,
      "total_acceptees": 20,
      "total_refusees": 5
    }
  ],
  "montants_par_mois": [
    {"mois": "2024-01-01", "montant_total": 150000}
  ]
}
```

#### 3. Métriques Détaillées
```http
GET /dashboard/metrics/
```
**Réponse :**
```json
{
  "taux_acceptation": 68.5,
  "temps_moyen_traitement_jours": 12,
  "montant_max_demande": 50000.00,
  "montant_moyen_demande": 15000.00,
  "agents_les_plus_actifs": [
    {"agent_traitant": 5, "nb_demandes": 25}
  ]
}
```

## 👥 **Gestion des Utilisateurs**

### CRUD Utilisateurs
```http
GET    /dashboard/utilisateurs/           # Liste tous les utilisateurs
POST   /dashboard/utilisateurs/           # Créer un utilisateur
GET    /dashboard/utilisateurs/{id}/      # Détails d'un utilisateur
PUT    /dashboard/utilisateurs/{id}/      # Modifier un utilisateur
DELETE /dashboard/utilisateurs/{id}/      # Supprimer un utilisateur
```

### Actions Spécifiques
```http
GET /dashboard/utilisateurs/agents/       # Liste tous les agents
GET /dashboard/utilisateurs/demandeurs/   # Liste tous les demandeurs
```

**Exemple de création d'utilisateur :**
```http
POST /dashboard/utilisateurs/
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "role": "demandeur",
  "password": "motdepasse123"
}
```

## 📋 **Gestion des Demandes**

### CRUD Demandes
```http
GET    /dashboard/demandes/               # Liste toutes les demandes
POST   /dashboard/demandes/               # Créer une demande
GET    /dashboard/demandes/{id}/          # Détails d'une demande
PUT    /dashboard/demandes/{id}/          # Modifier une demande
DELETE /dashboard/demandes/{id}/          # Supprimer une demande
```

### Actions Spécifiques
```http
GET  /dashboard/demandes/en-attente/      # Demandes en attente
GET  /dashboard/demandes/en-etude/        # Demandes en cours d'étude
GET  /dashboard/demandes/acceptees/       # Demandes acceptées
GET  /dashboard/demandes/refusees/        # Demandes refusées
```

### Actions sur les Demandes
```http
POST /dashboard/demandes/{id}/assigner-agent/  # Assigner un agent
POST /dashboard/demandes/{id}/valider/         # Valider une demande
POST /dashboard/demandes/{id}/rejeter/         # Rejeter une demande
```

**Exemple d'assignation d'agent :**
```http
POST /dashboard/demandes/5/assigner-agent/
Content-Type: application/json

{
  "agent_traitant_id": 3
}
```

## 👨‍💼 **Gestion des Agents**

### CRUD Agents
```http
GET    /dashboard/agents/                 # Liste tous les agents
POST   /dashboard/agents/                 # Créer un agent
GET    /dashboard/agents/{id}/            # Détails d'un agent
PUT    /dashboard/agents/{id}/            # Modifier un agent
DELETE /dashboard/agents/{id}/            # Supprimer un agent
```

### Actions Spécifiques
```http
GET /dashboard/agents/{id}/demandes/      # Demandes d'un agent
GET /dashboard/agents/{id}/statistiques/  # Statistiques d'un agent
```

**Exemple de création d'agent :**
```http
POST /dashboard/agents/
Content-Type: application/json

{
  "utilisateur_id": 15,
  "fonction": "Agent Formation",
  "departement": "Formation",
  "droits_validation": true
}
```

## 📄 **Gestion des Documents**

### CRUD Documents
```http
GET    /dashboard/documents/              # Liste tous les documents
POST   /dashboard/documents/              # Uploader un document
GET    /dashboard/documents/{id}/         # Détails d'un document
PUT    /dashboard/documents/{id}/         # Modifier un document
DELETE /dashboard/documents/{id}/         # Supprimer un document
```

### Actions Spécifiques
```http
GET /dashboard/documents/par-type/        # Documents groupés par type
```

## 💰 **Gestion des Paiements**

### CRUD Paiements
```http
GET    /dashboard/paiements/              # Liste tous les paiements
POST   /dashboard/paiements/              # Créer un paiement
GET    /dashboard/paiements/{id}/         # Détails d'un paiement
PUT    /dashboard/paiements/{id}/         # Modifier un paiement
DELETE /dashboard/paiements/{id}/         # Supprimer un paiement
```

### Actions Spécifiques
```http
GET  /dashboard/paiements/en-attente/     # Paiements en attente
POST /dashboard/paiements/{id}/traiter/   # Traiter un paiement
```

## 🔔 **Gestion des Notifications**

### CRUD Notifications
```http
GET    /dashboard/notifications/          # Liste toutes les notifications
POST   /dashboard/notifications/          # Créer une notification
GET    /dashboard/notifications/{id}/     # Détails d'une notification
PUT    /dashboard/notifications/{id}/     # Modifier une notification
DELETE /dashboard/notifications/{id}/     # Supprimer une notification
```

### Actions Spécifiques
```http
GET  /dashboard/notifications/non-lues/   # Notifications non lues
POST /dashboard/notifications/{id}/marquer-lu/  # Marquer comme lue
```

## 🔍 **Filtrage et Recherche**

### Paramètres de Filtrage
Tous les endpoints de liste supportent les paramètres suivants :

- **Filtrage :** `?statut=en_attente&type=formation`
- **Recherche :** `?search=jean`
- **Tri :** `?ordering=-date_soumission`
- **Pagination :** `?page=2&page_size=20`

### Exemples d'Utilisation
```http
# Filtrer les demandes en attente
GET /dashboard/demandes/?statut=en_attente

# Rechercher par nom d'utilisateur
GET /dashboard/utilisateurs/?search=jean

# Trier par montant décroissant
GET /dashboard/demandes/?ordering=-montant

# Pagination
GET /dashboard/demandes/?page=2&page_size=10
```

## 🔐 **Authentification et Permissions**

### Rôles et Accès
- **👑 Admin :** Accès complet à toutes les fonctionnalités
- **👨‍💼 Agent :** Gestion des demandes assignées et paiements
- **👤 Demandeur :** Accès à ses propres données

### Authentification
```http
POST /auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "motdepasse"
}
```

## 📊 **Exemples d'Utilisation Frontend**

### Dashboard React/Vue.js
```javascript
// Récupérer les statistiques
const stats = await fetch('/dashboard/stats/').then(r => r.json());

// Récupérer les graphiques
const graphs = await fetch('/dashboard/graphs/').then(r => r.json());

// Lister les demandes en attente
const demandes = await fetch('/dashboard/demandes/en-attente/').then(r => r.json());

// Assigner un agent
await fetch('/dashboard/demandes/5/assigner-agent/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ agent_traitant_id: 3 })
});
```

## 🚀 **Déploiement et Production**

### Configuration
1. Définir les permissions appropriées
2. Configurer la pagination
3. Activer la mise en cache pour les statistiques
4. Configurer les logs d'audit

### Monitoring
- Surveiller les performances des requêtes
- Monitorer l'utilisation des endpoints
- Alertes sur les erreurs

## 📝 **Notes de Développement**

- Tous les endpoints retournent des réponses JSON
- Les erreurs suivent le format standard HTTP
- Support complet de la pagination
- Filtrage et recherche optimisés
- Requêtes optimisées avec `select_related` et `prefetch_related`

---

**🎉 L'API Dashboard ASDM est maintenant prête à être utilisée !**
