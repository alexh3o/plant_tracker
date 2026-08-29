from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image, ImageOps
import io
import sqlite3
import os
import shutil
import zipfile

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configuration CORS pour Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect("plants.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- MODÈLE DE DONNÉES ---
class Plant(BaseModel):
    id: Optional[int] = None
    name_fr: str
    name_en: Optional[str] = ""
    name_sci: Optional[str] = ""
    variety: Optional[str] = ""
    plant_type: Optional[str] = ""
    is_edible: bool = False
    edibility_detail: Optional[str] = ""
    is_fruit: bool = False
    is_vegetable: bool = False
    hardiness: Optional[str] = ""
    exposure: Optional[str] = ""
    soil_humidity: Optional[str] = ""
    soil_details: Optional[str] = ""
    height: Optional[str] = ""
    flowering_months: Optional[str] = ""
    harvest_months: Optional[str] = ""
    pruning_months: Optional[str] = ""
    fertilizing_months: Optional[str] = ""
    pruning_comment: Optional[str] = ""
    fertilizing_comment: Optional[str] = ""
    harvest_comment: Optional[str] = ""
    location_type: Optional[str] = ""
    location_zone: Optional[str] = ""
    location_detail: Optional[str] = ""
    container: Optional[str] = ""
    date_plantation: Optional[str] = ""
    date_last_fertilisation: Optional[str] = ""
    date_last_taille: Optional[str] = ""
    last_repotting_date: Optional[str] = ""
    presentation: Optional[str] = ""
    notes: Optional[str] = ""
    web_link: Optional[str] = ""
    id_confidence: Optional[int] = None
    melliferous_score: Optional[int] = None
    toxicity_score: Optional[int] = None
    toxicity_detail: Optional[str] = ""
    flower_color: Optional[str] = ""
    foliage_persistence: Optional[str] = ""
    purchase_location: Optional[str] = ""
    purchase_price: Optional[float] = 0.0
    purchase_date: Optional[str] = ""
    container_id: Optional[int] = None
    tags: Optional[str] = ""
    rating: Optional[int] = None
    is_archived: bool = False
    other_names: Optional[str] = ""

class SettingUpdate(BaseModel):
    old_value: str
    new_value: str
    category: str

class Container(BaseModel):
    id: Optional[int] = None
    container_type: str
    name: str
    color: Optional[str] = ""
    material: str        # Terre cuite, Plastique, etc.
    volume_liters: Optional[float] = 0.0
    purchase_price: Optional[float] = 0.0
    purchase_location: Optional[str] = ""
    purchase_date: Optional[str] = ""
    diameter_base: Optional[float] = None
    diameter_top: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    container_weight: Optional[float] = None
    container_brand: Optional[str] = ""
    location_type: Optional[str] = ""

# --- INITIALISATION ET MIGRATION ---
def init_db():
    conn = get_db()
    # Table principale
    conn.execute('''CREATE TABLE IF NOT EXISTS plants
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name_fr TEXT, name_en TEXT, name_sci TEXT, variety TEXT, plant_type TEXT,
                  is_edible BOOLEAN DEFAULT 0, edibility_detail TEXT, is_fruit BOOLEAN DEFAULT 0, is_vegetable BOOLEAN DEFAULT 0,
                  hardiness TEXT, exposure TEXT, soil_humidity TEXT, soil_details TEXT, height TEXT,
                  flowering_months TEXT, harvest_months TEXT, pruning_months TEXT, fertilizing_months TEXT,
                  pruning_comment TEXT, fertilizing_comment TEXT, harvest_comment TEXT,
                  location_type TEXT, location_zone TEXT, location_detail TEXT, container TEXT,
                  date_plantation TEXT, date_last_fertilisation TEXT, date_last_taille TEXT, last_repotting_date TEXT,
                  presentation TEXT, notes TEXT, web_link TEXT,
                  id_confidence INTEGER, melliferous_score INTEGER, toxicity_score INTEGER, toxicity_detail TEXT,
                  flower_color TEXT, foliage_persistence TEXT,
                  purchase_location TEXT, purchase_price REAL, purchase_date TEXT,
                  container_id INTEGER, tags TEXT, rating INTEGER, is_archived BOOLEAN DEFAULT 0, other_names TEXT)''')
    
    # Migration : Ajout des colonnes si elles manquent
    #new_cols = [
    #    ("rating", "INTEGER"),
    #    ("is_archived", "BOOLEAN DEFAULT 0"),
    #]
    #for col, ctype in new_cols:
    #    try:
    #        conn.execute(f"ALTER TABLE plants ADD COLUMN {col} {ctype}")
    #    except sqlite3.OperationalError:
    #        pass
    try:
        conn.execute("ALTER TABLE plants ADD COLUMN harvest_comment TEXT")
    except:
        pass


    # --- Migration des contenants ---
    new_cont_cols =[
        ("diameter_base", "REAL"), ("diameter_top", "REAL"), ("height", "REAL"),
        ("width", "REAL"), ("length", "REAL"), ("container_weight", "REAL"),
        ("container_brand", "TEXT"), ("location_type", "TEXT") 
    ]
    for col, ctype in new_cont_cols:
        try:
            conn.execute(f"ALTER TABLE containers ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    # Tables annexes (Photos et Paramètres)
    conn.execute('''CREATE TABLE IF NOT EXISTS photos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER, path TEXT, upload_date TEXT, is_main BOOLEAN)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  category TEXT, value TEXT)''')
    
    # Table principale contenants
    conn.execute("""
        CREATE TABLE IF NOT EXISTS containers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_type TEXT,
            name TEXT UNIQUE,
            color TEXT,
            material TEXT,
            volume_liters REAL,
            purchase_price REAL,
            purchase_location TEXT,
            purchase_date TEXT,
            diameter_base REAL,
            diameter_top REAL,
            height REAL,
            width REAL,
            length REAL,
            container_weight REAL,
            container_brand TEXT
        )
    """)

# Table pour les photos des contenants
    conn.execute("""
        CREATE TABLE IF NOT EXISTS container_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER,
            path TEXT,
            thumb_path TEXT,
            upload_date TEXT,
            is_main BOOLEAN DEFAULT 0,
            FOREIGN KEY(container_id) REFERENCES containers(id)
        )
    """)
    # MIGRATION : Ajout des miniatures et dates pour les contenants
    #try:
    #    conn.execute("ALTER TABLE container_photos ADD COLUMN thumb_path TEXT")
    #except:
    #    pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id INTEGER,
            action TEXT,
            date TEXT,
            notes TEXT,
            FOREIGN KEY(plant_id) REFERENCES plants(id)
        )
    """)

    # --- NOUVEAU : MIGRATION DES MOIS EN CHIFFRES ---
    try:
        cursor = conn.execute("SELECT id, flowering_months, harvest_months, pruning_months, fertilizing_months FROM plants")
        # On force le formatage sur 2 chiffres (01, 02) pour sécuriser les recherches SQL (LIKE %01%)
        M_MAP = {"Jan": "01", "Fév": "02", "Mar": "03", "Avr": "04", "Mai": "05", "Juin": "06", 
                 "Juil": "07", "Août": "08", "Sept": "09", "Oct": "10", "Nov": "11", "Déc": "12"}
        for row in cursor.fetchall():
            updated = False
            new_vals = []
            for col in["flowering_months", "harvest_months", "pruning_months", "fertilizing_months"]:
                val = row[col]
                if val:
                    for k, v in M_MAP.items():
                        val = val.replace(k, v)
                    if val != row[col]:
                        updated = True
                new_vals.append(val)
            if updated:
                conn.execute(
                    "UPDATE plants SET flowering_months=?, harvest_months=?, pruning_months=?, fertilizing_months=? WHERE id=?",
                    (new_vals[0], new_vals[1], new_vals[2], new_vals[3], row["id"])
                )
    except Exception as e:
        print("Erreur migration mois:", e)

    conn.commit()
    conn.close()

init_db()


# --- UTILS ---
def resize_image(image_file, max_side=4000):
    # Ouvrir l'image
    img = Image.open(image_file)
    
    # Calculer le ratio pour ne pas déformer
    w, h = img.size
    if max(w, h) > max_side:
        ratio = max_side / float(max(w, h))
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Convertir l'objet Image en bytes pour l'envoi
    img_byte_arr = io.BytesIO()
    # On sauvegarde en JPEG pour compresser un peu (tu peux garder PNG si besoin)
    img.save(img_byte_arr, format='JPEG', quality=70)
    return img_byte_arr.getvalue()


# --- ROUTES ---

@app.get("/plants/")
def list_plants():
    conn = get_db()
    # L'alias 'main_photo' est OBLIGATOIRE ici pour que d['main_photo'] fonctionne
    query = """
        SELECT p.*, ph.thumb_path as main_photo
        FROM plants p 
        LEFT JOIN photos ph ON p.id = ph.plant_id AND ph.is_main = 1
    """
    try:
        plants = conn.execute(query).fetchall()
        results = []
        base_url = os.getenv("HOST_URL", "http://localhost:8000")
        for p in plants:
            d = dict(p)
            # Sécurité : on vérifie si la clé existe avant de l'utiliser
            if d.get('main_photo'):
                filename = d['main_photo'].split('/')[-1]
                d['image_url'] = f"{base_url}/uploads/{filename}"
            else:
                d['image_url'] = None
            results.append(d)
        return results
    finally:
        conn.close()


@app.get("/plants/{plant_id}")
def get_single_plant(plant_id: int):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None # Si l'ID n'existe pas

@app.post("/plants/")
def add_plant(p: Plant):
    conn = get_db()
    cursor = conn.execute('''INSERT INTO plants 
        (name_fr, name_en, name_sci, plant_type, hardiness, height, flowering_months, harvest_months, 
         pruning_months, fertilizing_months, pruning_comment, fertilizing_comment, harvest_comment,
         location_type, location_zone, location_detail, container, is_fruit, is_vegetable,
         date_plantation, date_last_fertilisation, date_last_taille, presentation, notes,
         web_link, id_confidence, melliferous_score, toxicity_score, toxicity_detail,
         is_edible, edibility_detail, flower_color, foliage_persistence, exposure,
         soil_humidity, soil_details, purchase_location, purchase_price, purchase_date, last_repotting_date,
          container_id, variety, tags, rating, is_archived, other_names) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
        (p.name_fr, p.name_en, p.name_sci, p.plant_type, p.hardiness, p.height, p.flowering_months, p.harvest_months,
         p.pruning_months, p.fertilizing_months, p.pruning_comment, p.fertilizing_comment, p.harvest_comment,
         p.location_type, p.location_zone, p.location_detail, p.container, p.is_fruit, p.is_vegetable,
         p.date_plantation, p.date_last_fertilisation, p.date_last_taille, p.presentation, p.notes,
         p.web_link, p.id_confidence, p.melliferous_score, p.toxicity_score, p.toxicity_detail,
         p.is_edible, p.edibility_detail, p.flower_color, p.foliage_persistence, p.exposure,
         p.soil_humidity, p.soil_details, p.purchase_location, p.purchase_price, p.purchase_date, p.last_repotting_date, 
         p.container_id, p.variety, p.tags, p.rating, p.is_archived, p.other_names))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id}

@app.delete("/plants/{plant_id}")
def delete_plant(plant_id: int):
    conn = get_db()
    try:
        # 1. NOUVEAU : Supprimer physiquement les fichiers photos du serveur
        photos = conn.execute("SELECT path, thumb_path FROM photos WHERE plant_id = ?", (plant_id,)).fetchall()
        for photo in photos:
            if photo['path'] and os.path.exists(photo['path']):
                os.remove(photo['path'])
            if photo['thumb_path'] and os.path.exists(photo['thumb_path']):
                os.remove(photo['thumb_path'])

        # 2. Supprimer les références aux photos dans la DB
        conn.execute("DELETE FROM photos WHERE plant_id = ?", (plant_id,))
        
        # 3. Supprimer la plante
        cursor = conn.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Plante non trouvée")
            
        conn.commit()
        return {"message": "Plante et photos supprimées avec succès"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/plants/{plant_id}")
def update_plant(plant_id: int, p: Plant):
    conn = get_db()
    
    # 1. Mise à jour normale de la plante ciblée
    conn.execute('''UPDATE plants SET 
        name_fr=?, name_en=?, name_sci=?, plant_type=?, hardiness=?, height=?, 
        flowering_months=?, harvest_months=?, pruning_months=?, fertilizing_months=?,
        pruning_comment=?, fertilizing_comment=?, harvest_comment=?,
        location_type=?, location_zone=?, location_detail=?, container=?, 
        is_fruit=?, is_vegetable=?,
        date_plantation=?, date_last_fertilisation=?, date_last_taille=?,
        presentation=?, notes=?, web_link=?, id_confidence=?, melliferous_score=?, toxicity_score=?, toxicity_detail=?,
        is_edible=?, edibility_detail=?, flower_color=?, foliage_persistence=?, exposure=?,
        soil_humidity=?, soil_details=?, purchase_location=?, purchase_price=?, purchase_date=?, last_repotting_date=?, 
        container_id=?, variety=?, tags=?, rating=?, is_archived=?, other_names=?
        WHERE id=?''',
        (p.name_fr, p.name_en, p.name_sci, p.plant_type, p.hardiness, p.height, 
         p.flowering_months, p.harvest_months, p.pruning_months, p.fertilizing_months,
         p.pruning_comment, p.fertilizing_comment, p.harvest_comment,
         p.location_type, p.location_zone, p.location_detail, p.container, 
         p.is_fruit, p.is_vegetable,
         p.date_plantation, p.date_last_fertilisation, p.date_last_taille,
         p.presentation, p.notes,
         p.web_link, p.id_confidence, p.melliferous_score, p.toxicity_score, p.toxicity_detail,
         p.is_edible, p.edibility_detail, p.flower_color, p.foliage_persistence, p.exposure,
         p.soil_humidity, p.soil_details, p.purchase_location, p.purchase_price, p.purchase_date, p.last_repotting_date,
         p.container_id, p.variety, p.tags, p.rating, p.is_archived, p.other_names, plant_id))
         
    # 2. SYNCHRONISATION AUTOMATIQUE DES EXEMPLAIRES IDENTIQUES
    # On met à jour les champs botaniques, calendriers et infos communes des autres plantes 
    # ayant le même Nom FR ET la même Variété.
    # On exclut sciemment : id_confidence, l'emplacement, l'achat, l'historique et les photos.
    safe_variety = p.variety or ""
    conn.execute('''UPDATE plants SET 
        name_en=?, name_sci=?, plant_type=?, hardiness=?, height=?, 
        flowering_months=?, harvest_months=?, pruning_months=?, fertilizing_months=?,
        pruning_comment=?, fertilizing_comment=?, harvest_comment=?,
        is_fruit=?, is_vegetable=?,
        presentation=?, web_link=?, melliferous_score=?, toxicity_score=?, toxicity_detail=?,
        is_edible=?, edibility_detail=?, flower_color=?, foliage_persistence=?, exposure=?,
        soil_humidity=?, soil_details=?, tags=?, other_names=?
        WHERE name_fr=? AND IFNULL(variety, "")=? AND id!=?''',
        (p.name_en, p.name_sci, p.plant_type, p.hardiness, p.height, 
         p.flowering_months, p.harvest_months, p.pruning_months, p.fertilizing_months,
         p.pruning_comment, p.fertilizing_comment, p.harvest_comment,
         p.is_fruit, p.is_vegetable,
         p.presentation, p.web_link, p.melliferous_score, p.toxicity_score, p.toxicity_detail,
         p.is_edible, p.edibility_detail, p.flower_color, p.foliage_persistence, p.exposure,
         p.soil_humidity, p.soil_details, p.tags, 
         p.name_fr, p.other_names, safe_variety, plant_id))
         
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.get("/plants/search/")
def search_plants(
    name: Optional[str]=None,
    plant_type: Optional[str]=None,
    location_type: Optional[str]=None,
    container: Optional[str]=None,
    flowering_month: Optional[str]=None,
    harvest_month: Optional[str]=None,
    pruning_month: Optional[str]=None,
    fertilizing_month: Optional[str]=None,
    is_fruit: Optional[bool] = None,
    is_vegetable: Optional[bool] = None,
    tags: Optional[str] = None
):
    conn = get_db()
    query = "SELECT * FROM plants WHERE 1=1"
    params = []
    if name:
        query += " AND (name_fr LIKE ? OR name_sci LIKE ? OR name_en LIKE ? OR other_names LIKE ?)"
        params.extend([f"%{name}%", f"%{name}%", f"%{name}%", f"%{name}%"])
    if plant_type:
        query += " AND plant_type LIKE ?"
        params.append(f"%{plant_type}%")
    if tags:
        query += " AND tags LIKE ?"
        params.append(f"%{tags}%")
    if location_type:
        query += " AND location_type = ?"
        params.append(location_type)
    if is_fruit:
        query += " AND is_fruit = ?"
        params.append(is_fruit)
    if is_vegetable:
        query += " AND is_vegetable = ?"
        params.append(is_vegetable)
    if container:
        query += " AND container = ?"
        params.append(container)
    if flowering_month:
        query += " AND flowering_months LIKE ?"
        params.append(f"%{flowering_month}%")
    if harvest_month:
        query += " AND harvest_months LIKE ?"
        params.append(f"%{harvest_month}%")
    if pruning_month:
        query += " AND pruning_months LIKE ?"
        params.append(f"%{pruning_month}%")
    if fertilizing_month:
        query += " AND fertilizing_months LIKE ?"
        params.append(f"%{fertilizing_month}%")
    
    try:
        results = conn.execute(query, params).fetchall()
        # On transforme en dictionnaire pour être sûr d'envoyer du JSON propre
        return [dict(r) for r in results]
    except Exception as e:
        print(f"Erreur Recherche: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

#####################################################################################
########################        PHOTOS                       ########################
#####################################################################################

# --- FONCTION UTILITAIRE POUR LE CROP CARRÉ ---
def create_square_thumbnail(source_path, size=(300, 300)):
    """Crée une version carrée centrée de l'image."""
    with Image.open(source_path) as img:
        # ImageOps.fit gère le crop centré automatiquement pour remplir le carré
        thumbnail = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        
        # On définit le nom du fichier miniature : "photo_thumb.jpg"
        ext = source_path.split('.')[-1]
        base_path = source_path.rsplit('.', 1)[0]
        thumb_path = f"{base_path}_thumb.{ext}"
        
        thumbnail.save(thumb_path)
        return thumb_path

@app.put("/photos/{photo_id}/main")
def set_main_photo(photo_id: int, plant_id: int):
    conn = get_db()
    try:
        # 1. On remet tout à zéro pour cette plante
        conn.execute("UPDATE photos SET is_main = 0 WHERE plant_id = ?", (plant_id,))
        # 2. On définit la nouvelle photo principale
        conn.execute("UPDATE photos SET is_main = 1 WHERE id = ?", (photo_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/plants/{plant_id}/photos/")
def get_photos(plant_id: int):
    conn = get_db()
    # On trie par date de manière descendante (DESC)
    cursor = conn.execute(
        "SELECT * FROM photos WHERE plant_id = ? ORDER BY upload_date DESC", 
        (plant_id,)
    )
    photos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return photos


@app.post("/plants/{plant_id}/photos/")
async def add_photo(
    plant_id: int,
    file: UploadFile = File(...), 
    date: str = Form(None)
):
    # 1. Lire le contenu du fichier envoyé
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    # 2. Redimensionnement (Max 4000px sur le plus grand côté)
    max_side = 4000
    w, h = image.size
    if max(w, h) > max_side:
        ratio = max_side / float(max(w, h))
        new_size = (int(w * ratio), int(h * ratio))
        # On utilise LANCZOS pour la qualité
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # 3. Sauvegarder l'image optimisée
    file_path = f"uploads/{file.filename}"
    # On force la conversion en RGB si c'est un PNG avec transparence pour sauvegarder en JPEG
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    image.save(file_path, "JPEG", quality=75, optimize=True)
    
    # 4. CRÉATION DE LA MINIATURE CARRÉE (ton code existant)
    try:
        thumb_path = create_square_thumbnail(file_path)
    except Exception as e:
        print(f"Erreur thumbnail: {e}")
        thumb_path = file_path 

    # Si aucune date n'est fournie par le front, on prend celle du jour
    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
    # 5. Enregistrement en base de données
    conn = get_db()
    conn.execute(
        "INSERT INTO photos (plant_id, path, thumb_path, is_main, upload_date) VALUES (?, ?, ?, 0, ?)",
        (plant_id, file_path, thumb_path, date)
    )
    conn.commit()
    conn.close()
    
    return {"status": "Photo ajoutée et redimensionnée"}

@app.delete("/photos/{photo_id}")
def delete_photo(photo_id: int):
    conn = get_db()
    # 1. On récupère les chemins des deux fichiers avant de supprimer l'entrée
    photo = conn.execute(
        "SELECT path, thumb_path FROM photos WHERE id = ?", 
        (photo_id,)
    ).fetchone()
    
    if not photo:
        conn.close()
        raise HTTPException(status_code=404, detail="Photo non trouvée")

    try:
        # 2. Suppression de la base de données
        conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        conn.commit()

        # 3. Suppression physique des fichiers sur le disque
        # On supprime l'original
        if photo['path'] and os.path.exists(photo['path']):
            os.remove(photo['path'])
        
        # On supprime la miniature carrée (le thumb)
        if photo['thumb_path'] and os.path.exists(photo['thumb_path']):
            os.remove(photo['thumb_path'])

        return {"status": "success", "message": "Fichiers et entrée supprimés"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur suppression: {str(e)}")
    finally:
        conn.close()


#####################################################################################
#####################           CONTAINERS                   ########################
#####################################################################################

# Route pour CRÉER un contenant
@app.post("/containers/")
def create_container(container: Container):
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO containers (name, container_type, material, color, volume_liters, purchase_price, 
           purchase_location, purchase_date, diameter_base, diameter_top, height, width, length, 
           container_weight, container_brand, location_type) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (container.name, container.container_type, container.material, container.color, container.volume_liters, 
         container.purchase_price, container.purchase_location, container.purchase_date,
         container.diameter_base, container.diameter_top, container.height, container.width, container.length,
         container.container_weight, container.container_brand, container.location_type)
    )
    conn.commit()
    return {"id": cursor.lastrowid, **container.dict()}

@app.get("/containers/")
def list_containers():
    conn = get_db()
    query = """
        SELECT c.*, cp.thumb_path as main_photo,
               (SELECT COUNT(*) FROM plants p WHERE p.container_id = c.id AND p.is_archived = 0) as plant_count
        FROM containers c
        LEFT JOIN container_photos cp ON c.id = cp.container_id AND cp.is_main = 1
    """
    cursor = conn.execute(query)
    results =[]
    base_url = os.getenv("HOST_URL", "http://localhost:8000")
    for row in cursor.fetchall():
        d = dict(row)
        if d.get('main_photo'):
            filename = d['main_photo'].split('/')[-1]
            d['image_url'] = f"{base_url}/uploads/{filename}"
        else:
            d['image_url'] = None
        results.append(d)
    conn.close()
    return results

# Route pour MODIFIER un contenant
@app.put("/containers/{container_id}")
def update_container(container_id: int, container: Container):
    conn = get_db()
    conn.execute(
        """UPDATE containers SET name=?, container_type=?, material=?, color=?, volume_liters=?, 
           purchase_price=?, purchase_location=?, purchase_date=?,
           diameter_base=?, diameter_top=?, height=?, width=?, length=?, container_weight=?, container_brand=?,
           location_type=?
           WHERE id=?""",
        (container.name, container.container_type, container.material, container.color, container.volume_liters, 
         container.purchase_price, container.purchase_location, container.purchase_date,
         container.diameter_base, container.diameter_top, container.height, container.width, container.length,
         container.container_weight, container.container_brand, container.location_type, container_id)
    )
    conn.commit()
    return {"status": "updated"}

# Route pour supprimer un contenant
@app.delete("/containers/{container_id}")
def delete_container(container_id: int):
    conn = get_db()
    try:
        # 1. On supprime physiquement les photos associées à ce contenant
        photos = conn.execute("SELECT path, thumb_path FROM container_photos WHERE container_id = ?", (container_id,)).fetchall()
        for photo in photos:
            if photo['path'] and os.path.exists(photo['path']): os.remove(photo['path'])
            if photo['thumb_path'] and os.path.exists(photo['thumb_path']): os.remove(photo['thumb_path'])
        
        # 2. On supprime les entrées photos de la base
        conn.execute("DELETE FROM container_photos WHERE container_id = ?", (container_id,))
        
        # 3. On supprime le contenant
        cursor = conn.execute("DELETE FROM containers WHERE id = ?", (container_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contenant non trouvé")
            
        # 4. (Optionnel) On libère les plantes qui utilisaient ce contenant
        conn.execute("UPDATE plants SET container_id = NULL, container = '-' WHERE container_id = ?", (container_id,))
        
        conn.commit()
        return {"message": "Contenant supprimé avec succès"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- ROUTES POUR LES PHOTOS DES CONTENANTS ---

@app.get("/containers/{container_id}/photos/")
def get_container_photos(container_id: int):
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM container_photos WHERE container_id = ? ORDER BY upload_date DESC", 
        (container_id,)
    )
    photos =[dict(row) for row in cursor.fetchall()]
    conn.close()
    return photos

@app.post("/containers/{container_id}/photos/")
async def add_container_photo(
    container_id: int,
    file: UploadFile = File(...), 
    date: str = Form(None)
):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    max_side = 4000
    w, h = image.size
    if max(w, h) > max_side:
        ratio = max_side / float(max(w, h))
        new_size = (int(w * ratio), int(h * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    file_path = f"uploads/c_{file.filename}"
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(file_path, "JPEG", quality=75, optimize=True)
    
    try:
        thumb_path = create_square_thumbnail(file_path)
    except Exception as e:
        print(f"Erreur thumbnail: {e}")
        thumb_path = file_path 

    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
        
    conn = get_db()
    conn.execute(
        "INSERT INTO container_photos (container_id, path, thumb_path, is_main, upload_date) VALUES (?, ?, ?, 0, ?)",
        (container_id, file_path, thumb_path, date)
    )
    conn.commit()
    conn.close()
    return {"status": "Photo ajoutée !"}

@app.put("/container_photos/{photo_id}/main")
def set_main_container_photo(photo_id: int, container_id: int):
    conn = get_db()
    try:
        conn.execute("UPDATE container_photos SET is_main = 0 WHERE container_id = ?", (container_id,))
        conn.execute("UPDATE container_photos SET is_main = 1 WHERE id = ?", (photo_id,))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/container_photos/{photo_id}")
def delete_container_photo(photo_id: int):
    conn = get_db()
    photo = conn.execute("SELECT path, thumb_path FROM container_photos WHERE id = ?", (photo_id,)).fetchone()
    if not photo:
        conn.close()
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    try:
        conn.execute("DELETE FROM container_photos WHERE id = ?", (photo_id,))
        conn.commit()
        if photo['path'] and os.path.exists(photo['path']): os.remove(photo['path'])
        if photo['thumb_path'] and os.path.exists(photo['thumb_path']): os.remove(photo['thumb_path'])
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
    finally:
        conn.close()


#####################################################################################
###################             AGENDA                       ########################
#####################################################################################

@app.get("/plants/agenda/{month_num}")
def get_plants_by_month(month_num: str):
    conn = get_db()
    
    # 1. Requête de base (Cherche '%01%' par exemple)
    # --- MODIFICATION : Ajout de la variété, de l'emplacement et du contenant ---
    query = """
        SELECT id, name_fr, variety, location_type, location_zone, location_detail, container,
               pruning_months, fertilizing_months, harvest_months,
               flowering_months, date_last_taille, date_last_fertilisation,
               pruning_comment, fertilizing_comment, harvest_comment
        FROM plants
        WHERE pruning_months LIKE ? 
           OR fertilizing_months LIKE ? 
           OR harvest_months LIKE ?
           OR flowering_months LIKE ?
    """
    search_term = f"%{month_num}%"
    cursor = conn.execute(query, (search_term, search_term, search_term, search_term))
    results =[dict(row) for row in cursor.fetchall()]

    try:
        from datetime import datetime
        current_year = datetime.now().year

        # Fonction modifiée pour extraire les entiers depuis "01, 02, 12"
        def get_block_indices(target_m_str, months_str):
            if not months_str: return set()
            active_months = {int(m.strip()) for m in months_str.split(',') if m.strip().isdigit()}
            target_m = int(target_m_str)
            if target_m not in active_months: return set()
            
            block = {target_m}
            curr = target_m
            while True:
                prev_m = curr - 1 if curr > 1 else 12
                if prev_m in active_months and prev_m not in block:
                    block.add(prev_m)
                    curr = prev_m
                else: break
            curr = target_m
            while True:
                next_m = curr + 1 if curr < 12 else 1
                if next_m in active_months and next_m not in block:
                    block.add(next_m)
                    curr = next_m
                else: break
            return block

        for p in results:
            p['done_actions'] =[]
            
            taille_block = get_block_indices(month_num, p.get('pruning_months', ''))
            if taille_block:
                d_str = p.get('date_last_taille')
                if d_str:
                    try:
                        d = datetime.strptime(d_str.split('T')[0].split(' ')[0], "%Y-%m-%d")
                        if d.year == current_year and d.month in taille_block: p['done_actions'].append('taille')
                    except: pass
            
            engrais_block = get_block_indices(month_num, p.get('fertilizing_months', ''))
            if engrais_block:
                d_str = p.get('date_last_fertilisation')
                if d_str:
                    try:
                        d = datetime.strptime(d_str.split('T')[0].split(' ')[0], "%Y-%m-%d")
                        if d.year == current_year and d.month in engrais_block: p['done_actions'].append('engrais')
                    except: pass
            
            recolte_block = get_block_indices(month_num, p.get('harvest_months', ''))
            if recolte_block:
                log_cursor = conn.execute(
                    "SELECT date FROM logs WHERE plant_id = ? AND action = 'récolte' AND date LIKE ?", 
                    (p['id'], f"{current_year}-%")
                )
                for row in log_cursor.fetchall():
                    try:
                        ld_date = datetime.strptime(row['date'].split('T')[0].split(' ')[0], "%Y-%m-%d")
                        if ld_date.month in recolte_block:
                            p['done_actions'].append('récolte')
                            break
                    except: pass

    except Exception as e:
        for p in results:
            if 'done_actions' not in p: p['done_actions'] =[]
        print(f"Erreur logs/agenda : {e}") 

    conn.close()
    return results

@app.post("/logs/")
def create_log(data: dict):
    conn = get_db()

    # 1. On inscrit l'action dans le journal d'historique (logs)
    conn.execute(
        "INSERT INTO logs (plant_id, action, date, notes) VALUES (?, ?, ?, ?)",
        (data['plant_id'], data['action'], data['date'], data.get('notes', ''))
    )
    # 2. AUTOMATISATION : On met à jour la vraie fiche de la plante !
    action = data.get('action', '').lower()
    if action == "taille":
        conn.execute("UPDATE plants SET date_last_taille = ? WHERE id = ?", (data['date'], data['plant_id']))
    elif action == "engrais":
        conn.execute("UPDATE plants SET date_last_fertilisation = ? WHERE id = ?", (data['date'], data['plant_id']))

    conn.commit()
    conn.close()
    return {"status": "logged"}

#####################################################################################
###################            SETTINGS                       ########################
#####################################################################################

@app.get("/settings/{category}")
def get_settings(category: str):
    conn = get_db()
    opts = conn.execute("SELECT * FROM settings WHERE category=? ORDER BY value COLLATE NOCASE ASC", (category,)).fetchall()
    conn.close()
    return [dict(o) for o in opts]

@app.post("/settings/")
def add_setting(opt: dict):
    conn = get_db()
    conn.execute("INSERT INTO settings (category, value) VALUES (?,?)", (opt['category'], opt['value']))
    conn.commit()
    conn.close()
    return {"status": "added"}

@app.delete("/settings/{setting_id}")
def delete_setting(setting_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM settings WHERE id = ?", (setting_id,))
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        conn.rollback()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/settings/{setting_id}")
def update_setting(setting_id: int, data: SettingUpdate):
    conn = get_db()
    try:
        # 1. On modifie le paramètre lui-même
        conn.execute("UPDATE settings SET value = ? WHERE id = ?", (data.new_value, setting_id))
        
        # 2. On répercute sur toutes les plantes !
        cat = data.category
        old = data.old_value
        new = data.new_value
        
        # Pour les paramètres uniques
        if cat in["location_type", "location_zone", "container"]:
            conn.execute(f"UPDATE plants SET {cat} = ? WHERE {cat} = ?", (new, old))
            
        # Pour les paramètres à choix multiples (plant_type, tags) séparés par des virgules
        elif cat in["plant_type", "tags"]:
            plants_to_update = conn.execute(f"SELECT id, {cat} FROM plants WHERE {cat} LIKE ?", (f"%{old}%",)).fetchall()
            for p in plants_to_update:
                # On découpe en liste, on remplace l'ancien mot précis, et on recrée la phrase
                items =[x.strip() for x in str(p[cat]).split(",") if x.strip()]
                updated_items =[new if x == old else x for x in items]
                new_val = ", ".join(updated_items)
                conn.execute(f"UPDATE plants SET {cat} = ? WHERE id = ?", (new_val, p["id"]))
        
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Fonction d'export de la base
@app.get("/plants/export/")
def export_plants():
    conn = get_db()
    # Cette requête récupère tout et groupe les chemins de photos par plante
    query = """
        SELECT p.*, GROUP_CONCAT(ph.path, ', ') as photo_paths
        FROM plants p
        LEFT JOIN photos ph ON p.id = ph.plant_id
        GROUP BY p.id
    """
    try:
        results = conn.execute(query).fetchall()
        return [dict(r) for r in results]
    finally:
        conn.close()

@app.post("/plants/import/")
def import_plants(data: List[dict]):
    conn = get_db()
    try:
        for item in data:
            # 1. Insertion de la plante
            cursor = conn.execute('''INSERT INTO plants 
                (name_fr, name_en, name_sci, plant_type, hardiness, height, flowering_months, harvest_months, 
                 pruning_months, fertilizing_months, pruning_comment, fertilizing_comment, harvest_comment,
                 location_type, location_zone, location_detail, container, is_fruit, is_vegetable,
                 date_plantation, date_last_fertilisation, date_last_taille, presentation, notes,
                 web_link, id_confidence, melliferous_score, toxicity_score, toxicity_detail, is_edible,
                 edibility_detail, flower_color, foliage_persistence, exposure, soil_humidity, soil_details,
                 purchase_location, purchase_price, purchase_date, last_repotting_date, container_id,
                 variety, tags, rating, is_archived, other_names
                 ) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                (item.get('name_fr'), item.get('name_en'), item.get('name_sci'), item.get('plant_type'), item.get('hardiness'), 
                 item.get('height'), item.get('flowering_months'), item.get('harvest_months'),
                 item.get('pruning_months'), item.get('fertilizing_months'), item.get('pruning_comment'), 
                 item.get('fertilizing_comment'), item.get('harvest_comment'), item.get('location_type'), item.get('location_zone'), 
                 item.get('location_detail'), item.get('container'), item.get('is_fruit', 0), 
                 item.get('is_vegetable', 0), item.get('date_plantation'), 
                 item.get('date_last_fertilisation'), item.get('date_last_taille'),
                 item.get('presentation'),item.get('notes'), item.get('web_link'), item.get('id_confidence'),
                 item.get('melliferous_score'), item.get('toxicity_score'), item.get('toxicity_detail'),
                 item.get('is_edible'), item.get('edibility_detail'), item.get('flower_color'),
                 item.get('foliage_persistence'), item.get('exposure'), item.get('soil_humidity'), item.get('soil_details'),
                 item.get('purchase_location'), item.get('purchase_price'), item.get('purchase_date'),
                 item.get('last_repotting_date'), item.get('container_id'), item.get('variety'), item.get('tags'),
                 item.get('rating'), item.get('is_archived', 0), item.get('other_names')
                 ))
            
            plant_id = cursor.lastrowid

            # 2. Gestion des chemins de photos (si présents dans la colonne photo_paths)
            if item.get('photo_paths'):
                paths = [p.strip() for p in str(item['photo_paths']).split(',')]
                for i, p in enumerate(paths):
                    # On insère le chemin. Note: le fichier physique doit déjà exister dans /uploads
                    # Sinon, l'image ne s'affichera pas, mais l'entrée sera là.
                    conn.execute(
                        "INSERT INTO photos (plant_id, path, is_main) VALUES (?, ?, ?)",
                        (plant_id, p, 1 if i == 0 else 0)
                    )
        
        conn.commit()
        return {"status": "success", "imported": len(data)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- EXPORT / IMPORT CONTENANTS ---

@app.get("/containers/export/")
def export_containers():
    conn = get_db()
    query = """
        SELECT c.*, GROUP_CONCAT(cp.path, ', ') as photo_paths
        FROM containers c
        LEFT JOIN container_photos cp ON c.id = cp.container_id
        GROUP BY c.id
    """
    try:
        results = conn.execute(query).fetchall()
        return [dict(r) for r in results]
    finally:
        conn.close()

@app.post("/containers/import/")
def import_containers(data: List[dict]):
    conn = get_db()
    try:
        for item in data:
            cursor = conn.execute('''INSERT INTO containers 
                (container_type, name, color, material, volume_liters, purchase_price, 
                 purchase_location, purchase_date, diameter_base, diameter_top, height, 
                 width, length, container_weight, container_brand) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                (item.get('container_type'), item.get('name'), item.get('color'), item.get('material'), 
                 item.get('volume_liters'), item.get('purchase_price'), item.get('purchase_location'), 
                 item.get('purchase_date'), item.get('diameter_base'), item.get('diameter_top'), 
                 item.get('height'), item.get('width'), item.get('length'), 
                 item.get('container_weight'), item.get('container_brand'), item.get('location_type')
                 ))
            
            container_id = cursor.lastrowid

            if item.get('photo_paths'):
                paths = [p.strip() for p in str(item['photo_paths']).split(',')]
                for i, p in enumerate(paths):
                    conn.execute(
                        "INSERT INTO container_photos (container_id, path, is_main) VALUES (?, ?, ?)",
                        (container_id, p, 1 if i == 0 else 0)
                    )
        conn.commit()
        return {"status": "success", "imported": len(data)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- BACKUP ET RESTAURATION DES PHOTOS ---

@app.get("/backup/photos/")
def backup_photos():
    zip_filename = "photos_backup.zip"
    # Crée une archive de tout le dossier 'uploads'
    shutil.make_archive(zip_filename.replace('.zip', ''), 'zip', UPLOAD_DIR)
    return FileResponse(zip_filename, media_type="application/zip", filename=zip_filename)

@app.post("/restore/photos/")
async def restore_photos(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Veuillez fournir un fichier .zip")
    
    zip_path = "temp_restore.zip"
    # On sauvegarde le zip uploadé temporairement
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # On l'extrait dans le dossier uploads, ce qui fusionne et écrase les fichiers existants
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_DIR)
        os.remove(zip_path) # Nettoyage
        return {"status": "success", "message": "Photos restaurées avec succès !"}
    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la restauration: {str(e)}")


@app.delete("/backup/cleanup_orphans/")
def cleanup_orphaned_photos():
    conn = get_db()
    try:
        valid_filenames = set()
        
        # 1. Lister tous les noms de fichiers légitimes (Plantes)
        for row in conn.execute("SELECT path, thumb_path FROM photos").fetchall():
            if row['path']: valid_filenames.add(os.path.basename(row['path']))
            if row['thumb_path']: valid_filenames.add(os.path.basename(row['thumb_path']))
            
        # 2. Lister tous les noms de fichiers légitimes (Contenants)
        for row in conn.execute("SELECT path, thumb_path FROM container_photos").fetchall():
            if row['path']: valid_filenames.add(os.path.basename(row['path']))
            if row['thumb_path']: valid_filenames.add(os.path.basename(row['thumb_path']))
            
        # 3. Parcourir le vrai dossier 'uploads' et supprimer les intrus
        deleted_count = 0
        for filename in os.listdir(UPLOAD_DIR):
            if filename not in valid_filenames:
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
