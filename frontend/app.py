import streamlit as st
import requests
import locale
import time
from datetime import datetime
import pandas as pd
import io
import math, json
import os
from PIL import Image, ExifTags
import streamlit.components.v1 as components 
from translations import _, format_months, TRANSLATIONS

##################################################
#           --- CONFIGURATION ---
##################################################
API_URL = "http://backend:8000"
IMG_URL_BASE = os.getenv("IMG_URL_BASE", "http://localhost:8000")

# --- Initialisation du Session State & Paramètres Persistants ---
if "selected_plant_id" not in st.session_state:
    st.session_state.selected_plant_id = None
if "lang" not in st.session_state:
    st.session_state.lang = "fr"

# 1. Écran de démarrage persistant
if "view" not in st.session_state:
    try:
        r = requests.get(f"{API_URL}/settings/default_view").json()
        st.session_state.view = r[0]['value'] if r else "gallery"
    except:
        st.session_state.view = "gallery"

# 2. Boutons de filtres persistants et communs
if "show_weed" not in st.session_state:
    try:
        r = requests.get(f"{API_URL}/settings/default_show_weed").json()
        st.session_state.show_weed = (r[0]['value'] == "True") if r else False
    except:
        st.session_state.show_weed = False

if "show_archived" not in st.session_state:
    try:
        r = requests.get(f"{API_URL}/settings/default_show_arch").json()
        st.session_state.show_archived = (r[0]['value'] == "True") if r else False
    except:
        st.session_state.show_archived = False

# Variables pour l'upload de photos
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "extracted_date" not in st.session_state:
    st.session_state.extracted_date = datetime.now().date()

st.set_page_config(page_title="Feuille", page_icon="assets/logo_feuille.png", layout="wide")

##################################################
#           --- CONFIGURATION ---
##################################################
API_URL = "http://backend:8000"
IMG_URL_BASE = os.getenv("IMG_URL_BASE", "http://localhost:8000")
# --- STYLE CSS ---
st.markdown("""
    <style>
    /* --- GALERIE: LIMITER LA HAUTEUR DES IMAGES --- */
    div[role="dialog"] div[data-testid="stImage"] {
        display: flex !important; justify-content: center !important; width: 100% !important; max-height: 80vh !important; 
    }
    div[role="dialog"] div[data-testid="stImage"] img {
        max-height: 80vh !important; width: auto !important; max-width: 100% !important; object-fit: contain !important; margin: 0 auto !important; display: block !important;
    }
    /* --- BARRES DE CALENDRIER CONTINUES --- */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) {
        gap: 0px !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important; margin-bottom: 15px !important; 
    }
    /* 2. Retirer l'espacement imposé par les sous-blocs internes */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) div[data-testid="stVerticalBlock"] {
        gap: 0px !important;
    }
    /* 3. Écraser les largeurs de colonnes forcées par Streamlit sur Mobile */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) > div[data-testid="stColumn"] {
        width: auto !important; min-width: 0px !important; flex: 1 1 0% !important; padding: 0px !important; display: flex !important;
    }
    /* 4. Ajustement de la 1ère colonne (Titre) pour lui donner plus de place */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) > div[data-testid="stColumn"]:first-child {
        flex: 2.5 1 0% !important; margin-right: 5px !important; align-items: center !important; justify-content: flex-start !important;
    }
    /* 5. Forcer TOUS les conteneurs internes à prendre 100% de l'espace pour écraser le fameux 'width: fit-content' */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) div[data-testid="stElementContainer"],
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) div[data-testid="stButton"] {
        width: 100% !important; max-width: 100% !important; display: flex !important; flex: 1 1 auto !important;
    }
    /* 6. Style des cases (boutons) - Force l'aspect carré sans espaces */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) button {
        border-radius: 0px !important; margin: 0px !important; padding: 0px !important; width: 100% !important; height: 38px !important; min-height: 38px !important; border: 1px solid rgba(150, 150, 150, 0.4) !important; border-right: none !important; box-shadow: none !important; display: flex !important; align-items: center !important; justify-content: center !important;
    }
    /* Ajuster le texte à l'intérieur du bouton (J, F, M...) */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) button p {
        font-weight: bold !important; margin: 0 !important; padding: 0 !important;
    }
    /* 7. Arrondis pour le premier (Janvier) et dernier (Décembre) mois */
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) > div[data-testid="stColumn"]:nth-child(2) button {
        border-top-left-radius: 6px !important; border-bottom-left-radius: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-temp_"]) > div[data-testid="stColumn"]:last-child button {
        border-top-right-radius: 6px !important; border-bottom-right-radius: 6px !important; border-right: 1px solid rgba(150, 150, 150, 0.4) !important;
    }

    /* --- COULEURS SPÉCIFIQUES --- */
    /* JAUNE - Floraison */
    div[class*="st-key-temp_flowering"] button[kind="primary"], div[class*="st-key-temp_flowering"] button[data-testid="baseButton-primary"] {
        background-color: #FFD700 !important; color: black !important; border-color: #FFD700 !important;
    }
    div[class*="st-key-temp_flowering"] button[kind="primary"] p, div[class*="st-key-temp_flowering"] button[data-testid="baseButton-primary"] p { color: black !important; }

    /* ROUGE - Récolte */
    div[class*="st-key-temp_flowering"] button[kind="primary"] p, div[class*="st-key-temp_flowering"] button[data-testid="baseButton-primary"] p { color: black !important; }
        background-color: #FF4B4B !important; color: white !important; border-color: #FF4B4B !important;
    }

    /* MARRON - Taille */
    div[class*="st-key-temp_pruning"] button[kind="primary"], div[class*="st-key-temp_pruning"] button[data-testid="baseButton-primary"] {
        background-color: #8B4513 !important; color: white !important; border-color: #8B4513 !important;
    }

    /* VERT - Engrais */
    div[class*="st-key-temp_fertilizing"] button[kind="primary"], div[class*="st-key-temp_fertilizing"] button[data-testid="baseButton-primary"] {
        background-color: #2E8B57 !important; color: white !important; border-color: #2E8B57 !important;
    }

    /* --- RESTE DU CSS ORIGINAL --- */
    .stImage img { border-radius: 10px; }
    .stForm { border: none !important; padding: 0 !important; }
    div[data-testid="stDataFrame"] table img, 
    div[data-testid="stTable"] table img,
    .st-emotion-cache-1p6f546 img { 
        object-fit: cover !important; width: 50px !important; height: 50px !important; aspect-ratio: 1 / 1 !important; border-radius: 8px !important;
    }
    [data-testid="stDataFrame"][role="gridcell"] { vertical-align: center !important; }

    /* --- VUE GALERIE : GRILLE RESPONSIVE --- */
    div[data-testid="stHorizontalBlock"]:has(.plant-card-marker) {
        display: grid !important;
        /* La magie opère ici : le nombre de colonnes s'ajuste tout seul selon la variable de taille ! */
        grid-template-columns: repeat(auto-fill, minmax(var(--gallery-card-size, 200px), 1fr)) !important;
        gap: 15px !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.plant-card-marker) > div[data-testid="stColumn"] {
        width: 100% !important; 
        min-width: 0 !important; 
        max-width: none !important;
        margin: 0 !important;
        padding: 0 !important;
        position: relative;
    }
    /* Force l'image à être parfaitement carrée */
    div[data-testid="stColumn"]:has(.plant-card-marker) div[data-testid="stImage"] img {
        aspect-ratio: 1 / 1 !important;
        object-fit: cover !important;
        border-radius: 12px !important;
        width: 100% !important;
    }
    /* Place le bouton en bas, par dessus l'image avec un centrage absolu parfait */
    div[data-testid="stColumn"]:has(.plant-card-marker) div[data-testid="stButton"] {
        position: absolute;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        z-index: 10;
        display: flex;
        justify-content: center;
    }
    /* Style du bouton transparent (verre dépoli) */
    div[data-testid="stColumn"]:has(.plant-card-marker) button {
        background-color: rgba(0, 0, 0, 0.65) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        backdrop-filter: blur(4px); 
        font-weight: bold !important;
        padding: 5px !important;
        height: auto !important;
        min-height: 40px !important;
        white-space: normal !important; 
        line-height: 1.2 !important;
        text-shadow: 1px 1px 2px black;
    }
    /* Effet au survol de la souris */
    div[data-testid="stColumn"]:has(.plant-card-marker) button:hover {
        background-color: rgba(0, 0, 0, 0.85) !important;
        border-color: white !important;
        transform: scale(1.02);
        transition: 0.2s;
    }

    </style>
    """, unsafe_allow_html=True)


##################################################
#             --- FONCTIONS API ---
##################################################
def api_get(path):
    try: return requests.get(f"{API_URL}{path}").json()
    except: return []

def api_post(path, data): return requests.post(f"{API_URL}{path}", json=data)
def api_delete(path): requests.delete(f"{API_URL}{path}")

def parse_date(date_str):
    if not date_str or date_str == "None": return None
    try: return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
    except Exception: return None

# --- NOUVELLE GALERIE INTERACTIVE ---
def prev_photo(): st.session_state.gal_idx -= 1
def next_photo(): st.session_state.gal_idx += 1

@st.dialog("📸 Galerie Photo", width="large")
def show_full_photo(photos_list, start_idx):
    # Initialisation de l'index de la galerie
    if "gal_idx" not in st.session_state:
        st.session_state.gal_idx = start_idx
        
    idx = st.session_state.gal_idx
    p = photos_list[idx]
    
    fname = p['path'].split('/')[-1] if '/' in p['path'] else p['path']
    img_url = f"{IMG_URL_BASE}/uploads/{fname}"
    
    # Affichage de l'image
    st.image(img_url, width='stretch')
    
    # Barre de navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.button("⬅️ Précédente", on_click=prev_photo, disabled=(idx == 0), width='stretch')
    with col2:
        # Formatage esthétique de la date
        d = p.get('upload_date', 'Inconnue')
        if d and '-' in d:
            try: d = datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
            except: pass
        st.markdown(f"<div style='text-align:center;'><b>{idx + 1} / {len(photos_list)}</b><br>📅 {d}</div>", unsafe_allow_html=True)
    with col3:
        st.button("Suivante ➡️", on_click=next_photo, disabled=(idx == len(photos_list) - 1), width='stretch')

    # --- INJECTION DU SCRIPT POUR LE CLAVIER ET SWIPE SUR MOBILE ---
    js = """
    <script>
    const doc = window.parent.document;
    if (!doc.galleryEventsAttached) {
        // 1. GESTION DU CLAVIER (Flèches Gauche et Droite)
        doc.addEventListener('keydown', function(e) {
            const modal = doc.querySelector('div[role="dialog"]');
            if (!modal) return;
            if (e.key === 'ArrowLeft') {
                const btns = Array.from(modal.querySelectorAll('button'));
                const prevBtn = btns.find(b => b.innerText.includes('Précédente'));
                if (prevBtn && !prevBtn.disabled) prevBtn.click();
            }
            if (e.key === 'ArrowRight') {
                const btns = Array.from(modal.querySelectorAll('button'));
                const nextBtn = btns.find(b => b.innerText.includes('Suivante'));
                if (nextBtn && !nextBtn.disabled) nextBtn.click();
            }
        });
        // 2. GESTION DU SWIPE SUR MOBILE (Tactile)
        let touchstartX = 0; let touchstartY = 0;
        doc.addEventListener('touchstart', e => {
            const modal = doc.querySelector('div[role="dialog"]');
            if (!modal) return;
            touchstartX = e.changedTouches[0].screenX;
            touchstartY = e.changedTouches[0].screenY;
        }, {passive: true});
        doc.addEventListener('touchend', e => {
            const modal = doc.querySelector('div[role="dialog"]');
            if (!modal) return;
            const touchendX = e.changedTouches[0].screenX;
            const touchendY = e.changedTouches[0].screenY;
            // On vérifie que c'est un balayage horizontal (et non vertical)
            if (Math.abs(touchendX - touchstartX) > Math.abs(touchendY - touchstartY)) {
                if (touchendX < touchstartX - 40) { // Balayage vers la gauche
                    const btns = Array.from(modal.querySelectorAll('button'));
                    const nextBtn = btns.find(b => b.innerText.includes('Suivante'));
                    if (nextBtn && !nextBtn.disabled) nextBtn.click();
                }
                if (touchendX > touchstartX + 40) { // Balayage vers la droite
                    const btns = Array.from(modal.querySelectorAll('button'));
                    const prevBtn = btns.find(b => b.innerText.includes('Précédente'));
                    if (prevBtn && !prevBtn.disabled) prevBtn.click();
                }
            }
        }, {passive: true});
        doc.galleryEventsAttached = true;
    }
    </script>
    """
    # Ce composant est invisible mais injecte la logique en arrière plan
    components.html(js, height=0, width=0)

def get_exif_date(file_object):
    """Tente de lire la date de prise de vue dans les métadonnées EXIF de la photo."""
    try:
        img = Image.open(file_object)
        if hasattr(img, '_getexif') and img._getexif() is not None:
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag in ['DateTimeOriginal', 'DateTime']:
                    date_str = str(value).split(" ")[0]
                    return datetime.strptime(date_str, "%Y:%m:%d").date()
    except Exception:
        pass
    return None

# Fenêtre de modification de paramètre
@st.dialog("✏️ Modifier le paramètre")
def edit_setting_dialog(setting_id, old_val, cat):
    new_val = st.text_input("Nouveau nom", value=old_val)
    if st.button("Sauvegarder et propager"):
        if new_val and new_val != old_val:
            res = requests.put(f"{API_URL}/settings/{setting_id}", json={
                "old_value": old_val,
                "new_value": new_val,
                "category": cat
            })
            if res.status_code == 200:
                st.success("Mise à jour réussie sur toutes les plantes !")
                st.rerun()
            else:
                st.error("Erreur lors de la mise à jour.")
        else:
            st.warning("Aucune modification ou valeur vide.")

st.logo("assets/logo_feuille.png", size="large")

##################################################
#                --- SIDEBAR ---
##################################################
with st.sidebar:
    st.title("Feuille")
    
    if st.button(_("menu_plants"), width="stretch"):
        st.session_state.view = "list"
        st.rerun()
    if st.button(_("menu_gallery"), width="stretch"):
        st.session_state.view = "gallery"
        st.rerun()
    if st.button(_("menu_search"), width="stretch"):
        st.session_state.view = "search"
        st.rerun()
    if st.button(_("menu_pots"), width="stretch"):
        st.session_state.view = "containers_list"
        st.rerun()
    if st.button(_("menu_agenda"), width="stretch"):
        st.session_state.view = "agenda"
        st.rerun()
    st.write("---")
    if st.button(_("menu_settings"), width="stretch"):
        st.session_state.view = "settings"
        st.rerun()
    lang = st.selectbox("🌐 Langue / Language", options=["fr", "en"], format_func=lambda x: "Français" if x == "fr" else "English")
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()

##################################################
#      --- VUE : LISTE DES CONTENANTS ---
##################################################
if st.session_state.view == "containers_list":
    st.title(_("menu_pots"))
    col_nav1, col_nav2 = st.columns([6, 1])
    with col_nav1:
        bulk_mode_c = st.toggle("☑️ Mode sélection multiple (Suppression)")
    with col_nav2:
        if st.button("➕ Ajouter"):
            st.session_state.selected_container = {} 
            st.session_state.view = "container_edit"
            st.rerun()

    # --- Sélecteur d'emplacement pour les contenants ---
    loc_options = ["Toutes"] + [o['value'] for o in api_get("/settings/location_type")]
    loc_options = list(dict.fromkeys(loc_options))
    loc_filter_c = st.selectbox("📍 Emplacement", options=loc_options)

    containers = api_get("/containers/")
    if isinstance(containers, list) and containers:
        df_c = pd.DataFrame(containers)
        
        # --- Filtrage de l'emplacement ---
        if loc_filter_c != "Toutes":
            df_c = df_c[df_c['location_type'] == loc_filter_c]

        if not df_c.empty:
            # Nettoyage des décimales
            num_cols_c = ['volume_liters', 'diameter_base', 'diameter_top', 'height', 'width', 'length', 'purchase_price', 'container_weight']
            for col in num_cols_c:
                if col in df_c.columns:
                    df_c[col] = pd.to_numeric(df_c[col].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- FIX: On définit l'ordre SANS détruire les colonnes cachées (comme 'id') ---
            cols_order_c = ["image_url", "container_brand", "name", "location_type", "container_type", "material", "volume_liters", "plant_count", "purchase_price"]
            existing_cols_c = [c for c in cols_order_c if c in df_c.columns]
            
            c_config = {
                "image_url": st.column_config.ImageColumn(label="Aperçu", width="None"),
                "container_brand": "Marque",
                "name": "Nom du pot",
                "location_type": "Int/Ext",
                "container_type": "Type",
                "material": "Matière",
                "volume_liters": "Volume (L)",
                "plant_count": st.column_config.NumberColumn("Nb. Plantes", format="%d"),
                "purchase_price": "Prix (€)",
                "id": None, "main_photo": None 
            }
            
            mode_c = "multi-row" if bulk_mode_c else "single-row"
            event_c = st.dataframe(
                df_c, 
                column_order=existing_cols_c, # <--- La magie opère ici !
                column_config=c_config, 
                width='stretch', 
                hide_index=True, 
                on_select="rerun", 
                selection_mode=mode_c
            )

            if event_c.selection.rows:
                if bulk_mode_c:
                    selected_indices = event_c.selection.rows
                    st.warning(f"⚠️ Vous avez sélectionné {len(selected_indices)} contenant(s).")
                    if st.button("🗑️ Supprimer définitivement la sélection", type="primary"):
                        with st.spinner("Suppression en cours..."):
                            for idx in selected_indices:
                                requests.delete(f"{API_URL}/containers/{df_c.iloc[idx]['id']}")
                        st.success("Suppression terminée !")
                        st.rerun()
                else:
                    # Sécurisation de l'index via l'ID réel de la base
                    selected_container_id = int(df_c.iloc[event_c.selection.rows[0]]['id'])
                    st.session_state.selected_container = next((c for c in containers if c['id'] == selected_container_id), {})
                    st.session_state.view = "container_edit"
                    st.rerun()
        else:
            st.info("Aucun contenant ne correspond à cet emplacement.")
    else:
        st.info("Aucun contenant enregistré. Cliquez sur 'Ajouter' pour commencer.")

##################################################
#      --- FICHES CONTENANTS ---
##################################################
elif st.session_state.view == "container_edit":
    opt_conts =[o['value'] for o in api_get("/settings/container")] or ["Pot"]
    opt_mats = [o['value'] for o in api_get("/settings/container_material")] or ["Terre cuite"]
    options_mats_with_none = ["-"] +[opt for opt in opt_mats if opt != "-"]
    opt_types = [o['value'] for o in api_get("/settings/location_type")] or ["Extérieur"]
    options_types_with_none = ["-"] + [opt for opt in opt_types if opt != "-"]
    sel = st.session_state.get('selected_container', {})
    
    # En-tête avec photo principale
    if sel.get('id'):
        c_photos = api_get(f"/containers/{sel['id']}/photos/")
    else:
        c_photos =[]
    c_main_p = next((p for p in c_photos if p.get('is_main')), None)
    
    h1, h2 = st.columns([1, 4])
    with h1:
        if c_main_p: st.image(f"{IMG_URL_BASE}/uploads/{c_main_p['path'].split('/')[-1]}", width="stretch")
    with h2: 
        st.title(f"🪴 {'Modifier' if sel.get('id') else 'Nouveau'} Contenant")

    with st.form("container_form"):
        c_name = st.text_input("Nom du contenant (Identifiant unique) *", value=sel.get('name', ""))
        
        col1, col2 = st.columns(2)
        with col1:
            c_type = st.selectbox("Type", opt_conts, index=opt_conts.index(sel.get('container_type')) if sel.get('container_type') in opt_conts else 0)
            c_mat = st.selectbox("Matière", options_mats_with_none, index=options_mats_with_none.index(sel.get('material')) if sel.get('material') in options_mats_with_none else 0)
            c_loc_type = st.selectbox("Intérieur / Extérieur", options_types_with_none, index=options_types_with_none.index(sel.get('location_type')) if sel.get('location_type') in options_types_with_none else 0)
            c_brand = st.text_input("Marque", value=sel.get('container_brand', "")) # NOUVEAU
        with col2:
            c_color = st.text_input("Couleur", value=sel.get('color', ""))
            raw_c_vol = sel.get('volume_liters')
            c_vol_val = float(raw_c_vol) if raw_c_vol is not None and str(raw_c_vol).strip() != "" else None
            c_vol = st.number_input("Volume (Litres)", value=c_vol_val)

        # --- NOUVEAU : Section Dimensions et Poids ---
        st.write("### 📏 Dimensions et Poids")
        dim1, dim2, dim3 = st.columns(3)
        with dim1:
            raw_h = sel.get('height')
            c_h = st.number_input("Hauteur (cm)", value=float(raw_h) if raw_h is not None and str(raw_h).strip() != "" else None)
            raw_db = sel.get('diameter_base')
            c_db = st.number_input("Diamètre base (cm)", value=float(raw_db) if raw_db is not None and str(raw_db).strip() != "" else None)
        with dim2:
            raw_w = sel.get('width')
            c_w = st.number_input("Largeur (cm)", value=float(raw_w) if raw_w is not None and str(raw_w).strip() != "" else None)
            raw_dt = sel.get('diameter_top')
            c_dt = st.number_input("Diamètre bouche (cm)", value=float(raw_dt) if raw_dt is not None and str(raw_dt).strip() != "" else None)
        with dim3:
            raw_l = sel.get('length')
            c_l = st.number_input("Longueur (cm)", value=float(raw_l) if raw_l is not None and str(raw_l).strip() != "" else None)
            raw_weight = sel.get('container_weight')
            c_weight = st.number_input("Poids à vide (kg)", value=float(raw_weight) if raw_weight is not None and str(raw_weight).strip() != "" else None)

        st.write("### 💰 Achat")
        ca1, ca2, ca3 = st.columns(3)
        with ca1: 
            raw_c_price = sel.get('purchase_price')
            c_price_val = float(raw_c_price) if raw_c_price is not None and str(raw_c_price).strip() != "" else None
            c_price = st.number_input("Prix d'achat (€)", value=c_price_val)
        with ca2: 
            c_loc = st.text_input("Lieu d'achat", value=sel.get('purchase_location', ""))
        with ca3:
            c_date_init = parse_date(sel.get('purchase_date'))
            c_date = st.date_input("Date d'achat", value=c_date_init, format="DD/MM/YYYY")

        submit_c = st.form_submit_button("💾 Enregistrer le contenant")

    if submit_c:
        if not c_name: st.error("Le nom est obligatoire.")
        else:
            data_c = {
                "name": c_name, "location_type": c_loc_type if c_loc_type != "-" else "",
                "container_type": c_type, "material": c_mat, "color": c_color,
                "volume_liters": c_vol, "purchase_price": c_price, "purchase_location": c_loc, 
                "purchase_date": str(c_date) if c_date else "",
                "container_brand": c_brand, "diameter_base": c_db, "diameter_top": c_dt, 
                "height": c_h, "width": c_w, "length": c_l, "container_weight": c_weight
            }
            if sel.get('id'): res = requests.put(f"{API_URL}/containers/{sel['id']}", json=data_c)
            else: res = requests.post(f"{API_URL}/containers/", json=data_c)
            if res.status_code == 200:
                st.toast("Contenant enregistré !", icon="😍")
                if not sel.get('id'): 
                    st.session_state.view = "containers_list"
                st.rerun()
            else: st.error(f"Erreur API : {res.text}")

    # --- NOUVEAU: LISTE DES PLANTES ASSOCIÉES ---
    if sel.get('id'):
        st.write("---")
        st.subheader("🪴 Plante(s) dans ce contenant")
        
        all_plants = api_get("/plants/")
        contained_plants = [p for p in all_plants if p.get('container_id') == sel['id']]
        
        if contained_plants:
            for cp in contained_plants:
                var_str = f" ({cp.get('variety')})" if cp.get('variety') else ""
                # On crée un bouton pour chaque plante qui permet de sauter directement sur sa fiche !
                if st.button(f"🌿 {cp.get('name_fr')}{var_str}", key=f"link_p_{cp['id']}"):
                    st.session_state.selected_plant_id = cp['id']
                    st.session_state.force_reload = True
                    st.session_state.view = "edit"
                    st.rerun()
        else:
            st.info("Ce contenant est actuellement vide (Aucune plante n'y est associée).")

    # --- GALERIE PHOTOS CONTENANT ---
    if sel.get('id'):
        st.write("---")
        st.subheader("📸 Galerie Photos du Contenant")

        current_container_id = sel.get('id')

        with st.expander("➕ Ajouter une photo"):
            up_file = st.file_uploader("Choisir une image", type=['jpg', 'jpeg', 'png', 'webp'], key="c_new_photo")
            
            if up_file is not None:
                file_id = f"{up_file.name}_{up_file.size}"
                if st.session_state.last_uploaded_file != file_id:
                    st.session_state.last_uploaded_file = file_id
                    exif_date = get_exif_date(up_file)
                    up_file.seek(0) 
                    if exif_date:
                        st.session_state.extracted_date = exif_date
                        st.success(f"📅 Date extraite automatiquement : **{exif_date.strftime('%d/%m/%Y')}**")
                    else:
                        st.session_state.extracted_date = datetime.now().date()
                        st.info("ℹ️ Aucune date trouvée dans l'image. La date du jour est sélectionnée.")
            else:
                st.session_state.last_uploaded_file = None
                st.session_state.extracted_date = datetime.now().date()

            photo_date = st.date_input("Date de la photo", key="c_extracted_date")
            
            if st.button("🚀 Envoyer l'image") and up_file:
                with st.spinner("Traitement et envoi..."):
                    files = {"file": (up_file.name, up_file.getvalue(), up_file.type)}
                    payload = {"date": str(photo_date)}
                    
                    res = requests.post(f"{API_URL}/containers/{current_container_id}/photos/", files=files, data=payload)
                    if res.status_code == 200:
                        st.success("Photo ajoutée avec succès !")
                        st.session_state.last_uploaded_file = None 
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de l'envoi : {res.text}")

        if isinstance(c_photos, list) and len(c_photos) > 0:
            nb_cols = 4
            cols = st.columns(nb_cols)

            for idx, p in enumerate(c_photos):
                with cols[idx % nb_cols]:
                    fname = p['path'].split('/')[-1] if '/' in p['path'] else p['path']
                    img_url = f"{IMG_URL_BASE}/uploads/{fname}"

                    st.image(img_url, width='stretch')
                    
                    photo_date = p.get('upload_date', 'Date inconnue')
                    if photo_date and '-' in photo_date:
                        try:
                            d = datetime.strptime(photo_date, "%Y-%m-%d")
                            photo_date = d.strftime("%d/%m/%Y")
                        except:
                            pass
                    st.caption(f"📅 {photo_date}")

                    b1, b2, b3 = st.columns(3)
                    with b1: 
                        if st.button("🔍", key=f"c_zoom_{p['id']}", help="Ouvrir la galerie"):
                            st.session_state.gal_idx = idx 
                            # On réutilise la fonction de la galerie des plantes !
                            show_full_photo(c_photos, idx)
                    with b2: 
                        if p.get('is_main'):
                            st.markdown("⭐ **Main**")
                        else:
                            if st.button("📍", key=f"c_main_{p['id']}", help="Définir comme photo principale"):
                                requests.put(f"{API_URL}/container_photos/{p['id']}/main?container_id={current_container_id}")
                                st.rerun()
                    with b3: 
                        if st.button("🗑️", key=f"c_del_{p['id']}", help="Supprimer cette photo"):
                            requests.delete(f"{API_URL}/container_photos/{p['id']}")
                            st.rerun()
        else:
            st.info("🪴 Aucune photo n'est encore associée à ce contenant.")

    if st.button("⬅️ Retour"):
        st.session_state.view = "containers_list"
        st.rerun()

    # --- NOUVEAU: Zone de danger pour supprimer la fiche contenant ---
    if sel.get('id'):
        st.write("---")
        with st.expander("⚠️ Zone de danger"):
            st.write("La suppression est définitive.")
            if st.button("🗑️ Supprimer définitivement ce contenant", type="secondary"):
                response = requests.delete(f"{API_URL}/containers/{sel['id']}")
                if response.status_code == 200:
                    st.success("Contenant supprimé.")
                    st.session_state.view = "containers_list"
                    st.rerun()
                else:
                    st.error("Erreur lors de la suppression.")

##################################################
#          --- VUE : SETTINGS ---
##################################################
elif st.session_state.view == "settings":
    st.title(_("menu_settings"))
    
    # Création des 4 onglets
    tab_data, tab_photos, tab_lists, tab_display = st.tabs(["💾 Import / Export CSV", "📸 Sauvegarde Photos", "🏷️ Listes Déroulantes", "👀 Affichage"])

    # ==========================================
    # ONGLET 1 : IMPORT / EXPORT (CSV)
    # ==========================================
    with tab_data:
        col_exp, col_imp = st.columns(2)
        
        with col_exp:
            st.subheader("📥 Exportation")
            st.info("Récupérez vos données sous forme de tableur Excel/CSV.")
            # Export Plantes
            if st.button("📥 Exporter les Plantes (CSV)", width='stretch'):
                data = api_get("/plants/export/")
                if data:
                    csv_body = pd.DataFrame(data).to_csv(index=False, encoding='utf-8', sep=';')
                    st.download_button("Télécharger Plantes CSV", data="sep=;\n" + csv_body, file_name=f"plantes_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", width='stretch')
                else: st.error("Aucune plante à exporter.")
                
            # Export Contenants
            if st.button("📥 Exporter les Contenants (CSV)", width='stretch'):
                data_c = api_get("/containers/export/")
                if data_c:
                    csv_body_c = pd.DataFrame(data_c).to_csv(index=False, encoding='utf-8', sep=';')
                    st.download_button("Télécharger Contenants CSV", data="sep=;\n" + csv_body_c, file_name=f"contenants_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", width='stretch')
                else: st.error("Aucun contenant à exporter.")

        with col_imp:
            st.subheader("📤 Importation")
            st.warning("Importez des fichiers CSV générés par les exports ci-contre.")
            
            # --- Import Plantes ---
            uploaded_file = st.file_uploader("Choisir CSV Plantes", type="csv")
            if uploaded_file is not None:
                try:
                    raw = uploaded_file.read()
                    # Nettoyage de l'entête spéciale Excel ---
                    if raw.startswith(b"sep=;\n"): 
                        raw = raw[6:]
                    elif raw.startswith(b"sep=;\r\n"): 
                        raw = raw[7:]
                    
                    for enc in['utf-8-sig', 'utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']:
                        try:
                            # On force le séparateur ';' pour éviter toute erreur de lecture
                            df_import = pd.read_csv(io.BytesIO(raw), sep=';', engine='python', encoding=enc)
                            break
                        except Exception: continue
                        
                    if st.button("🚀 Lancer l'importation des Plantes", width='stretch'):
                        # Gestion des symoboles décimaux virgule/point
                        def clean_record(record):
                            for k, v in record.items():
                                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                                    record[k] = None
                                elif isinstance(v, str) and k in['purchase_price', 'height', 'id_confidence', 'melliferous_score', 'toxicity_score', 'rating']:
                                    try: record[k] = float(v.replace(',', '.'))
                                    except: pass
                            return record
                            
                        import_data =[clean_record(r) for r in df_import.to_dict(orient='records')]
                        total_plants = len(import_data)
                        
                        if total_plants == 0:
                            st.warning("Le fichier est vide ou invalide.")
                        else:
                            # Barre de progression pour les plantes
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            chunk_size = 20
                            success_count = 0
                            has_error = False
                            
                            for i in range(0, total_plants, chunk_size):
                                chunk = import_data[i:i+chunk_size]
                                response = requests.post(f"{API_URL}/plants/import/", json=chunk)
                                
                                if response.status_code == 200:
                                    success_count += len(chunk)
                                else:
                                    st.error(f"Erreur lors de l'import (ligne {i}) : {response.text}")
                                    has_error = True
                                    break
                                
                                progress = min(1.0, (i + chunk_size) / total_plants)
                                progress_bar.progress(progress)
                                status_text.markdown(f"⏳ **Importation en cours : {success_count} / {total_plants} plantes...**")
                            
                            if not has_error:
                                progress_bar.progress(1.0)
                                status_text.markdown("✅ **Importation terminée !**")
                                st.balloons()
                                st.success(f"Génial ! {success_count} plantes ont été importées avec succès.")
                                time.sleep(5)
                                st.session_state.view = "list"
                                st.rerun()
                                
                except Exception as e: st.error(f"Erreur : {e}")

            st.write("---")
            
            # --- Import Contenants ---
            uploaded_file_c = st.file_uploader("Choisir CSV Contenants", type="csv")
            if uploaded_file_c is not None:
                try:
                    raw_c = uploaded_file_c.read()
                    # Nettoyage de l'entête spéciale Excel ---
                    if raw_c.startswith(b"sep=;\n"): 
                        raw_c = raw_c[6:]
                    elif raw_c.startswith(b"sep=;\r\n"): 
                        raw_c = raw_c[7:]

                    for enc in['utf-8-sig', 'utf-8', 'latin-1', 'windows-1252', 'iso-8859-1']:
                        try:
                            # On force le séparateur ';'
                            df_import_c = pd.read_csv(io.BytesIO(raw_c), sep=';', engine='python', encoding=enc)
                            break
                        except Exception: continue
                        
                    if st.button("🚀 Lancer l'importation des Contenants", width='stretch'):
                        def clean_record_c(record):
                            for k, v in record.items():
                                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                                    record[k] = None
                                elif isinstance(v, str) and k in['volume_liters', 'purchase_price', 'diameter_base', 'diameter_top', 'height', 'width', 'length', 'container_weight']:
                                    try: record[k] = float(v.replace(',', '.'))
                                    except: pass
                            return record
                            
                        import_data_c =[clean_record_c(r) for r in df_import_c.to_dict(orient='records')]
                        res_c = requests.post(f"{API_URL}/containers/import/", json=import_data_c)
                        if res_c.status_code == 200:
                            st.success(f"Importation réussie : {len(import_data_c)} contenants ajoutés !")
                            time.sleep(5)
                            st.session_state.view = "containers_list"
                            st.rerun()
                        else: st.error(f"Erreur : {res_c.text}")
                except Exception as e: st.error(f"Erreur : {e}")

    # ==========================================
    # ONGLET 2 : SAUVEGARDE DES PHOTOS (ZIP)
    # ==========================================
    with tab_photos:
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.subheader("📥 Exporter les Photos")
            st.info("Crée une archive complète avec toutes vos images originales et miniatures.")
            if st.button("📦 Préparer l'archive (ZIP)", width='stretch'):
                with st.spinner("Compression des images en cours (cela peut prendre quelques minutes)..."):
                    zip_res = requests.get(f"{API_URL}/backup/photos/")
                    if zip_res.status_code == 200:
                        st.download_button(
                            label="⬇️ Cliquez ici pour Télécharger l'archive",
                            data=zip_res.content,
                            file_name=f"photos_backup_{datetime.now().strftime('%Y%m%d')}.zip",
                            mime="application/zip",
                            width='stretch'
                        )
                    else:
                        st.error("Erreur lors de la création de l'archive.")

            st.write("---")
            st.subheader("🧹 Nettoyage du serveur")
            st.warning("Supprime les images 'orphelines' pour libérer de l'espace disque.")
            if st.button("🗑️ Nettoyer les photos orphelines", width='stretch'):
                with st.spinner("Recherche et suppression des fichiers inutiles..."):
                    res_clean = requests.delete(f"{API_URL}/backup/cleanup_orphans/")
                    if res_clean.status_code == 200:
                        deleted = res_clean.json().get("deleted_count", 0)
                        if deleted > 0:
                            st.success(f"Nettoyage terminé ! {deleted} photo(s) fantôme(s) supprimée(s).")
                            st.balloons()
                        else:
                            st.info("Votre dossier photos est déjà parfaitement propre !")
                    else:
                        st.error(f"Erreur : {res_clean.text}")

        with col_p2:
            st.subheader("📤 Restaurer les Photos")
            st.warning("Restaure les photos à partir d'un fichier .zip préalablement exporté.")
            uploaded_zip = st.file_uploader("Archive Photos (.zip)", type="zip")
            if uploaded_zip and st.button("🚀 Restaurer les photos", width='stretch'):
                with st.spinner("Décompression des images en cours..."):
                    files = {"file": (uploaded_zip.name, uploaded_zip.getvalue(), "application/zip")}
                    res_zip = requests.post(f"{API_URL}/restore/photos/", files=files)
                    if res_zip.status_code == 200:
                        st.success("✅ Toutes les photos ont été restaurées avec succès !")
                        st.balloons()
                    else:
                        st.error(f"Erreur de restauration : {res_zip.text}")

    # ==========================================
    # ONGLET 4 : AFFICHAGE LISTE & GALERIE
    # ==========================================
    with tab_display:
        st.subheader("👀 Tableau de la Liste Principale")
        st.write("Choisissez les informations à afficher par défaut dans la vue 'Ma Collection'.")
        
        AVAILABLE_COLUMNS = {
            "image_url": "📸 Aperçu (Image)",
            "display_name": "🪴 Nom de la Plante",
            "name_fr": "🏷️ Nom Commun",
            "other_names": "🏷️ Autres Noms",
            "name_sci": "🔬 "+_("latin_name"),
            "name_en": "🇬🇧 Nom Anglais",
            "variety": "🧬 Variété / Cultivar",
            "plant_type": "🌳 "+_("plant_type"),
            "tags": "🔖 "+_("tags"),
            "rating": "⭐ Note",
            "is_archived": "❌ Indisponible (Archivée)",
            "location_type": "🏠 Int/Ext",
            "location_zone": "📍 Zone",
            "location_detail": "📝 "+_("location_detail"),
            "container": "🪴 Contenant",
            "hardiness": "❄️ "+_("hardiness"),
            "height": "📏 "+_("height"),
            "flowering_months": "🌷 Floraison",
            "harvest_months": "🍎 Récolte",
            "pruning_months": "✂️ Taille",
            "fertilizing_months": "🧪 Engrais",
            "purchase_date": "📅 Date d'achat",
            "purchase_price": "💰 Prix d'achat"
        }
        
        current_cols_setting = api_get("/settings/visible_columns")
        if current_cols_setting and len(current_cols_setting) > 0:
            current_cols = current_cols_setting[0]["value"].split(",")
        else:
            current_cols = ["image_url", "display_name", "location_type", "container"]
            
        selected_cols = st.multiselect(
            "Colonnes à afficher :", 
            options=list(AVAILABLE_COLUMNS.keys()), 
            format_func=lambda x: AVAILABLE_COLUMNS.get(x, x), 
            default=[c for c in current_cols if c in AVAILABLE_COLUMNS]
        )

        st.write("---")
        st.subheader("🖼️ Grille de la Galerie")
        # Récupération de la taille souhaitée
        gal_setting = api_get("/settings/gallery_size")
        current_gal_size = gal_setting[0]["value"] if gal_setting else "Moyenne"
        
        selected_gal_size = st.selectbox(
            "Taille des vignettes (S'adapte automatiquement à l'écran)", 
            options=["Petite", "Moyenne", "Grande"], 
            index=["Petite", "Moyenne", "Grande"].index(current_gal_size)
        )

        # COMPORTEMENTS PAR DÉFAUT ---
        st.write("---")
        st.subheader("⚙️ Comportement par défaut (Persistant)")
        
        current_def_view = api_get("/settings/default_view")
        def_view_val = current_def_view[0]["value"] if current_def_view else "gallery"
        selected_def_view = st.selectbox(
            "Vue par défaut au démarrage",
            options=["list", "gallery", "search"],
            format_func=lambda x: {"list": "📋 Liste", "gallery": "🖼️ Galerie", "search": "🔍 Recherche"}.get(x, x),
            index=["list", "gallery", "search"].index(def_view_val) if def_view_val in ["list", "gallery", "search"] else 1
        )
        
        current_def_weed = api_get("/settings/default_show_weed")
        def_weed_val = (current_def_weed[0]["value"] == "True") if current_def_weed else False
        selected_def_weed = st.checkbox("Afficher les adventices par défaut", value=def_weed_val)
        
        current_def_arch = api_get("/settings/default_show_arch")
        def_arch_val = (current_def_arch[0]["value"] == "True") if current_def_arch else False
        selected_def_arch = st.checkbox("Afficher les plantes indisponibles par défaut", value=def_arch_val)

        st.write("---")
        if st.button("💾 Enregistrer les préférences d'affichage", width='stretch'):
            # 1. Sauvegarde des colonnes du tableau
            for s in current_cols_setting:
                api_delete(f"/settings/{s['id']}")
            if selected_cols:
                api_post("/settings/", {"category": "visible_columns", "value": ",".join(selected_cols)})
            
            # 2. Sauvegarde de la taille de galerie
            for s in api_get("/settings/gallery_size"):
                api_delete(f"/settings/{s['id']}")
            for s in api_get("/settings/gallery_columns"): # Nettoyage de l'ancien paramètre
                api_delete(f"/settings/{s['id']}")
            api_post("/settings/", {"category": "gallery_size", "value": selected_gal_size})

            # 3. Sauvegarde des comportements par défaut
            for cat in ["default_view", "default_show_weed", "default_show_arch"]:
                for s in api_get(f"/settings/{cat}"):
                    api_delete(f"/settings/{s['id']}")
            
            api_post("/settings/", {"category": "default_view", "value": selected_def_view})
            api_post("/settings/", {"category": "default_show_weed", "value": str(selected_def_weed)})
            api_post("/settings/", {"category": "default_show_arch", "value": str(selected_def_arch)})
            
            # Mise à jour de la session immédiate
            st.session_state.show_weed = selected_def_weed
            st.session_state.show_archived = selected_def_arch
            
            st.success("Paramètres mis à jour avec succès !")
            time.sleep(1)
            st.rerun()

    # ==========================================
    # ONGLET 3 : GESTION DES LISTES
    # ==========================================
    with tab_lists:
        st.subheader("🏷️ Paramétrage des listes déroulantes")
        cats = {"location_type": "Types (Int/Ext)", "location_zone": "Zones", "container": "Types de Contenants",
            "container_material": "Matières de Contenants", "plant_type": "Type de Plante", "tags": "Étiquettes"}
        c_key = st.selectbox("Catégorie à modifier", options=list(cats.keys()), format_func=lambda x: cats[x])
        
        with st.form("add_opt"):
            nv = st.text_input("Nouvelle valeur")
            if st.form_submit_button("Ajouter à la liste") and nv:
                api_post("/settings/", {"category": c_key, "value": nv})
                st.rerun()
                
        for o in api_get(f"/settings/{c_key}"):
            c_t, c_edit, c_del = st.columns([4, 1, 1])
            c_t.write(f"• {o['value']}")
            if c_edit.button("✏️", key=f"e_o_{o['id']}", help="Renommer"):
                edit_setting_dialog(o['id'], o['value'], c_key)
            if c_del.button("🗑️", key=f"d_o_{o['id']}", help="Supprimer"):
                api_delete(f"/settings/{o['id']}")
                st.rerun()


##################################################
#             --- VUE : GALERIE ---
##################################################
elif st.session_state.view == "gallery":
    plants = api_get("/plants/")
    
    # --- 1. PRÉPARATION DES DONNÉES ---
    for p in plants:
        var = (p.get('variety') or "").strip()
        name = f"{p.get('name_fr', '')} ({var})" if var else p.get('name_fr', '')
        if p.get('is_archived', False):
            name = f"❌ {name}"
        p['display_name'] = name

    # --- 2. BARRE D'OUTILS ET FILTRES ---
    col_nav1, col_nav2 = st.columns([2, 5])
    with col_nav1:
        if st.button("➕ Ajouter une plante", width='stretch'):
            st.session_state.view = "add"
            st.session_state.force_reload = True
            st.rerun()

    st.write("") # Petit espacement visuel
    
    # Ligne des filtres
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        loc_options = ["Toutes"] + [o['value'] for o in api_get("/settings/location_type")]
        loc_options = list(dict.fromkeys(loc_options))
        loc_filter = st.selectbox("📍 Emplacement", options=loc_options, key="gal_loc_filter")
    with col_f2:
        st.toggle("🌿 Adventices", key="show_weed")
    with col_f3:
        st.toggle("❌ Indisponibles", key="show_archived")

    st.write("---")

    # --- 3. FILTRAGE ---
    filtered_plants =[]
    for p in plants:
        # Filtre Indisponibles
        if not st.session_state.show_archived and p.get('is_archived', False): continue
        if loc_filter != "Toutes" and p.get('location_type') != loc_filter: continue
        if not st.session_state.show_weed:
            ptype = str(p.get('plant_type') or "").lower()
            ptags = str(p.get('tags') or "").lower()
            if "adventice" in ptype or "adventice" in ptags: 
                continue
                
        filtered_plants.append(p)

    # Tri alphabétique
    filtered_plants = sorted(filtered_plants, key=lambda x: x.get('display_name', '').lower())

    st.title(f"{_('menu_gallery')} ({len(filtered_plants)})")

    # --- 4. RÉGLAGES D'AFFICHAGE RESPONSIVE ---
    gal_setting = api_get("/settings/gallery_size")
    gal_size = gal_setting[0]["value"] if gal_setting else "Moyenne"
    
    # On traduit le mot en une vraie taille de pixels pour le navigateur
    size_map = {"Petite": "120px", "Moyenne": "200px", "Grande": "300px"}
    css_size = size_map.get(gal_size, "200px")
    
    # Injection invisible de la variable dans la page
    st.markdown(f"<style>:root {{ --gallery-card-size: {css_size}; }}</style>", unsafe_allow_html=True)

    # --- 5. AFFICHAGE DE LA GRILLE ---
    if filtered_plants:
        # Création d'un seul bloc contenant TOUTES les plantes
        # (C'est le CSS Grid qui s'occupe de faire les retours à la ligne proprement, sans trous !)
        cols = st.columns(len(filtered_plants))
        
        for j, p in enumerate(filtered_plants):
            with cols[j]:
                # Marqueur pour appliquer notre CSS spécifique
                st.markdown('<div class="plant-card-marker" style="display:none;"></div>', unsafe_allow_html=True)
                
                img_url = p.get('image_url')
                if not img_url: 
                    img_url = "assets/logo_feuille.png"
                    
                st.image(img_url, width='stretch')
                
                if st.button(p['display_name'], key=f"gal_btn_{p['id']}", width='stretch'):
                    st.session_state.selected_plant_id = p['id']
                    st.session_state.force_reload = True
                    st.session_state.view = "edit"
                    st.rerun()
    else:
        st.info("Aucune plante à afficher avec ces filtres. Modifiez-les ou cliquez sur 'Ajouter' pour commencer.")
    
##################################################
#             --- VUE : LISTE ---
##################################################
elif st.session_state.view == "list":
    
    # --- NOUVEAU: Titre dynamique (Placé en avance, rempli plus tard) ---
    title_placeholder = st.empty()
    
    plants = api_get("/plants/")
    
    # Récupération des noms de contenants pour la liste
    all_containers = api_get("/containers/")
    cont_map = {}
    if isinstance(all_containers, list):
        for c in all_containers:
            brand = c.get('container_brand') or ""
            name = c.get('name') or ""
            cont_map[c['id']] = f"{brand} {name}".strip()
    
    # --- 1. PRÉPARATION DES DONNÉES ---
    for p in plants:
        p['flowering_months'] = format_months(p.get('flowering_months'))
        p['harvest_months'] = format_months(p.get('harvest_months'))
        p['pruning_months'] = format_months(p.get('pruning_months'))
        p['fertilizing_months'] = format_months(p.get('fertilizing_months'))
        
        var = (p.get('variety') or "").strip()
        p['display_name'] = f"{p.get('name_fr', '')} ({var})" if var else p.get('name_fr', '')
        
        # --- NOUVEAU: Remplacement du nom du contenant ---
        c_id = p.get('container_id')
        p['container'] = cont_map.get(c_id) if c_id else p.get('container')
        
    # --- 2. DÉTECTION DES DÉSYNCHRONISATIONS ---
    grouped_plants = {}
    for p in plants:
        key = ((p.get('name_fr') or '').strip().lower(), (p.get('variety') or "").strip().lower())
        if not key[0]: continue
        if key not in grouped_plants:
            grouped_plants[key] = []
        grouped_plants[key].append(p)
        
    desync_groups = []
    for key, group in grouped_plants.items():
        if len(group) > 1:
            def get_sig(pl):
                return f"{pl.get('plant_type')}|{pl.get('hardiness')}|{pl.get('exposure')}|{pl.get('flowering_months')}"
            sig0 = get_sig(group[0])
            if any(get_sig(pl) != sig0 for pl in group[1:]):
                desync_groups.append(group[0])
                
    if desync_groups:
        st.error("⚠️ **Désynchronisation détectée !**")
        for ref in desync_groups:
            st.warning(f"👉 Plusieurs exemplaires de **{ref['display_name']}** ont des caractéristiques botaniques différentes. Ouvrez la fiche de l'exemplaire contenant les **bonnes données** et sauvegardez-la pour appliquer les infos aux autres.")
        st.write("---")

    # --- 3. BARRE D'OUTILS ET FILTRES ---
    col_nav1, col_nav2, col_nav3 = st.columns([1.5, 3, 4])
    with col_nav1:
        if st.button("➕ Ajouter une plante"):
            st.session_state.view = "add"
            st.session_state.force_reload = True
            st.rerun()
    with col_nav2:
        bulk_mode = st.toggle("☑️ Sélection multiple")
    
    st.write("") 
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        loc_options = ["Toutes"] + [o['value'] for o in api_get("/settings/location_type")]
        loc_options = list(dict.fromkeys(loc_options))
        loc_filter = st.selectbox("📍 Emplacement", options=loc_options)
    with col_f2:
        st.toggle("🌿 Adventices", key="show_weed")
    with col_f3:
        st.toggle("❌ Indisponibles", key="show_archived")
            
            
    # --- 4. FILTRAGE ET AFFICHAGE ---
    filtered_plants = []
    
    for p in plants:
        if not st.session_state.show_archived and p.get('is_archived', False): continue
        if loc_filter != "Toutes" and p.get('location_type') != loc_filter: continue
        if not st.session_state.show_weed:
            ptype = str(p.get('plant_type') or "").lower()
            ptags = str(p.get('tags') or "").lower()
            if "adventice" in ptype or "adventice" in ptags: continue
                
        filtered_plants.append(p)

    # --- MISE À JOUR DU TITRE DYNAMIQUE ---
    title_placeholder.title(f"{_('menu_plants')} ({len(filtered_plants)})")

    if filtered_plants:
        df = pd.DataFrame(filtered_plants)
        
        # Tri alphabétique (insensible à la casse) par nom d'affichage
        df = df.sort_values(by="display_name", key=lambda col: col.str.lower()).reset_index(drop=True)
        
        # Nettoyage des décimales (virgules -> points)
        num_cols_p =['purchase_price', 'height', 'id_confidence', 'melliferous_score', 'toxicity_score', 'rating']
        for col in num_cols_p:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # Récupération des colonnes choisies dans les paramètres
        current_cols_setting = api_get("/settings/visible_columns")
        if current_cols_setting and len(current_cols_setting) > 0:
            cols_order = current_cols_setting[0]["value"].split(",")
        else:
            cols_order =["image_url", "display_name", "location_type", "container"]
            
        existing_cols =[c for c in cols_order if c in df.columns]

        column_configuration = {
            "image_url": st.column_config.ImageColumn(label="📸", width=None),
            "display_name": st.column_config.TextColumn("Plante", pinned=True),
            "name_fr": st.column_config.TextColumn("Nom Commun", pinned=True),
            "name_sci": _("latin_name"),
            "name_en": "Nom Anglais",
            "variety": "Variété",
            "plant_type": _("plant_type"),
            "tags": _("tags"),
            "rating": st.column_config.NumberColumn("Note /10", format="%d ⭐"),
            "is_archived": st.column_config.CheckboxColumn("Indisponible"),
            "location_type": _("location_type"),
            "location_zone": _("location_zone"),
            "location_detail": _("location_detail"),
            "container": "Contenant",
            "hardiness": _("hardiness"),
            "height": _("height"),
            "flowering_months": "Floraison",
            "harvest_months": "Récolte",
            "pruning_months": "Taille",
            "fertilizing_months": "Engrais",
            "purchase_date": "Achat",
            "purchase_price": "Prix (€)"
        }

        mode = "multi-row" if bulk_mode else "single-row"
        
        event = st.dataframe(
            df, 
            column_order=existing_cols,
            column_config=column_configuration,
            width="stretch", 
            height="content",
            row_height=45,
            hide_index=True, 
            on_select="rerun", 
            selection_mode=mode
        )

        if event.selection.rows:
            if bulk_mode:
                selected_indices = event.selection.rows
                st.warning(f"⚠️ Vous avez sélectionné {len(selected_indices)} plante(s).")
                if st.button("🗑️ Supprimer définitivement la sélection", type="primary"):
                    with st.spinner("Suppression en cours..."):
                        for idx in selected_indices:
                            requests.delete(f"{API_URL}/plants/{df.iloc[idx]['id']}")
                    st.success("Suppression terminée !")
                    st.rerun()
            else:
                st.session_state.selected_plant_id = int(df.iloc[event.selection.rows[0]]['id'])
                st.session_state.force_reload = True
                st.session_state.view = "edit"
                st.rerun()
    else:
        st.info("Aucune plante à afficher dans cette vue. Cliquez sur 'Ajouter' pour commencer.")

##################################################
#     --- VUE : RECHERCHE MULTI-CRITÈRES ---
##################################################
elif st.session_state.view == "search":
    st.title((_("menu_search")))
    with st.container(border=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_name = st.text_input("Nom (Fr, En, Latin, Autres)")
            s_type = st.selectbox("Intérieur/Extérieur", ["Tous"] + [o['value'] for o in api_get("/settings/location_type")])
            s_ptype = st.selectbox("Type de Plante", ["Tous"] + [o['value'] for o in api_get("/settings/plant_type")])
            s_tags = st.selectbox("Étiquettes", ["Toutes"] + [o['value'] for o in api_get("/settings/tags")])
            
        with col2:
            s_cont = st.selectbox("Contenant", ["Tous"] + [o['value'] for o in api_get("/settings/container")])
            options_mois = [0] + list(range(1, 13))
            format_mois = lambda x: "Tous" if x == 0 else TRANSLATIONS[st.session_state.lang]["months_short"][x]
            s_flow = st.selectbox("🌸 Floraison en...", options_mois, format_func=format_mois)
            s_harv = st.selectbox("🍎 Récolte en...", options_mois, format_func=format_mois)
            s_fert = st.selectbox("🪣 Engrais en...", options_mois, format_func=format_mois)
            
        with col3:
            s_prun = st.selectbox("✂️ Tailler en...", options_mois, format_func=format_mois)
            s_cat = st.radio("Catégorie", ["Toutes", "Fruits", "Légumes"], horizontal=True)
            st.toggle("🌿 Adventices", key="show_weed")
            st.toggle("❌ Indisponibles", key="show_archived")

    # Construction des paramètres pour l'API
    params = {}
    if s_name: params["name"] = s_name
    if s_type != "Tous": params["location_type"] = s_type
    if s_ptype != "Tous": params["plant_type"] = s_ptype
    if s_tags != "Toutes": params["tags"] = s_tags
    if s_cont != "Tous": params["container"] = s_cont
    # On force le formatage à deux chiffres "01", "12"
    if s_flow != 0: params["flowering_month"] = f"{s_flow:02d}"
    if s_harv != 0: params["harvest_month"] = f"{s_harv:02d}"
    if s_fert != 0: params["fertilizing_month"] = f"{s_fert:02d}"
    if s_prun != 0: params["pruning_month"] = f"{s_prun:02d}"
    if s_cat == "Fruits": params["is_fruit"] = True
    if s_cat == "Légumes": params["is_vegetable"] = True

# Appel API
    search_results = requests.get(f"{API_URL}/plants/search/", params=params).json()
    
    filtered_results = []
    for r in search_results:
        if not st.session_state.show_archived and r.get('is_archived', False): continue
        if not st.session_state.show_weed:
            ptype = str(r.get('plant_type') or "").lower()
            ptags = str(r.get('tags') or "").lower()
            if "adventice" in ptype or "adventice" in ptags: continue
        filtered_results.append(r)

    st.write(f"### 📋 Résultats ({len(filtered_results)})")
    
    if filtered_results:
        # --- NOUVEAU: Récupération des noms de contenants complets ---
        all_containers = api_get("/containers/")
        cont_map = {}
        if isinstance(all_containers, list):
            for c in all_containers:
                brand = c.get('container_brand') or ""
                name = c.get('name') or ""
                cont_map[c['id']] = f"{brand} {name}".strip()
        
        display_df = []
        for r in filtered_results:
            
            c_id = r.get('container_id')
            c_name = cont_map.get(c_id) if c_id else r.get('container')

            display_df.append({
                "Nom": r['name_fr'],
                "Latin": r['name_sci'],
                "Type": r['location_type'],
                "Lieu": r['location_detail'],
                "Contenant": c_name, # <-- Le nom complet ou générique
                "Floraison": format_months(r['flowering_months']),
                "Récolte": format_months(r['harvest_months']),
                "Engrais": format_months(r['fertilizing_months']),
                "Taille": format_months(r['pruning_months'])
            })
            

        event = st.dataframe(
            display_df, 
            width='stretch',
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row",
            column_config={"name_fr": st.column_config.TextColumn("Nom de la plante", width="large")}
        )
        
        if event.selection.rows:
            # IMPORTANT: On transmet l'ID et on force le rechargement
            st.session_state.selected_plant_id = filtered_results[event.selection.rows[0]]['id']
            st.session_state.force_reload = True
            st.session_state.view = "edit"
            st.rerun()
    else:
        st.info("Aucune plante ne correspond à ces critères. Vérifiez la cohérence des filtres.")

    if st.button("➕ Ajouter une plante"):
        st.session_state.view = "add"
        st.session_state.force_reload = True
        st.rerun()

################################################
##                    AGENDA
##################################################

elif st.session_state.view == "agenda":
    st.title((_("menu_agenda")))

    # --- LOGIQUE DE NAVIGATION ---
    # On initialise l'index du mois dans le session_state s'il n'existe pas
    if 'agenda_month_idx' not in st.session_state:
        st.session_state.agenda_month_idx = datetime.now().month - 1

    # Barre de navigation
    col_prev, col_month, col_next = st.columns([1, 3, 1])

    with col_prev:
        if st.button("⬅️ Précédent"):
            st.session_state.agenda_month_idx = (st.session_state.agenda_month_idx - 1) % 12
            st.rerun()

    with col_month:
        # Index de 1 à 12
        mois_actuel_idx = st.session_state.agenda_month_idx + 1
        mois_actuel_nom = TRANSLATIONS[st.session_state.lang]["months"][mois_actuel_idx]
        st.markdown(f"<h2 style='text-align: center;'>{mois_actuel_nom}</h2>", unsafe_allow_html=True)

    with col_next:
        if st.button("Suivant ➡️"):
            st.session_state.agenda_month_idx = (st.session_state.agenda_month_idx + 1) % 12
            st.rerun()

    st.write("---")

    # --- RÉCUPÉRATION ET AFFICHAGE ---
    mois_recherche_str = f"{mois_actuel_idx:02d}" # Envoie "01", "02"...
    plantes_du_mois = api_get(f"/plants/agenda/{mois_recherche_str}")

    if not plantes_du_mois:
        st.info(f"Aucune action spécifique n'est paramétrée pour le mois de {mois_actuel_nom}.")
    else:
        actions_config = [
            ("Taille", "pruning_months", "✂️"),
            ("Engrais", "fertilizing_months", "🧪"),
            ("Récolte", "harvest_months", "🧺"),
            ("Floraison", "flowering_months", "🌷")
        ]

        for action, col_base, emoji in actions_config:
            # On filtre les plantes qui concernent cette action précise
            concernes = [p for p in plantes_du_mois if mois_recherche_str in (p.get(col_base) or "")]

            if concernes:
                st.write(f"### {emoji} {action}")
                for p in concernes:
                    
                    # --- NOUVEAU : NOM D'AFFICHAGE & DISCRIMINATION DES CLONES ---
                    base_name = p.get('name_fr', '')
                    var = (p.get('variety') or "").strip()
                    disp_name = f"{base_name} ({var})" if var else base_name
                    
                    # Si c'est Taille ou Engrais, on vérifie s'il y a des doublons dans CETTE liste d'action
                    if action in ["Taille", "Engrais"]:
                        clones = [c for c in concernes if c.get('name_fr') == base_name and (c.get('variety') or "").strip() == var and c['id'] != p['id']]
                        
                        if clones:
                            # Fonction locale pour extraire le lieu le plus précis possible
                            def get_loc(pl):
                                if pl.get('location_detail') and pl.get('location_detail') != "-": return pl.get('location_detail')
                                if pl.get('location_zone') and pl.get('location_zone') != "-": return pl.get('location_zone')
                                if pl.get('location_type') and pl.get('location_type') != "-": return pl.get('location_type')
                                return ""
                            
                            my_loc = get_loc(p)
                            # On vérifie si un des clones possède exactement la même localisation que nous
                            needs_container = any(get_loc(c) == my_loc for c in clones)
                            
                            extra = []
                            if my_loc: extra.append(my_loc)
                            
                            # Si la localisation ne suffit pas, on ajoute le pot !
                            if needs_container and p.get('container') and p.get('container') != "-":
                                extra.append(p.get('container'))
                                
                            if extra:
                                disp_name += f" 📍 {' - '.join(extra)}"

                    # --- LOGIQUE DE VALIDATION ---
                    deja_fait = action.lower() in p.get('done_actions', [])

                    if action == "Récolte" or action == "Floraison":
                        titre = disp_name
                    else:
                        titre = f"{disp_name} ✅" if deja_fait else disp_name

                    with st.expander(f"**{titre}**"):
                        
                        # VUE RÉCOLTE / FLORAISON
                        if action == "Récolte":
                            st.write(f"**Mois de récolte :** {format_months(p.get(col_base))}")
                        elif action == "Floraison":
                            st.write(f"**Mois de floraison :** {format_months(p.get(col_base))}")
                            
                        # VUE TAILLE / ENGRAIS
                        else:
                            if deja_fait: 
                                st.success(f"Action '{action}' terminée pour {mois_actuel_nom} !")
                            else:
                                st.write(f"**Période programmée :** {format_months(p.get(col_base))}")
                                if st.button(f"✅ Marquer comme fait", key=f"log_{action}_{p['id']}"):
                                    api_post("/logs/", {"plant_id": p['id'], "action": action.lower(), "date": datetime.now().strftime("%Y-%m-%d")})
                                    st.rerun()
                                    
                            # Affichage additionnel des Dates et Notes d'entretien
                            if action == "Taille":
                                d_last = p.get('date_last_taille')
                                if d_last:
                                    try: d_last = datetime.strptime(d_last.split('T')[0].split(' ')[0], "%Y-%m-%d").strftime("%d/%m/%Y")
                                    except: pass
                                    st.write(f"⏱️ *Dernière taille le : {d_last}*")
                                if p.get('pruning_comment'):
                                    st.info(f"📝 **Notes :** {p.get('pruning_comment')}")
                                    
                            elif action == "Engrais":
                                d_last = p.get('date_last_fertilisation')
                                if d_last:
                                    try: d_last = datetime.strptime(d_last.split('T')[0].split(' ')[0], "%Y-%m-%d").strftime("%d/%m/%Y")
                                    except: pass
                                    st.write(f"⏱️ *Dernière fertilisation le : {d_last}*")
                                if p.get('fertilizing_comment'):
                                    st.info(f"📝 **Notes :** {p.get('fertilizing_comment')}")

                        # Bouton d'ouverture de fiche présent dans tous les cas
                        if st.button(f"Ouvrir la fiche", key=f"btn_{action}_{p['id']}"):
                            st.session_state.selected_plant_id = p['id']
                            st.session_state.force_reload = True
                            st.session_state.view = "edit"
                            st.rerun()


################################################
##              Fiche Plante
##################################################
# --- VUE : FICHE (AJOUT / EDIT) ---
elif st.session_state.view in ["add", "edit"]:
    mode_edit = st.session_state.view == "edit"
    
    if mode_edit:
        # On récupère l'ID depuis le state
        plant_id = st.session_state.get('selected_plant_id')
        
        # On force la récupération des données si on ne les a pas ou si elles ne correspondent pas
        if plant_id:
            sel = api_get(f"/plants/{plant_id}")
            # On met à jour selected_plant pour les autres fonctions qui pourraient en avoir besoin
            st.session_state.selected_plant = sel 
            
            # --- RECHARGEMENT DES VARIABLES DE CALENDRIER EN MEMOIRE ---
            if st.session_state.get('force_reload', False):
                st.session_state.force_reload = False
                
                def parse_m(db_val):
                    if not db_val: return []
                    return[int(m.strip()) for m in str(db_val).split(",") if m.strip().isdigit()]
                
                st.session_state.temp_flowering = parse_m(sel.get('flowering_months'))
                st.session_state.temp_harvest = parse_m(sel.get('harvest_months'))
                st.session_state.temp_pruning = parse_m(sel.get('pruning_months'))
                st.session_state.temp_fertilizing = parse_m(sel.get('fertilizing_months'))
                st.session_state.is_fruit = bool(sel.get('is_fruit', False))
                st.session_state.is_vegetable = bool(sel.get('is_vegetable', False))
                st.session_state.is_edible = bool(sel.get('is_edible', False))
        else:
            sel = None
            
        if not sel or 'id' not in sel:
            st.error("Impossible de charger les données de la plante.")
            if st.button("Retour à l'Agenda"):
                st.session_state.view = "agenda"
                st.rerun()
            st.stop()
    else:
        # Mode ajout
        sel = {}
        if st.session_state.get('force_reload', False):
            st.session_state.force_reload = False
            st.session_state.selected_plant = {}
            st.session_state.temp_flowering = []
            st.session_state.temp_harvest =[]
            st.session_state.temp_pruning = []
            st.session_state.temp_fertilizing =[]
            st.session_state.is_fruit = False
            st.session_state.is_vegetable = False
            st.session_state.is_edible = False

    h1, h2 = st.columns([1, 4])
    if mode_edit:
        if sel and 'id' in sel:
            photos = api_get(f"/plants/{sel['id']}/photos/")
        else:
            photos = []
        main_p = next((p for p in photos if p['is_main']), None)
        with h1:
            if main_p: st.image(f"{IMG_URL_BASE}/uploads/{main_p['path'].split('/')[-1]}", width="stretch")
        with h2: st.title(sel.get('name_fr', "Fiche Plante"))
    else: st.title("➕ Nouvelle Plante")

    # -VÉRIFICATION de multiplicité ET BANNIÈRE DE SYNCHRONISATION ---
    if mode_edit and sel:
        # On récupère toutes les plantes pour compter les clones
        all_p = api_get("/plants/")
        my_name = sel.get('name_fr', "")
        my_var = sel.get('variety') or ""
        
        # On compte combien d'AUTRES plantes (id différent) partagent le même duo Nom/Variété
        identical_count = sum(1 for p in all_p if p.get('name_fr') == my_name and (p.get('variety') or "") == my_var and p.get('id') != sel.get('id'))
        
        if identical_count > 0:
            st.info(f"🔄 **Synchronisation active :** Vous possédez **{identical_count} autre(s) exemplaire(s)** de cette plante. Les modifications apportées à la botanique et aux calendriers seront appliquées à tous lors de la sauvegarde.\n*(Exclus de la synchronisation : emplacement, achat, historique, photos et confiance d'identification. Modifiez le nom ou la variété pour désolidariser cette fiche).*")

    # --- CADRE PRINCIPAL ---
    with st.container(border=False):
        opt_types = [o['value'] for o in api_get("/settings/location_type")] or["Extérieur"]
        opt_loczone = [o['value'] for o in api_get("/settings/location_zone")] or [""]
        opt_conts = [o['value'] for o in api_get("/settings/container")] or["Pleine Terre"]
        opt_ptyp = [o['value'] for o in api_get("/settings/plant_type")]
        opt_tags = [o['value'] for o in api_get("/settings/tags")]        
        options_types_with_none = ["-"] + [opt for opt in opt_types if opt != "-"]
        options_loczone_with_none =["-"] +[opt for opt in opt_loczone if opt != "-"]
        options_conts_with_none = ["-"] +[opt for opt in opt_conts if opt != "-"]

        # Formulaire pour les champs texte
        with st.form("p_form", border=False):

            col_head_titre, col_head_btn = st.columns([3, 1])
            with col_head_titre: st.write("### 🏷️ Identité et Emplacement")
            with col_head_btn:
                submit = st.form_submit_button("💾 Sauvegarder la fiche")

            col_id1, col_id2 = st.columns(2)
            with col_id1:
                is_archived = st.checkbox("❌ Indisponible", value=bool(sel.get('is_archived', False)))
            with col_id2:
                rating_options = [None] + list(range(0, 11))
                current_rating = sel.get('rating')
                rating_val = int(current_rating) if current_rating is not None else None
                rating = st.selectbox("⭐ Note (0-10)", options=rating_options, index=rating_options.index(rating_val) if rating_val in rating_options else 0, format_func=lambda x: "-" if x is None else str(x))

            # Zone de présentation (plus courte)
            d_presentation = st.text_area("📖 "+_("presentation"), 
                                value=sel.get('presentation', ""), 
                                help="Origine, entretien général, etc.")
            col1, col2 = st.columns(2)
            with col1:
                n_fr = st.text_input("Nom FR *", value=sel.get('name_fr', ""))
                n_en = st.text_input("Nom EN", value=sel.get('name_en', ""))
                n_sci = st.text_input("Nom Latin", value=sel.get('name_sci', ""))
                other_names = st.text_input("Autres noms", value=sel.get('other_names', ""), help="Séparateur virgule")
                variety = st.text_input("Variété / Cultivar", value=sel.get('variety', ""))

            with col2:
                # Pour le Type Plante
                current_pt_raw = sel.get('plant_type') or ""
                if current_pt_raw == "-":
                    current_pt_list =[]
                else:
                    current_pt_list =[x.strip() for x in current_pt_raw.split(",") if x.strip() in opt_ptyp]
                l_pt_list = st.multiselect(
                    _("plant_type"), 
                    options=opt_ptyp, 
                    default=current_pt_list,
                    placeholder="-"
                )
                l_pt_final = ", ".join(l_pt_list) if l_pt_list else ""
                # Etiquettes
                current_tags_raw = sel.get('tags') or ""
                current_tags_list =[x.strip() for x in current_tags_raw.split(",") if x.strip() in opt_tags]
                l_tags_list = st.multiselect(_("tags"), options=opt_tags, default=current_tags_list, placeholder="-")
                l_tags_final = ", ".join(l_tags_list) if l_tags_list else ""

                link = st.text_input(_("weblink"), value=sel.get('web_link', ""))

            # --- SECTION 1a : Emplacement ---
            st.write("### 🌿 "+_("location"))

            col1, col2 = st.columns(2)
            with col1:
                # Pour le Type Location
                current_type = sel.get('location_type')
                # Si c'est une nouvelle plante (None) ou une valeur inconnue, on force "-"
                if not current_type or current_type not in options_types_with_none:
                    current_type = "-"
                l_t = st.selectbox(
                    _("location_type"), 
                    options_types_with_none, 
                    index=options_types_with_none.index(current_type)
                )
                # Zone Location
                current_locationzone = sel.get('location_zone')
                # Si c'est une nouvelle plante (None) ou une valeur inconnue, on force "-"
                if not current_locationzone or current_locationzone not in options_loczone_with_none:
                    current_locationzone = "-"
                l_z = st.selectbox(
                    _("location_zone"), 
                    options_loczone_with_none, 
                    index=options_loczone_with_none.index(current_locationzone)
                )
                # Detail Location
                l_d = st.text_input(_("location_detail"), value=sel.get('location_detail', ""))
            with col2:
                # Pour le type de Contenant
                current_cont = sel.get('container')
                if not current_cont or current_cont not in options_conts_with_none:
                    current_cont = "-"
                l_c = st.selectbox(
                    _("container_type"), 
                    options_conts_with_none, 
                    index=options_conts_with_none.index(current_cont)
                )
                # Contenant
                # 1. On récupère la liste réelle des pots depuis l'API
                all_containers_data = api_get("/containers/")
                if not isinstance(all_containers_data, list): 
                    all_containers_data = []

                filtered_containers = []
                current_c_id = sel.get('container_id')

                for c in all_containers_data:
                    c_loc = c.get('location_type')
                    c_type_val = c.get('container_type')

                    # Filtres (bien indentés) :
                    # 1. Emplacement (Int/Ext) : Correspond à la plante ou l'un des deux n'est pas défini
                    loc_match = (not current_type or current_type == "-" or not c_loc or c_loc == "-" or c_loc == current_type)
                    # 2. Type de contenant (Pot, Jardinière...) : Correspond à la plante ou la plante n'a pas de type défini
                    type_match = (not current_cont or current_cont == "-" or c_type_val == current_cont)
                
                # Condition d'affichage :
                # - C'est le contenant déjà assigné à cette plante (pour ne pas le perdre)
                # - OU la plante n'a pas d'emplacement spécifique ("-")
                # - OU le pot n'a pas d'emplacement spécifique ("-")
                # - OU l'emplacement du pot correspond à l'emplacement de la plante
                    if c.get('id') == current_c_id or (loc_match and type_match):
                       filtered_containers.append(c)

                # 2. On crée le dictionnaire d'options {id: "Nom (Type)"}
                container_options = {None: "-"}
                for c in filtered_containers:
                    if isinstance(c, dict):
                        brand = c.get('container_brand')
                        brand_str = f" ({brand})" if brand else ""
                        container_options[c['id']] = f"{c.get('name')}{brand_str}"
                        
                # 3. On récupère l'ID du container déjà associé à la plante (si existant)
                selected_c_id = st.selectbox(
                    _("container_set"),
                    options=list(container_options.keys()),
                    format_func=lambda x: container_options[x],
                    index=list(container_options.keys()).index(current_c_id) if current_c_id in container_options else 0
                )

            # --- SECTION 1b : BOTANIQUE ---
            st.write("### 🌿 Caractéristiques Botaniques")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                hard = st.text_input(_("hardiness"), value=sel.get('hardiness', ""))
                h_mat = st.text_input(_("height"), value=sel.get('height', ""))
                f_color = st.text_input("Couleur des fleurs", value=sel.get('flower_color', ""))

                f_options = ["-", "Caduc", "Semi-persistant", "Persistant"]
                current_f = sel.get('foliage_persistence') if sel.get('foliage_persistence') in f_options else "-"
                f_pers = st.selectbox("Feuillage", f_options, index=f_options.index(current_f))

            with col_b2:
                # Pour l'exposition
                e_options = ["Soleil", "Mi-ombre", "Ombre"]
                current_e_raw = sel.get('exposure') or ""
                if current_e_raw == "-":
                    current_e_list = []
                else:
                    current_e_list = [x.strip() for x in current_e_raw.split(",") if x.strip() in e_options]
                exp_list = st.multiselect("Exposition", options=e_options, default=current_e_list, placeholder="-")
                exp_final = ", ".join(exp_list) if exp_list else ""

                # Pour l'humidité du sol
                s_options = ["Sec", "Moyen", "Frais", "Humide"]
                current_s_raw = sel.get('soil_humidity') or ""
                if current_s_raw == "-":
                    current_s_list = []
                else:
                    current_s_list = [x.strip() for x in current_s_raw.split(",") if x.strip() in s_options]
                soil_list = st.multiselect("Humidité du sol", options=s_options, default=current_s_list, placeholder="-")
                soil_final = ", ".join(soil_list) if soil_list else ""
                # Details sol
                soil_details = st.text_input("Détails du sol (Terreau, drainage, pH...)", value=sel.get('soil_details', ""))

            c_s1, c_s2 = st.columns(2)
            with c_s1:
                # Confiance (Permet de laisser le champ vide)
                conf_raw = sel.get('id_confidence')
                conf_val = int(conf_raw) if conf_raw is not None else None
                conf = st.number_input("Confiance identification (%)", min_value=0, max_value=100, value=conf_val, step=10)
                
                # Mellifère (Liste déroulante de - à 5)
                score_options =[None, 0, 1, 2, 3, 4, 5]
                mell_raw = sel.get('melliferous_score')
                mell_val = int(mell_raw) if mell_raw is not None else None
                mell = st.selectbox(
                    "Niveau mellifère (0-5)", 
                    options=score_options, 
                    index=score_options.index(mell_val) if mell_val in score_options else 0,
                    format_func=lambda x: "-" if x is None else str(x)
                )

            with c_s2:
                # Toxicité (Liste déroulante de - à 5)
                tox_raw = sel.get('toxicity_score')
                tox_val = int(tox_raw) if tox_raw is not None else None
                tox = st.selectbox(
                    "Toxicité (0-5)", 
                    options=score_options, 
                    index=score_options.index(tox_val) if tox_val in score_options else 0,
                    format_func=lambda x: "-" if x is None else str(x)
                )
                tox_txt = st.text_area("Détails toxicité", value=sel.get('toxicity_detail', ""), height=68)

            c_s3, c_s4 = st.columns(2)
            with c_s3:
                is_edible = st.checkbox("Comestible", value=bool(sel.get('is_edible', False)))
                st.session_state.is_fruit = st.checkbox("🍎 Fruit", value=st.session_state.is_fruit)
                st.session_state.is_vegetable = st.checkbox("🥦 Légume", value=st.session_state.is_vegetable)

            with c_s4:
                edib_txt = st.text_area("Détails comestibilité", value=sel.get('edibility_detail', ""), height=68)


            # --- SECTION 3 : ACHAT & SUIVI ---
            st.write("### 💰 Achat")
            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                p_loc = st.text_input("Lieu d'achat", value=sel.get('purchase_location', ""))
            with c_a2:

                p_date_init = parse_date(sel.get('purchase_date'))
                p_date = st.date_input("Date d'achat", value=p_date_init, format="DD/MM/YYYY")
            with c_a3:
                # --- MODIFICATION: Prix vide par défaut ---
                raw_p_price = sel.get('purchase_price')
                p_price_val = float(raw_p_price) if raw_p_price is not None and str(raw_p_price).strip() != "" else None
                p_price = st.number_input("Prix d'achat (€)", value=p_price_val)
            d_notes = st.text_area("📝 Historique et notes libres", 
                         value=sel.get('notes', ""), 
                         height=200,
                         help="Suivi, notes et commentaires sur les entretiens et problèmes rencontrés, etc.")

            st.write("### ✂️ Entretien et Calendriers")
            cc1, cc2 = st.columns(2)
            with cc1: 
                comm_prun = st.text_area("Notes sur la Taille", value=sel.get('pruning_comment', ""))
            with cc2: 
                comm_fert = st.text_area("Notes sur l'Engrais", value=sel.get('fertilizing_comment', ""))
            comm_harv = st.text_area("📝 Notes sur la Récolte", 
                         value=sel.get('harvest_comment', ""), 
                         height=200,
                         help="Consiels de récolte et d'utilisation")
                
            dcol1, dcol2, dcol3, dcol4 = st.columns(4)
            with dcol1: d_plantation = st.date_input("🌱 Date de plantation", value=parse_date(sel.get('date_plantation')), format="DD/MM/YYYY")
            with dcol2: d_fertilisation = st.date_input("🧪 Dernière fertilisation", value=parse_date(sel.get('date_last_fertilisation')), format="DD/MM/YYYY")
            with dcol3: d_taille = st.date_input("✂️ Dernière taille", value=parse_date(sel.get('date_last_taille')), format="DD/MM/YYYY")
            with dcol4: r_date = st.date_input("🪴 Dernier rempotage", value=parse_date(sel.get('last_repotting_date')), format="DD/MM/YYYY")

            # --- NOUVEAU BOUTON EN BAS DE FORMULAIRE ---
            st.write("") # Petit espacement visuel
            submit_bottom = st.form_submit_button("💾 Sauvegarder la fiche", width='stretch', key="submit_bottom_btn")

            # ACTION DES BOUTONS (On valide si celui du HAUT -ou- celui du BAS est cliqué)
            if submit or submit_bottom:
                data = {
                    "name_fr": n_fr, "name_en": n_en, "name_sci": n_sci, "hardiness": hard, "height": h_mat,
                    "plant_type": l_pt_final,
                    "is_fruit": st.session_state.is_fruit, "is_vegetable": st.session_state.is_vegetable,
                    "flowering_months": ", ".join([f"{m:02d}" for m in st.session_state.temp_flowering]),
                    "harvest_months": ", ".join([f"{m:02d}" for m in st.session_state.temp_harvest]),
                    "pruning_months": ", ".join([f"{m:02d}" for m in st.session_state.temp_pruning]),
                    "fertilizing_months": ", ".join([f"{m:02d}" for m in st.session_state.temp_fertilizing]),
                    "pruning_comment": comm_prun, "fertilizing_comment": comm_fert, "pruning_comment": comm_harv,
                    "location_type": l_t, "location_zone": l_z, "location_detail": l_d, "container": l_c,
                    "date_plantation": str(d_plantation) if d_plantation else "",
                    "date_last_fertilisation": str(d_fertilisation) if d_fertilisation else "",
                    "date_last_taille": str(d_taille) if d_taille else "",
                    "presentation": str(d_presentation) if d_presentation else "",
                    "notes": str(d_notes) if d_notes else "",
                    "web_link": str(link) if link else "",
                    "id_confidence": conf,
                    "melliferous_score": mell,
                    "toxicity_score": tox,
                    "toxicity_detail": str(tox_txt) if tox_txt else "",
                    "is_edible": is_edible,
                    "edibility_detail": str(edib_txt) if edib_txt else "",
                    "flower_color": str(f_color) if f_color else "",
                    "foliage_persistence": str(f_pers) if f_pers else "-",
                    "exposure": exp_final,
                    "soil_humidity": soil_final,
                    "soil_details": soil_details,
                    "purchase_location": str(p_loc) if p_loc else "",
                    "purchase_price": p_price,
                    "purchase_date": str(p_date) if p_date else "",
                    "last_repotting_date": str(r_date) if r_date else "",
                    "container_id": selected_c_id,
                    "variety": variety,
                    "tags": l_tags_final,
                    "rating": rating,
                    "is_archived": is_archived,
                    "other_names": other_names
                }

                # 3. Envoi à l'API
                try:
                    if mode_edit:
                        target_id = sel.get('id')
                        if target_id:
                            response = requests.put(f"{API_URL}/plants/{target_id}", json=data)
                        else:
                            st.error("Erreur : ID de la plante introuvable.")
                    else:
                        response = requests.post(f"{API_URL}/plants/", json=data)

                    # 4. Vérification post-sauvegarde
                    if response is not None:
                        if response.status_code in[200, 201]:
                            
                            # --- FIX : VERIFICATION DESYNCHRO PROTEGÉE CONTRE LES NONE ---
                            all_p = api_get("/plants/")
                            safe_n_fr = (n_fr or "").strip().lower()
                            safe_var = (variety or "").strip().lower()
                            
                            clones =[p for p in all_p if (p.get('name_fr') or '').strip().lower() == safe_n_fr and (p.get('variety') or "").strip().lower() == safe_var]
                            
                            is_desynced = False
                            if len(clones) > 1:
                                sig0 = f"{clones[0].get('plant_type')}|{clones[0].get('hardiness')}|{clones[0].get('flowering_months')}"
                                if any(f"{c.get('plant_type')}|{c.get('hardiness')}|{c.get('flowering_months')}" != sig0 for c in clones[1:]):
                                    is_desynced = True

                            # Si on vient d'ajouter une nouvelle plante avec des infos discordantes
                            if is_desynced and not mode_edit:
                                st.warning("⚠️ **Attention :** Votre nouvel exemplaire a été enregistré, mais ses données botaniques diffèrent de l'exemplaire existant ! Redirection vers la liste...")
                                time.sleep(5) 
                                st.session_state.view = "list"
                                st.rerun()
                            else:
                                st.toast("Enregistrement réussi", icon="😍")
                                # --- FIX : RETOUR À LA LISTE ---
                                if st.session_state.view == "add":
                                    time.sleep(5) # Laisse 1 sec pour afficher le toast de succès
                                    st.session_state.view = "list"
                                    st.rerun()
                        else:
                            st.error(f"❌ Erreur API ({response.status_code}) : {response.text}")

                except Exception as e:
                    st.error(f"⚠️ Erreur de connexion au serveur : {e}")

# --- BARRES DE MOIS des calendriers ---
    def render_calendar(title, session_key):
        cols = st.columns([2.5] + [1]*12)
        with cols[0]:
            st.markdown(f"<div style='margin-top: 8px; font-size: 0.9em; font-weight: bold;'>{title}</div>", unsafe_allow_html=True)
            
        for i, m in enumerate(range(1, 13)): # m = 1 à 12
            with cols[i+1]:
                act = m in st.session_state[session_key]
                # On récupère le texte ("Jan", "Fév") et on n'affiche que la 1ère lettre ([0])
                month_txt = TRANSLATIONS[st.session_state.lang]["months_short"][m]
                if st.button(month_txt[0], key=f"{session_key}_{m}", type="primary" if act else "secondary"):
                    if act: st.session_state[session_key].remove(m)
                    else: st.session_state[session_key].append(m)
                    st.rerun()

    # Affichage des calendriers (On a retiré l'argument btn_class qui ne sert plus à rien)
    render_calendar("🌷 Floraison", "temp_flowering")
    
    if st.session_state.is_fruit or st.session_state.is_vegetable or st.session_state.is_edible:
        render_calendar("🍎 Récolte", "temp_harvest")
    
    render_calendar("✂️ Taille", "temp_pruning")
    render_calendar("🧪 Fertilisation", "temp_fertilizing")
        

# --- SECTION GALERIE (En dehors du formulaire principal) ---
    if mode_edit:
        st.write("---")
        st.subheader("📸 Galerie Photos")

        # 1. RÉCUPÉRATION DIRECTE DES PHOTOS
        # On force l'appel ici pour être sûr d'avoir les données à jour
        current_plant_id = sel.get('id')
        photos_list = api_get(f"/plants/{current_plant_id}/photos/")

        # 2. ZONE D'UPLOAD
        with st.expander("Ajouter une photo"):
            up_file = st.file_uploader("Choisir une image", type=['jpg', 'jpeg', 'png', 'webp'], key="new_photo")
            
            # --- GESTION INTELLIGENTE DE LA DATE (EXIF) ---
            if up_file is not None:
                # On crée un identifiant unique pour le fichier en cours
                file_id = f"{up_file.name}_{up_file.size}"
                
                # Si c'est un nouveau fichier, on tente d'extraire la date
                if st.session_state.last_uploaded_file != file_id:
                    st.session_state.last_uploaded_file = file_id
                    exif_date = get_exif_date(up_file)
                    
                    # IMPORTANT : On remet le curseur du fichier à 0 pour que l'API puisse le lire ensuite !
                    up_file.seek(0) 
                    
                    if exif_date:
                        st.session_state.extracted_date = exif_date
                        st.success(f"📅 Date extraite automatiquement : **{exif_date.strftime('%d/%m/%Y')}**")
                    else:
                        st.session_state.extracted_date = datetime.now().date()
                        st.info("ℹ️ Aucune date trouvée dans l'image. La date du jour est sélectionnée.")
            else:
                # Si l'utilisateur retire la photo, on réinitialise
                st.session_state.last_uploaded_file = None
                st.session_state.extracted_date = datetime.now().date()

            # AJOUT DU SÉLECTEUR DE DATE (Lié à notre variable d'état)
            photo_date = st.date_input("Date de la photo", key="extracted_date")
            
            if st.button("🚀 Envoyer") and up_file:
                with st.spinner("Traitement..."):
                    files = {"file": (up_file.name, up_file.getvalue(), up_file.type)}
                    payload = {"date": str(photo_date)}
                    
                    res = requests.post(f"{API_URL}/plants/{current_plant_id}/photos/", files=files, data=payload)
                    if res.status_code == 200:
                        st.success("Photo ajoutée avec succès !")
                        # On force la réinitialisation pour la prochaine photo
                        st.session_state.last_uploaded_file = None 
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de l'envoi : {res.text}")

        # 3. AFFICHAGE DES PHOTOS
        if isinstance(photos_list, list) and len(photos_list) > 0:
            # On définit le nombre de colonnes
            nb_cols = 4
            cols = st.columns(nb_cols)

            for idx, p in enumerate(photos_list):
                with cols[idx % nb_cols]:
                    # Construction de l'URL vers l'image redimensionnée (path)
                    # On nettoie le chemin au cas où
                    fname = p['path'].split('/')[-1] if '/' in p['path'] else p['path']
                    img_url = f"{IMG_URL_BASE}/uploads/{fname}"

                    # Affichage de l'image (format carré via CSS ou simple redimensionnement)
                    st.image(img_url, width='stretch')
                    
                    # 2. LA DATE (Ajoutée ici)
                    photo_date = p.get('upload_date', 'Date inconnue')
                    # Optionnel : Si le format est AAAA-MM-JJ, on peut le rendre plus joli
                    if photo_date and '-' in photo_date:
                        try:
                            d = datetime.strptime(photo_date, "%Y-%m-%d")
                            photo_date = d.strftime("%d/%m/%Y")
                        except:
                            pass
                    st.caption(f"📅 {photo_date}")

                    # Barre d'outils sous chaque photo
                    b1, b2, b3 = st.columns(3)

                    with b1: # OUVERTURE GALERIE
                        if st.button("🔍", key=f"zoom_{p['id']}", help="Ouvrir la galerie"):
                            st.session_state.gal_idx = idx # Force le début de la galerie sur la bonne image
                            show_full_photo(photos_list, idx)

                    with b2: # FAVORITE (MAIN)
                        if p.get('is_main'):
                            st.markdown("⭐ **Principale**")
                        else:
                            if st.button("📍", key=f"main_{p['id']}", help="Définir comme photo principale"):
                                requests.put(f"{API_URL}/photos/{p['id']}/main?plant_id={current_plant_id}")
                                st.rerun()

                    with b3: # DELETE
                        if st.button("🗑️", key=f"del_{p['id']}", help="Supprimer cette photo"):
                            requests.delete(f"{API_URL}/photos/{p['id']}")
                            st.rerun()
        else:
            st.info("🌿 Aucune photo n'est associée.")

    if st.button("⬅️ Retour"):
        st.session_state.view = "gallery"
        st.rerun()

    st.write("---")
    # Remplacement de l'expander unique par une zone d'actions avancées
    with st.expander("⚙️ Actions avancées (Dupliquer / Supprimer)"):
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            st.write("📑 **Dupliquer la plante**")
            st.write("Crée une copie synchronisée de cette fiche (même nom et variété) sans recopier l'historique ou les photos.")
            if mode_edit and st.session_state.selected_plant_id is not None:
                if st.button("➕ Créer un nouvel exemplaire", use_container_width=True):
                    # On prépare un dictionnaire avec UNIQUEMENT les infos communes
                    dup_data = {
                        "name_fr": sel.get('name_fr', ''),
                        "name_en": sel.get('name_en', ''),
                        "name_sci": sel.get('name_sci', ''),
                        "variety": sel.get('variety', ''),
                        "plant_type": sel.get('plant_type', ''),
                        "hardiness": sel.get('hardiness', ''),
                        "height": sel.get('height', ''),
                        "flowering_months": sel.get('flowering_months', ''),
                        "harvest_months": sel.get('harvest_months', ''),
                        "pruning_months": sel.get('pruning_months', ''),
                        "fertilizing_months": sel.get('fertilizing_months', ''),
                        "pruning_comment": sel.get('pruning_comment', ''),
                        "fertilizing_comment": sel.get('fertilizing_comment', ''),
                        "pruning_comment": sel.get('pruning_comment', ''),
                        "is_fruit": bool(sel.get('is_fruit', False)),
                        "is_vegetable": bool(sel.get('is_vegetable', False)),
                        "presentation": sel.get('presentation', ''),
                        "web_link": sel.get('web_link', ''),
                        "id_confidence": sel.get('id_confidence'),
                        "melliferous_score": sel.get('melliferous_score'),
                        "toxicity_score": sel.get('toxicity_score'),
                        "toxicity_detail": sel.get('toxicity_detail', ''),
                        "is_edible": bool(sel.get('is_edible', False)),
                        "edibility_detail": sel.get('edibility_detail', ''),
                        "flower_color": sel.get('flower_color', ''),
                        "foliage_persistence": sel.get('foliage_persistence', ''),
                        "exposure": sel.get('exposure', ''),
                        "soil_humidity": sel.get('soil_humidity', ''),
                        "soil_details": sel.get('soil_details', ''),
                        "tags": sel.get('tags', ''),
                        "other_names": other_names
                    }
                    res = requests.post(f"{API_URL}/plants/", json=dup_data)
                    if res.status_code in [200, 201]:
                        st.success("Plante dupliquée avec succès !")
                        # On charge automatiquement la nouvelle fiche !
                        st.session_state.selected_plant_id = res.json().get('id')
                        st.session_state.force_reload = True
                        st.rerun()
                    else:
                        st.error(f"Erreur lors de la duplication : {res.text}")
            else:
                st.info("Sauvegardez d'abord la fiche pour pouvoir la dupliquer.")

        with col_act2:
            st.write("⚠️ **Zone de danger**")
            st.write("La suppression est définitive et supprimera également les photos associées.")
            if st.session_state.selected_plant_id is not None:
                if st.button("🗑️ Supprimer définitivement cette fiche", type="primary", use_container_width=True):
                    response = requests.delete(f"{API_URL}/plants/{st.session_state.selected_plant_id}")
                    if response.status_code == 200:
                        st.success("Fiche supprimée.")
                        st.session_state.view = "list"
                        st.rerun()
                    else:
                        st.error("Erreur lors de la suppression.")
            else:
                st.warning("Aucune plante sélectionnée pour la suppression.")
