import streamlit as st

TRANSLATIONS = {
    "fr": {
        "months": {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"},
        "months_short": {1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin", 7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc"},
        "menu_plants": "🍀 Plantes",
        "menu_gallery": "🖼️ Galerie",
        "menu_search": "🔍 Recherche",
        "menu_pots": "🪴 Contenants",
        "menu_agenda": "📅 Agenda",
        "menu_settings": "⚙️ Paramètres",
        "presentation": "Présentation",
        "plant_type": "Type Plante",
        "location": "Emplacement",
        "tags": "Étiquettes",
        "weblink": "Lien Web",
        "latin_name": "Nom Latin",
        "container_type": "Type de Contenant",
        "container_set": "Attribuer un pot/contenant",
        "location_zone": "Zone",
        "location_detail": "Détail lieu",
        "location_type": "Intérieur/Extérieur",
        "hardiness": "Rusticité",
        "height": "Hauteur",
        "choose_containers_file": "Choisir CSV Contenants"
    },
    "en": {
        "months": {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"},
        "months_short": {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"},
        "menu_plants": "🍀 Plants",
        "menu_gallery": "🖼️ Gallery",
        "menu_search": "🔍 Search",
        "menu_pots": "🪴 Containers",
        "menu_agenda": "📅 Agenda",
        "menu_settings": "⚙️ Settings",
        "presentation": "Presentation",
        "plant_type": "Plant Type",
        "location": "Location",
        "tags": "Tags",
        "weblink": "Weblink",
        "latin_name": "Latin Name",
        "container_type": "Container Type",
        "container_set": "Set Container",
        "location_zone": "Zone",
        "location_detail": "Location details",
        "location_type": "Inside/Outside",
        "hardiness": "Hardiness",
        "height": "Height",
        "choose_containers_file": "Choose containers CSV"
    }
}

def _(key):
    """Fonction magique pour traduire un texte selon la langue choisie"""
    lang = st.session_state.get("lang", "fr")
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)

def format_months(db_val):
    """Convertit '01, 02' de la base en texte lisible ('Jan, Fév') pour l'affichage"""
    if not db_val: 
        return ""
    lang = st.session_state.get("lang", "fr")
    nums =[int(x.strip()) for x in str(db_val).split(",") if x.strip().isdigit()]
    return ", ".join([TRANSLATIONS.get(lang, TRANSLATIONS["fr"])["months_short"][n] for n in nums])
