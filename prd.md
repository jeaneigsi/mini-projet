Je vais te l’écrire comme un vrai doc que tu peux donner tel quel en PFE / à Vinci.

Tu pourras ensuite adapter 2–3 noms, mais la structure est déjà pro.

---

## 1. Contexte et vision

Exprom FM gère plusieurs bâtiments tertiaires à Casanearshore pour le compte de clients (tours de bureaux, data centers, sites multi-services).
Aujourd’hui, une grande partie de la maintenance est encore :

* réactive (on intervient après la panne)
* peu instrumentée (peu de données capteurs)
* difficile à piloter globalement (multi-sites, multi-équipements).

L’objectif du projet est de concevoir et de prototyper une plateforme de “Maintenance 4.0” multi-sites, capable de :

* collecter automatiquement des données issues de capteurs (réels ou simulés) sur des équipements critiques
* détecter des dérives ou conditions de panne
* générer des alertes et des ordres de travail
* fournir un tableau de bord clair au responsable maintenance.

Ce prototype doit être suffisamment proche d’un cas réel pour pouvoir, à terme, être connecté à de vrais capteurs / GTC / GMAO existants.

---

## 2. Objectifs du projet

### 2.1 Objectifs métier

* Réduire le recours à la maintenance purement corrective en introduisant :

  * de la maintenance préventive (basée sur heures de fonctionnement / cycles)
  * de la maintenance conditionnelle (basée sur l’état réel mesuré).
* Donner une vision consolidée de l’état des équipements sur plusieurs sites Casanearshore.
* Proposer une base technique réutilisable pour des déploiements futurs chez des clients Exprom FM.

### 2.2 Objectifs pédagogiques / PFE

* Montrer la capacité à concevoir une architecture de Maintenance 4.0 end-to-end :

  * modélisation métier (sites, assets, policies)
  * data engineering (ingestion, stockage, requêtes)
  * logique métier (règles de maintenance, génération d’alertes)
  * visualisation (tableaux de bord)
  * déploiement (Docker, VPS, outils open source).
* Se positionner comme profil pré-embauche capable de prendre un sujet industriel et de le transformer en système opérationnel.

---

## 3. Périmètre fonctionnel

### 3.1 Inclus

* Multi-sites Casanearshore (au moins 2 sites simulés).
* Trois types d’équipements critiques par site :

  * HVAC (groupe climatisation)
  * CHILLER (groupe froid / eau glacée)
  * ELEVATOR (ascenseur principal).
* Simulation de capteurs pour chaque équipement (température, courant, vibration, heures de marche, cycles…).
* Ingestion des données en continu via API.
* Stockage structuré des données dans une base relationnelle.
* Définition et exécution de règles de maintenance :

  * seuils
  * dérives sur fenêtre temporelle
  * heures de fonctionnement / cycles.
* Génération d’alertes et création automatique d’ordres de travail.
* Tableau de bord multi-sites (état global, équipements, alertes).
* Déploiement conteneurisé (Docker / docker-compose) avec outils gratuits.

### 3.2 Hors périmètre (mais à prévoir en “phase 2”)

* Connexion à des capteurs physiques réels (Modbus, BACnet, LON, etc.).
* Intégration à une GMAO d’entreprise existante (SAM FM, Carl, etc.).
* Application mobile technicien.
* Authentification SSO / AD.

---

## 4. Utilisateurs cibles et besoins

### 4.1 Responsable maintenance FM (persona principal)

* Supervise plusieurs bâtiments (multi-sites).
* Veut :

  * voir en un coup d’œil les sites “à risque”
  * prioriser les interventions
  * suivre l’évolution de la santé des équipements critiques.

### 4.2 Technicien

* Reçoit des ordres de travail.
* Veut :

  * savoir où intervenir
  * sur quel équipement
  * avec quel contexte (message d’alerte, métriques récentes).

Pour le prototype, on ne gère pas encore les sessions / profils, mais l’interface et les APIs sont pensées pour ces rôles.

---

## 5. User stories clés

US-01 – Vue globale multi-sites
En tant que responsable maintenance, je veux voir la liste des sites avec le nombre d’alertes ouvertes par criticité, afin d’identifier rapidement les sites à prioriser.

US-02 – Suivi d’un site
En tant que responsable maintenance, je veux voir pour un site donné la liste des équipements et leur état (OK / sous surveillance / en alerte), afin de décider où affecter des techniciens.

US-03 – Détail d’un équipement
En tant que technicien, je veux voir les courbes récentes des métriques (température, courant, vibration, etc.) pour un équipement, afin de comprendre la nature de la dérive avant de me déplacer.

US-04 – Alertes automatiques
En tant que responsable maintenance, je veux que des alertes soient générées automatiquement en cas de dépassement de seuil ou de dérive, afin de ne pas dépendre uniquement des remontées “humaines”.

US-05 – Ordre de travail
En tant que technicien, je veux qu’un ordre de travail soit créé automatiquement lorsque qu’une alerte importante est détectée, afin de formaliser l’intervention.

---

## 6. Spécifications fonctionnelles

### 6.1 Modèle métier

Entités principales :

* Site

  * code (ex : CAS-S1)
  * nom (ex : Tour Alpha – Casanearshore)
* Asset (équipement)

  * code (ex : CAS-S1-HVAC_1)
  * type (HVAC, CHILLER, ELEVATOR)
  * site (référence à Site)
* Telemetry (point de mesure)

  * asset
  * timestamp
  * metric (ex : temp_supply_air, power_kw, vibration_level)
  * value
* MaintenancePolicy

  * asset_type
  * metric
  * rule_type (threshold, runtime, rate_of_change)
  * threshold
  * condition (>, <, >=, <=)
  * window_minutes (optionnel)
  * description
* Alert

  * asset
  * policy
  * timestamp
  * severity (low / medium / high)
  * status (open / ack / closed)
  * message
* WorkOrder

  * alert
  * timestamp création
  * timestamp clôture
  * statut (open / in_progress / done)
  * assigned_to
  * notes

### 6.2 Règles de maintenance (exemples concrets)

HVAC – Performance clim

* R1 : si temp_supply_air > 20 °C en moyenne sur les 15 dernières minutes → alerte “Performance clim dégradée” (severity = medium).

HVAC – Vibration anormale

* R2 : si vibration_level > 7 sur les 5 dernières mesures → alerte “Risque mécanique ventilateur” (severity = high).

CHILLER – Refroidissement insuffisant

* R3 : si water_temp_out > 14 °C en moyenne sur les 10 dernières minutes → alerte “Refroidissement insuffisant” (severity = high).

CHILLER – Entretien préventif

* R4 : si run_hours > 500 depuis le dernier reset → alerte “Maintenance préventive due” (severity = low).

ELEVATOR – Surchauffe moteur

* R5 : si motor_temp > 80 °C sur 5 mesures consécutives → alerte “Surchauffe moteur ascenseur” (severity = high).

ELEVATOR – Usure portes

* R6 : si door_cycles > 100 000 → alerte “Inspection portes à planifier” (severity = medium).

### 6.3 Comportement du système

* Ingestion :

  * le simulateur envoie, toutes les 10 secondes, un payload JSON avec les métriques courantes d’un équipement.
  * l’API valide le payload, résout site_code + asset_code → IDs internes, puis enregistre les mesures.

* Évaluation des règles :

  * un job périodique (toutes les 1 à 5 minutes) parcourt les policies.
  * pour chaque policy, il interroge la table telemetry sur la fenêtre pertinente.
  * si la condition est satisfaite et qu’aucune alerte du même type n’est déjà ouverte, le système crée une alerte et un work order.

---

## 7. API et formats

### 7.1 Ingestion télémétrie

Endpoint :
POST /api/v1/telemetry

Payload :

```json
{
  "site_code": "CAS-S1",
  "asset_code": "CAS-S1-HVAC_1",
  "timestamp": "2025-12-09T10:15:23Z",
  "metrics": {
    "temp_out_air": 32.5,
    "temp_supply_air": 17.8,
    "power_kw": 12.3,
    "vibration_level": 3.1
  }
}
```

Réponse (succès) :

```json
{
  "status": "ok",
  "inserted_points": 4
}
```

### 7.2 Consultation

Exemples d’endpoints :

* GET /api/v1/sites
* GET /api/v1/sites/{site_id}/assets
* GET /api/v1/assets/{asset_id}/metrics?from=…&to=…
* GET /api/v1/alerts?status=open
* GET /api/v1/workorders?status=open

---

## 8. Architecture technique

### 8.1 Vue d’ensemble

Composants (tous sur outils open source, gratuits) :

* Simulateur capteurs

  * Python (script ou container) générant des données réalistes.

* Backend API

  * Framework : FastAPI (Python)
  * Responsabilités :

    * réception de télémétrie
    * enregistrement BDD
    * exposition d’API de consultation
    * exécution du moteur de règles (via background tasks / scheduler).

* Base de données

  * PostgreSQL (ou TimescaleDB si souhait d’optimisation séries temporelles).

* Dashboard

  * Grafana (datasource PostgreSQL) pour:

    * vues multi-sites
    * courbes temps réel / historiques
    * liste d’alertes.

* Orchestration

  * Docker et docker-compose pour local et production.

Optionnel :

* Broker MQTT (Mosquitto) si tu veux simuler un vrai flux IoT : simulateur → MQTT → petit service → API.

### 8.2 Choix technologiques

* Langage backend : Python (maîtrisé, riche écosystème data).
* API : FastAPI (typage, doc OpenAPI auto, performant).
* BDD : PostgreSQL (standard, robuste).
* Visualisation : Grafana (gratuite, adaptée aux séries temporelles).
* Conteneurisation : Docker, docker-compose (déploiement simple sur VPS).
* Monitoring minimal :

  * logs structurés backend
  * métriques basiques via Grafana (requêtes lentes, volume de données).

---

## 9. Exigences non fonctionnelles

* Télémétrie :

  * Capable de gérer plusieurs dizaines de capteurs simulés (équivalent multi-sites Casanearshore).
  * Latence d’ingestion < 2 secondes en conditions normales.

* Disponibilité :

  * Pour le PFE / démo : disponibilité suffisante pour une démonstration en continu de 1 à 2 heures.

* Observabilité :

  * Logs backend consultables
  * tableaux Grafana pour vérifier l’arrivée des données.

* Sécurité (pour le prototype) :

  * Exposition API uniquement en HTTPS si accessible depuis Internet (reverse proxy gratuit type Caddy / Traefik + Let’s Encrypt).
  * Pas de données personnelles.

---

## 10. Déploiement

### 10.1 Environnement de développement

Sur machine locale :

* Installation :

  * Docker + docker-compose
  * Python 3.10+ si tu veux aussi lancer le backend en direct.

* Services via docker-compose :

  * db (PostgreSQL)
  * api (FastAPI)
  * grafana
  * simulator (script Python containerisé)

Fichiers principaux :

* docker-compose.yml
* backend/Dockerfile
* simulator/Dockerfile
* grafana/provisioning/* (datasource + dashboards préconfigurés)

Commande :

* `docker-compose up -d` pour tout démarrer.

### 10.2 Environnement de démonstration (VPS)

Outils gratuits / open source privilégiés :

* VPS économique (ou machine fournie par l’école / Vinci)
* Docker + docker-compose
* Optionnel : nom de domaine gratuit (DuckDNS)
* Reverse proxy gratuit :

  * Caddy ou Traefik pour :

    * exposer l’API et Grafana
    * générer des certificats TLS via Let’s Encrypt.

Étapes type :

1. Préparer le serveur

   * Installer Docker, docker-compose
   * Créer un utilisateur non-root pour le déploiement.

2. Déployer la stack

   * Cloner le repo Git du projet
   * Configurer les variables d’environnement (DB, mots de passe)
   * Lancer `docker-compose up -d`

3. Sécuriser minimum

   * UFW / firewall : n’ouvrir que:

     * 80/443 (pour Grafana / API via reverse proxy)
   * Désactiver accès direct PostgreSQL depuis Internet.

4. Tester la démo

   * Vérifier que le simulateur envoie bien des données
   * Vérifier l’apparition des courbes dans Grafana
   * Forcer un scénario d’alerte (par ex : simuler surchauffe ascenseur).

---

## 11. Plan de démonstration pour le jury / Vinci

Scénario de démo en 5 minutes :

1. Contexte (30–45 sec)

   * “On se place dans le contexte Exprom FM – Casanearshore, multi-bâtiments, équipements critiques (clim, chiller, ascenseur).
     L’objectif : passer d’une maintenance réactive à une maintenance 4.0, pilotée par les données.”

2. Architecture (1 min)

   * Montrer un schéma :

     * simulateur → API FastAPI → PostgreSQL → règles → alertes / work_orders → Grafana.
   * Préciser que c’est 100 % basé sur des outils open source, conteneurisés et déployables chez un client.

3. Démo live (2–3 min)

   * Afficher Grafana :

     * vue multi-sites (CAS-S1, CAS-S2)
     * vue d’un équipement avec courbes temps réel.
   * Expliquer qu’un simulateur joue le rôle des capteurs physiques.
   * Forcer une dérive (modifier temporairement le simulateur pour augmenter la température / vibration) → voir :

     * l’apparition d’une alerte
     * la création automatique d’un ordre de travail.

4. Projection Vinci (1 min)

   * Expliquer comment :

     * remplacer le simulateur par de vrais capteurs (via passerelle IoT, BMS…)
     * connecter les work_orders à une GMAO existante
     * ajouter une couche IA (anomalie detection) pour réduire les faux positifs.

---

## 12. Livrables

* Code source :

  * backend FastAPI
  * simulateur capteurs
  * fichiers de règles / policies
  * provisioning Grafana
  * docker-compose, Dockerfiles.

* Documentation :

  * ce PRD (vision + exigences)
  * documentation technique (architecture, schémas)
  * guide de déploiement (local + VPS)
  * guide utilisateur court (comment lire les dashboards, interpréter les alertes).

* Annexes :

  * captures d’écran des dashboards
  * exemple de log d’alerte + ordre de travail.

---

Si tu veux, prochain message je peux te faire la structure exacte du dépôt Git (arborescence de dossiers + fichiers) et un docker-compose de base cohérent avec ce PRD, comme ça tu n’as plus qu’à remplir.
