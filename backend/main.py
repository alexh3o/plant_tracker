from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image, ImageOps
import sqlite3
import os
import shutil

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
    hardiness: Optional[str] = ""
    height: Optional[str] = ""
    flowering_months: Optional[str] = ""
    harvest_months: Optional[str] = ""
    pruning_months: Optional[str] = ""      # Nouveau
    fertilizing_months: Optional[str] = ""  # Nouveau
    pruning_comment: Optional[str] = ""     # Nouveau
    fertilizing_comment: Optional[str] = "" # Nouveau
    location_type: Optional[str] = ""
    location_zone: Optional[str] = ""
    location_detail: Optional[str] = ""
    container: Optional[str] = ""
    is_fruit: bool = False
    is_vegetable: bool = False

# --- INITIALISATION ET MIGRATION ---
def init_db():
    conn = get_db()
    # Table principale
    conn.execute('''CREATE TABLE IF NOT EXISTS plants
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name_fr TEXT, name_en TEXT, name_sci TEXT, 
                  hardiness TEXT, height TEXT,
                  flowering_months TEXT, location_type TEXT, 
                  location_zone TEXT, location_detail TEXT, 
                  container TEXT)''')
    
    # Migration : Ajout des colonnes si elles manquent
    new_cols = [
        ("harvest_months", "TEXT"),
        ("is_fruit", "BOOLEAN DEFAULT 0"),
        ("is_vegetable", "BOOLEAN DEFAULT 0"),
        ("pruning_months", "TEXT"),
        ("fertilizing_months", "TEXT"),
        ("pruning_comment", "TEXT"),
        ("fertilizing_comment", "TEXT")
    ]
    for col, ctype in new_cols:
        try:
            conn.execute(f"ALTER TABLE plants ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    # Tables annexes (Photos et Paramètres)
    conn.execute('''CREATE TABLE IF NOT EXISTS photos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER, path TEXT, upload_date TEXT, is_main BOOLEAN)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  category TEXT, value TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

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
        for p in plants:
            d = dict(p)
            # Sécurité : on vérifie si la clé existe avant de l'utiliser
            if d.get('main_photo'):
                filename = d['main_photo'].split('/')[-1]
                d['image_url'] = f"http://192.168.1.105:8000/uploads/{filename}"
            else:
                d['image_url'] = None
            results.append(d)
        return results
    finally:
        conn.close()

@app.post("/plants/")
def add_plant(p: Plant):
    conn = get_db()
    cursor = conn.execute('''INSERT INTO plants 
        (name_fr, name_en, name_sci, hardiness, height, flowering_months, harvest_months, 
         pruning_months, fertilizing_months, pruning_comment, fertilizing_comment,
         location_type, location_zone, location_detail, container, is_fruit, is_vegetable) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
        (p.name_fr, p.name_en, p.name_sci, p.hardiness, p.height, p.flowering_months, p.harvest_months,
         p.pruning_months, p.fertilizing_months, p.pruning_comment, p.fertilizing_comment,
         p.location_type, p.location_zone, p.location_detail, p.container, p.is_fruit, p.is_vegetable))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id}

@app.put("/plants/{plant_id}")
def update_plant(plant_id: int, p: Plant):
    conn = get_db()
    conn.execute('''UPDATE plants SET 
        name_fr=?, name_en=?, name_sci=?, hardiness=?, height=?, 
        flowering_months=?, harvest_months=?, pruning_months=?, fertilizing_months=?,
        pruning_comment=?, fertilizing_comment=?,
        location_type=?, location_zone=?, location_detail=?, container=?, 
        is_fruit=?, is_vegetable=? WHERE id=?''',
        (p.name_fr, p.name_en, p.name_sci, p.hardiness, p.height, 
         p.flowering_months, p.harvest_months, p.pruning_months, p.fertilizing_months,
         p.pruning_comment, p.fertilizing_comment,
         p.location_type, p.location_zone, p.location_detail, p.container, 
         p.is_fruit, p.is_vegetable, plant_id))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.get("/plants/search/")
def search_plants(
    name: Optional[str]=None,
    location_type: Optional[str]=None,
    container: Optional[str]=None,
    flowering_month: Optional[str]=None,
    harvest_month: Optional[str]=None,
    pruning_month: Optional[str]=None,
    fertilizing_month: Optional[str]=None,
    is_fruit: Optional[bool] = None,
    is_vegetable: Optional[bool] = None
):
    conn = get_db()
    query = "SELECT * FROM plants WHERE 1=1"
    params = []
    if name:
        query += " AND (name_fr LIKE ? OR name_sci LIKE ?)"
        params.extend([f"%{name}%", f"%{name}%"])
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

# --- ROUTES PHOTOS & SETTINGS (Gardées telles quelles) ---

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
    photos = conn.execute("SELECT * FROM photos WHERE plant_id=?", (plant_id,)).fetchall()
    conn.close()
    return [dict(p) for p in photos]

@app.post("/plants/{plant_id}/photos/")
async def add_photo(plant_id: int, file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # CRÉATION DE LA MINIATURE CARRÉE
    try:
        thumb_path = create_square_thumbnail(file_path)
    except Exception as e:
        print(f"Erreur thumbnail: {e}")
        thumb_path = file_path # Repli sur l'original si échec

    conn = get_db()
    # On ajoute thumb_path dans une nouvelle colonne ou on l'utilise pour la liste
    conn.execute(
        "INSERT INTO photos (plant_id, path, thumb_path, is_main) VALUES (?, ?, ?, 0)",
        (plant_id, file_path, thumb_path)
    )
    conn.commit()
    conn.close()
    return {"status": "Photo ajoutée"}

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


@app.get("/settings/{category}")
def get_settings(category: str):
    conn = get_db()
    opts = conn.execute("SELECT * FROM settings WHERE category=?", (category,)).fetchall()
    conn.close()
    return [dict(o) for o in opts]

@app.post("/settings/")
def add_setting(opt: dict):
    conn = get_db()
    conn.execute("INSERT INTO settings (category, value) VALUES (?,?)", (opt['category'], opt['value']))
    conn.commit()
    conn.close()
    return {"status": "added"}
