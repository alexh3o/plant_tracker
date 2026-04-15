# 🌿 Plant Tracker v2.0

Une application complète et intuitive pour gérer votre collection de plantes, suivre leur entretien et documenter leur évolution.

## ✨ Fonctionnalités

### 🗂️ Gestion de Collection
* **Fiches Détaillées** : Suivi des noms (FR/EN/Latin), rusticité, feuillage, exposition et humidité.
* **Diagnostics Santé** : Indicateurs pour la toxicité, le niveau mellifère et la comestibilité.
* **Suivi d'Achat** : Historique des lieux, dates et prix d'achat.

### 📅 Entretien & Calendriers
* **Tableau de bord 12 mois** : Visualisation rapide des périodes de :
  * 🌸 Floraison
  * ✂️ Taille
  * 🧪 Fertilisation
  * 🍓 Récolte
* **Historique** : Zone de notes libres pour suivre les rempotages et événements marquants.

### 📸 Galerie Photo
* Gestion multi-photos par plante.
* Système de "Photo Vedette" (Star) pour l'aperçu dans la liste.
* Fonction zoom pour examiner vos plantes de plus près.

---

## 🛠️ Stack Technique

- **Frontend** : [Streamlit](https://streamlit.io/)
- **Backend** : [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Base de données** : [SQLite](https://sqlite.org/)
- **Conteneurisation** : [Docker](https://www.docker.com/) & Docker Compose

---

## 🚀 Installation & Lancement

1. **Cloner le projet** :
   ```bash
   git clone [https://github.com/votre-utilisateur/plant-tracker.git](https://github.com/votre-utilisateur/plant-tracker.git)
   cd plant-tracker

 
2. **Lancer avec Docker** :
   ```bash
   docker-compose up --build

3. **Accès** :
- Interface utilisateur : http://localhost:8501
- Documentation API : http://localhost:8000/docs

## 📊 Structure du Projet

 .
 ├── backend/
 │   ├── main.py          # API FastAPI & Gestion DB
 │   └── uploads/         # Stockage persistant des images
 ├── frontend/
 │   └── app.py           # Interface Streamlit
 └── docker-compose.yml   # Orchestration des services

## 📥 Import / Export
L'application permet d'exporter l'intégralité de votre base au format CSV (compatible Excel avec encodage UTF-8) et de la réimporter facilement, garantissant la portabilité de vos données.

---

Développé avec ❤️ pour les amoureux de la nature.
