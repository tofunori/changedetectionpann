# Guide des démonstrations PANN

Ce fichier clarifie quels scripts utilisent de **vraies** images satellites et lesquels utilisent des **simulations**.

---

## 🚨 Important: Vraies images vs Simulations

| Script | Type de données | Description |
|--------|----------------|-------------|
| `demo_visuelle.py` | **❌ SIMULATION** | Images artificielles générées avec numpy |
| `demo_avec_vraies_donnees.py` | **❌ SIMULATION** | Simulation "réaliste" mais toujours artificielle |
| `run_pann_vraies_images.py` | **✅ VRAIES IMAGES** | Lit de vrais fichiers GeoTIFF Sentinel-2/Landsat |

---

## ✅ Pour utiliser de VRAIES images satellites

### Étape 1: Télécharger les données

**Option A: Dataset RaVAEn (Recommandé)**

1. Accédez à: https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn
2. Téléchargez un événement (ex: `fires.zip`)
3. Extrayez dans `data/`:

```bash
mkdir -p data
unzip fires.zip -d data/
```

**Option B: Sentinel-2 via Copernicus**

Voir le guide complet dans `UTILISER_VRAIES_IMAGES.md`

### Étape 2: Installer les dépendances

```bash
pip install rasterio numpy matplotlib scipy
```

### Étape 3: Exécuter sur les vraies images

```bash
# Exemple avec une scène d'incendie
python3 run_pann_vraies_images.py \
    --scene data/fires/EONET_4766 \
    --band B08 \
    --pool-size 16 \
    --output resultats_vraie_scene.png
```

**Sortie:**
```
==================================================================
Modèle PANN - Détection de changements sur VRAIES images satellites
==================================================================

✓ rasterio disponible

📥 Chargement des images satellites...
📡 Pré-événement:
   Trouvé 4 image(s) pour la bande B08
   → Utilisation de la dernière: S2A_MSIL1C_20181027T184931_..._B08.tif
   • Dimensions: 10980×10980 pixels
   • Type: uint16
   • Valeurs: min=1, max=12453, mean=7234.5
   • CRS: EPSG:32610

📡 Post-événement:
   Trouvé 1 image(s) pour la bande B08
   → Utilisation de la première: S2A_MSIL1C_20181116T184921_..._B08.tif
   • Dimensions: 10980×10980 pixels
   • Type: uint16
   • Valeurs: min=1, max=11892, mean=6543.2
   • CRS: EPSG:32610

✓ Masque de vérité terrain: EONET_4766_post_fire.tif
   • Dimensions: (10980, 10980)
   • Valeurs uniques: [0 255]

🔧 Prétraitement...
  ✓ Normalisation log-transform
  ✓ Max pooling: (10980, 10980) → (686, 686)
  ✓ Signaux: 470596 entrées spatiales

🧠 Simulation du réseau PANN...
  ✓ Features: (100, 470596)

📊 Détection de changements...
  ✓ Score moyen: 0.234
  ✓ Score max: 0.987

📈 Génération de la visualisation...
✓ Résultats sauvegardés: resultats_vraie_scene.png

📊 Métriques de performance...
  • Précision: 0.XXX
  • Rappel:    0.XXX
  • F1-Score:  0.XXX
  • Accuracy:  0.XXX

==================================================================
✅ Traitement terminé!
==================================================================
```

---

## 📊 Comparaison des scripts

### `demo_visuelle.py` - Démo rapide (SIMULATION)

**Avantages:**
- ✅ Aucune donnée à télécharger
- ✅ Exécution rapide (~10 secondes)
- ✅ Montre le concept

**Inconvénients:**
- ❌ Images artificielles (pas réelles)
- ❌ Résultats peu réalistes
- ❌ Petite résolution (128×128)

**Usage:**
```bash
python3 demo_visuelle.py
```

---

### `demo_avec_vraies_donnees.py` - Simulation "réaliste" (SIMULATION)

**Avantages:**
- ✅ Aucune donnée à télécharger
- ✅ Valeurs Sentinel-2 réalistes
- ✅ Pattern organique d'incendie
- ✅ Plus grande résolution (512×512)

**Inconvénients:**
- ❌ Toujours une simulation (PAS de vraies images)
- ❌ Topographie artificielle
- ❌ Ne montre pas la vraie performance du modèle

**Usage:**
```bash
python3 demo_avec_vraies_donnees.py
```

---

### `run_pann_vraies_images.py` - Vraies images satellites (VRAIES DONNÉES)

**Avantages:**
- ✅ **Vraies images GeoTIFF Sentinel-2/Landsat**
- ✅ Vraies valeurs spectrales
- ✅ Vraies coordonnées géographiques
- ✅ Masque de vérité terrain inclus
- ✅ Métriques précises
- ✅ Haute résolution (10980×10980 pour Sentinel-2)

**Inconvénients:**
- ⚠️ Nécessite de télécharger les données (~100-500 MB par scène)
- ⚠️ Plus long à exécuter (~1-3 minutes selon la résolution)
- ⚠️ Nécessite rasterio

**Usage:**
```bash
# Après avoir téléchargé les données
python3 run_pann_vraies_images.py --scene data/fires/EONET_4766 --band B08
```

---

## 🎯 Recommandations

### Pour comprendre le concept rapidement:
→ Utilisez `demo_visuelle.py`

### Pour voir une simulation plus réaliste:
→ Utilisez `demo_avec_vraies_donnees.py`

### Pour tester le vrai modèle PANN:
→ **Utilisez `run_pann_vraies_images.py` avec les données RaVAEn**

---

## 📚 Documentation complète

- **Guide d'installation:** `GUIDE_INSTALLATION_FR.md`
- **Démarrage rapide:** `QUICKSTART_FR.md`
- **Comment ça marche:** `COMMENT_CA_MARCHE.md`
- **Utiliser de vraies images:** `UTILISER_VRAIES_IMAGES.md` ← **IMPORTANT!**
- **Ce fichier:** `README_DEMOS.md`

---

## ❓ FAQ

**Q: Les démos montrent-elles les vrais résultats du modèle?**

Non. Les scripts de démo (`demo_*.py`) utilisent une simulation simplifiée du réseau PANN. Pour les vrais résultats, vous devez:
1. Installer Julia
2. Utiliser le code Julia original dans `src/`
3. Ou utiliser `run_pann_vraies_images.py` comme point de départ

**Q: Pourquoi créer des simulations alors que le projet a de vraies images?**

Les simulations permettent de:
- Tester le code sans télécharger 10+ GB de données
- Comprendre le flux de traitement
- Déboguer rapidement

Mais pour des **vrais résultats**, utilisez de **vraies images**!

**Q: Comment obtenir les meilleures performances?**

Utilisez le code Julia original avec:
- Vraies données RaVAEn
- Fichier de connectivité complet (803 nœuds, 12279 memristors)
- Simulation physique complète (400 timesteps)
- Voir `scripts/exampleRun.jl`

---

## 🔗 Liens utiles

- **Paper:** https://www.nature.com/articles/s41598-025-19057-9
- **Dataset RaVAEn:** https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn
- **Repo RaVAEn:** https://github.com/spaceml-org/RaVAEn
- **Sentinel Hub:** https://www.sentinel-hub.com/
- **USGS Earth Explorer:** https://earthexplorer.usgs.gov/

---

**✅ EN RÉSUMÉ:**

Les scripts `demo_*.py` = **simulations** pour démonstration rapide
Le script `run_pann_vraies_images.py` = **vraies images GeoTIFF**

**Pour de vrais résultats → téléchargez le dataset RaVAEn et utilisez `run_pann_vraies_images.py`!**
