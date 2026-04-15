import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Plant Tracker", page_icon="🌿", layout="wide")

# --- CONFIGURATION ---
API_URL = "http://backend:8000"
# Assure-toi que cette IP correspond bien à ton accès réseau externe/interne
IMG_URL_BASE = "http://192.168.1.105:8000" 
MONTHS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]

# --- STYLE CSS ---
st.markdown("""
    <style>
    .flow-btn button[kind="primary"] { background-color: #FFD700 !important; color: black !important; border: 2px solid #FFD700 !important; }
    .harv-btn button[kind="primary"] { background-color: #FF4B4B !important; color: white !important; border: 2px solid #FF4B4B !important; }
    .prun-btn button[kind="primary"] { background-color: #2E8B57 !important; color: white !important; border: 2px solid #2E8B57 !important; }
    .fert-btn button[kind="primary"] { background-color: #8A2BE2 !important; color: white !important; border: 2px solid #8A2BE2 !important; }
    div.stButton > button { width: 100% !important; font-weight: bold; border: 0px; }
    .stImage img { border-radius: 10px; }
    /* Ajustement pour coller le formulaire au container */
    .stForm { border: none !important; padding: 0 !important; }
    /* Ciblage ultra-précis des cellules d'images dans le canvas Streamlit */
    div[data-testid="stDataFrame"] table img, 
    div[data-testid="stTable"] table img,
    .st-emotion-cache-1p6f546 img { 
        object-fit: cover !important;
        width: 50px !important;   /* Force une largeur fixe */
        height: 50px !important;  /* Force la même hauteur */
        aspect-ratio: 1 / 1 !important;
        border-radius: 8px !important;
    }
    /* Ajustement de la ligne pour que le carré ne soit pas écrasé */
    [data-testid="stDataFrame"] [role="gridcell"] {
        vertical-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)


# --- FONCTIONS API ---
def api_get(path):
    try: return requests.get(f"{API_URL}{path}").json()
    except: return []

def api_post(path, data): return requests.post(f"{API_URL}{path}", json=data)
def api_delete(path): requests.delete(f"{API_URL}{path}")

@st.dialog("Zoom Photo")
def show_full_photo(url, date):
    st.image(url, width="stretch")
    st.write(f"📅 Photo du : **{date}**")

# --- ÉTAT DE SESSION ---
if "view" not in st.session_state: st.session_state.view = "list"
if "selected_plant" not in st.session_state: st.session_state.selected_plant = None
if "temp_flowering" not in st.session_state: st.session_state.temp_flowering = []
if "temp_pruning" not in st.session_state: st.session_state.temp_pruning = []
if "temp_fertilizing" not in st.session_state: st.session_state.temp_fertilizing = []
if "temp_harvest" not in st.session_state: st.session_state.temp_harvest = []
if "is_fruit" not in st.session_state: st.session_state.is_fruit = False
if "is_vegetable" not in st.session_state: st.session_state.is_vegetable = False

# --- SIDEBAR ---
with st.sidebar:
    st.title("🍀 Menu")
    if st.button("📋 Mes Plantes"):
        st.session_state.view = "list"
        st.rerun()
    if st.button("🔍 Recherche Avancée"):
        st.session_state.view = "search"
        st.rerun()
    if st.button("➕ Ajouter une plante"):
        st.session_state.view = "add"
        st.session_state.selected_plant = None
        st.session_state.temp_flowering, st.session_state.temp_harvest = [], []
        st.session_state.is_fruit, st.session_state.is_vegetable = False, False
        st.rerun()
    st.write("---")
    if st.button("⚙️ Gérer les options"):
        st.session_state.view = "settings"
        st.rerun()

# --- VUE : SETTINGS ---
if st.session_state.view == "settings":
    st.title("⚙️ Paramètres")
    cats = {"type": "Types", "zone": "Zones", "detail": "Lieux", "container": "Contenants"}
    c_key = st.selectbox("Liste", options=list(cats.keys()), format_func=lambda x: cats[x])
    with st.form("add_opt"):
        nv = st.text_input("Valeur")
        if st.form_submit_button("Ajouter") and nv:
            api_post("/settings/", {"category": c_key, "value": nv})
            st.rerun()
    for o in api_get(f"/settings/{c_key}"):
        c_t, c_b = st.columns([4, 1])
        c_t.write(f"• {o['value']}")
        if c_b.button("🗑️", key=f"d_o_{o['id']}"):
            api_delete(f"/settings/{o['id']}")
            st.rerun()

# --- VUE : LISTE ---
elif st.session_state.view == "list":
    st.title("🌿 Ma Collection")
    plants = api_get("/plants/")

    if plants:
        import pandas as pd
        df = pd.DataFrame(plants)

        # --- ÉTAPE CLÉ : RÉORGANISATION ---
        # On définit l'ordre exact ici. Les colonnes non listées seront à la fin.
        cols_order = ["image_url", "name_fr", "location_type", "container"]
        # On ne garde que les colonnes qui existent vraiment dans le DF
        existing_cols = [c for c in cols_order if c in df.columns]
        other_cols = [c for c in df.columns if c not in existing_cols]
        df = df[existing_cols + other_cols]

        column_configuration = {
            "image_url": st.column_config.ImageColumn("Aperçu", width="medium"),
            "name_fr": "Nom Commun",
            "name_sci": "Nom Scientifique",
            "name_en": "Nom Anglais",
            "location_type": "Int/Ext",
            "container": "Contenant",
            "hardiness": "Rusticité",
            "height": "Hauteur",
            "location_zone": "Zone",
            "flowering_months": "Floraison",
            "harvest_months": "Récolte",
            "pruning_months": "Taille",
            "fertilizing_months": "Engrais",
            "id": None, "main_photo": None # On cache le reste
        }

        # Affichage du tableau avec les photos
        event = st.dataframe(
            df, 
            column_config=column_configuration,
            width="stretch", 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )

        if event.selection.rows:
            sel = plants[event.selection.rows[0]]
            st.session_state.selected_plant = sel
            st.session_state.temp_flowering = [m for m in (sel.get('flowering_months', "") or "").split(", ") if m]
            st.session_state.temp_harvest = [m for m in (sel.get('harvest_months', "") or "").split(", ") if m]
            st.session_state.temp_pruning = [m for m in (sel.get('pruning_months', "") or "").split(", ") if m]
            st.session_state.temp_fertilizing = [m for m in (sel.get('fertilizing_months', "") or "").split(", ") if m]
            st.session_state.is_fruit = bool(sel.get('is_fruit', False))
            st.session_state.is_vegetable = bool(sel.get('is_vegetable', False))
            st.session_state.view = "edit"
            st.rerun()

# --- VUE : RECHERCHE MULTI-CRITÈRES ---
elif st.session_state.view == "search":
    st.title("🔍 Recherche & Calendrier")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            s_name = st.text_input("Nom (Fr, EN ou Latin)")
            s_type = st.selectbox("Intérieur/Extérieur", ["Tous"] + [o['value'] for o in api_get("/settings/type")])
            s_cat = st.radio("Catégorie", ["Toutes", "Fruits", "Légumes"], horizontal=True)

        with col2:
            s_cont = st.selectbox("Contenant", ["Tous"] + [o['value'] for o in api_get("/settings/container")])
            # Filtre par mois
            s_flow = st.selectbox("🌸 Floraison en...", ["Tous"] + MONTHS)
            s_harv = st.selectbox("🍎 Récolte en...", ["Tous"] + MONTHS)
            s_fert = st.selectbox("🍎 Engrais en...", ["Tous"] + MONTHS)
            s_prun = st.selectbox("🍎 Tailler en...", ["Tous"] + MONTHS)
            
        with col3:
            st.write("💡 **Astuce**")
            st.caption("Sélectionnez un mois pour voir ce qui fleurit ou se récolte à cette période précise de l'année.")

    # Construction des paramètres pour l'API
    params = {}
    if s_name: params["name"] = s_name
    if s_type != "Tous": params["location_type"] = s_type
    if s_cont != "Tous": params["container"] = s_cont
    if s_flow != "Tous": params["flowering_month"] = s_flow
    if s_harv != "Tous": params["harvest_month"] = s_harv
    if s_fert != "Tous": params["fertilizing_month"] = s_fert
    if s_prun != "Tous": params["pruning_month"] = s_prun
    if s_cat == "Fruits": params["is_fruit"] = True
    if s_cat == "Légumes": params["is_vegetable"] = True

    # Appel API
    search_results = requests.get(f"{API_URL}/plants/search/", params=params).json()

    st.write(f"### 📋 Résultats ({len(search_results)})")
    
    if search_results:
        # Configuration de l'affichage du tableau
        display_df = []
        for r in search_results:
            display_df.append({
                "Nom": r['name_fr'],
                "Latin": r['name_sci'],
                "Type": r['location_type'],
                "Lieu": r['location_detail'],
                "Contenant": r['container'],
                "Floraison": r['flowering_months'],
                "Récolte": r['harvest_months'],
                "Engrais": r['fertilizing_months'],
                "Taille": r['pruning_months']
            })
            
        event = st.dataframe(
            display_df, 
            width="stretch", 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )
        
        # Logique pour ouvrir la fiche quand on clique sur une ligne
        if event.selection.rows:
            idx = event.selection.rows[0]
            sel = search_results[idx]
            st.session_state.selected_plant = sel
            st.session_state.temp_flowering = [m for m in (sel.get('flowering_months', "") or "").split(", ") if m]
            st.session_state.temp_harvest = [m for m in (sel.get('harvest_months', "") or "").split(", ") if m]
            st.session_state.temp_pruning = [m for m in (sel.get('fertilizing_months', "") or "").split(", ") if m]
            st.session_state.temp_fertilizing = [m for m in (sel.get('pruning_months', "") or "").split(", ") if m]
            st.session_state.is_fruit = bool(sel.get('is_fruit', False))
            st.session_state.is_vegetable = bool(sel.get('is_vegetable', False))
            st.session_state.view = "edit"
            st.rerun()
    else:
        st.info("Aucune plante ne correspond à ces critères.")

# --- VUE : FICHE (AJOUT / EDIT) ---
elif st.session_state.view in ["add", "edit"]:
    mode_edit = st.session_state.view == "edit"
    sel = st.session_state.selected_plant if mode_edit else {}
    
    h1, h2 = st.columns([1, 4])
    if mode_edit:
        photos = api_get(f"/plants/{sel['id']}/photos/")
        main_p = next((p for p in photos if p['is_main']), None)
        with h1:
            if main_p: st.image(f"{IMG_URL_BASE}/uploads/{main_p['path'].split('/')[-1]}", width="stretch")
        with h2: st.title(sel.get('name_fr', "Fiche Plante"))
    else: st.title("➕ Nouvelle Plante")

    # --- CADRE PRINCIPAL ---
    with st.container(border=True):
        st.write("### 🏷️ Catégorie & Infos")
        
        # Fruit / Légume intégrés visuellement mais réactifs
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.is_fruit = st.checkbox("🍎 Fruit", value=st.session_state.is_fruit)
        with c2:
            st.session_state.is_vegetable = st.checkbox("🥦 Légume", value=st.session_state.is_vegetable)
        
        st.write("---")

        opt_types = [o['value'] for o in api_get("/settings/type")] or ["Extérieur"]
        opt_conts = [o['value'] for o in api_get("/settings/container")] or ["Pleine Terre"]

        # Formulaire pour les champs texte
        with st.form("p_form", border=False):
            col1, col2 = st.columns(2)
            with col1:
                n_fr = st.text_input("Nom FR *", value=sel.get('name_fr', ""))
                n_en = st.text_input("Nom EN", value=sel.get('name_en', ""))
                n_sci = st.text_input("Nom Latin", value=sel.get('name_sci', ""))
            with col2:
                hard = st.text_input("Rusticité", value=sel.get('hardiness', ""))
                h_mat = st.text_input("Hauteur", value=sel.get('height', ""))
                l_t = st.selectbox("Type", opt_types, index=opt_types.index(sel.get('location_type')) if sel.get('location_type') in opt_types else 0)
                l_z = st.text_input("Zone", value=sel.get('location_zone', ""))
                l_d = st.text_input("Lieu", value=sel.get('location_detail', ""))
                l_c = st.selectbox("Contenant", opt_conts, index=opt_conts.index(sel.get('container')) if sel.get('container') in opt_conts else 0)

            st.write("---")
            st.write("### ✂️ Entretien & Maintenance")
            cc1, cc2 = st.columns(2)
            with cc1: 
                comm_prun = st.text_area("Notes sur la Taille", value=sel.get('pruning_comment', ""))
            with cc2: 
                comm_fert = st.text_area("Notes sur l'Engrais", value=sel.get('fertilizing_comment', ""))

            if st.form_submit_button("💾 Sauvegarder la fiche"):
                data = {
                    "name_fr": n_fr, "name_en": n_en, "name_sci": n_sci, "hardiness": hard, "height": h_mat,
                    "is_fruit": st.session_state.is_fruit, "is_vegetable": st.session_state.is_vegetable,
                    "flowering_months": ", ".join(st.session_state.temp_flowering),
                    "harvest_months": ", ".join(st.session_state.temp_harvest),
                    "pruning_months": ", ".join(st.session_state.temp_pruning),
                    "fertilizing_months": ", ".join(st.session_state.temp_fertilizing),
                    "pruning_comment": comm_prun, 
                    "fertilizing_comment": comm_fert,
                    "location_type": l_t, "location_zone": l_z, "container": l_c
                }

                if mode_edit: requests.put(f"{API_URL}/plants/{sel['id']}", json=data)
                else: api_post("/plants/", data)
                st.session_state.view = "list"
                st.rerun()

    # --- BARRES DE MOIS ---
    def render_calendar(title, session_key, btn_class):
        st.write(f"### {title}")
        cols = st.columns(12)
        for i, m in enumerate(MONTHS):
            with cols[i]:
                act = m in st.session_state[session_key]
                st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                if st.button(m, key=f"{session_key}_{m}", type="primary" if act else "secondary"):
                    if act: st.session_state[session_key].remove(m)
                    else: st.session_state[session_key].append(m)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # Affichage des 4 calendriers
    render_calendar("📅 Floraison", "temp_flowering", "flow-btn")
    
    if st.session_state.is_fruit or st.session_state.is_vegetable:
        render_calendar("🍎 Récolte", "temp_harvest", "harv-btn")
    
    render_calendar("✂️ Taille", "temp_pruning", "prun-btn")
    render_calendar("🧪 Fertilisation", "temp_fertilizing", "fert-btn")

    # --- GALERIE ---
    if mode_edit:
        st.write("---")
        st.subheader("📸 Galerie Photos")
        with st.expander("➕ Ajouter une photo"):
            up = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
            dt = st.date_input("Date", value=datetime.now())
            if st.button("Envoyer") and up:
                requests.post(f"{API_URL}/plants/{sel['id']}/photos/", files={"file": up}, data={"date": str(dt)})
                st.rerun()
        
        if photos:
            p_cols = st.columns(4)
            for idx, p in enumerate(photos):
                with p_cols[idx % 4]:
                    url = f"{IMG_URL_BASE}/uploads/{p['path'].split('/')[-1]}"
                    st.image(url, width="stretch")
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("🔍", key=f"z_{p['id']}"): show_full_photo(url, p['upload_date'])
                    with b2:
                        if not p['is_main'] and st.button("⭐", key=f"s_{p['id']}"):
                            target_url = f"{API_URL}/photos/{p['id']}/main?plant_id={sel['id']}"
                            response = requests.put(target_url)
                            if response.status_code == 200:
                                 st.rerun() # Crucial pour rafraîchir l'affichage
                            else:
                                st.error("Erreur lors de la mise à jour")
                        elif p['is_main']:
                            st.write("🌟")
                    with b3:
                        if st.button("🗑️", key=f"d_{p['id']}"):
                            api_delete(f"/photos/{p['id']}")
                            st.rerun()

    if st.button("⬅️ Retour"):
        st.session_state.view = "list"
        st.rerun()
