# Comment utiliser de VRAIES images satellites

## ⚠️ Clarification importante

Les scripts `demo_visuelle.py` et `demo_avec_vraies_donnees.py` utilisent des **images SIMULÉES** - ce ne sont **PAS** de vraies images Landsat ou Sentinel-2.

Pour utiliser de **vraies images satellites**, suivez ce guide.

---

## 📥 Option 1: Dataset RaVAEn (Recommandé)

### Téléchargement

1. **Accédez au Google Drive public:**
   https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn?usp=sharing

2. **Téléchargez un ou plusieurs événements:**
   - `fires.zip` (5 scènes d'incendies) - ~2 GB
   - `floods.zip` (4 scènes d'inondations)
   - `hurricanes.zip` (5 scènes d'ouragans)
   - `landslides.zip` (5 scènes de glissements de terrain)

3. **Extrayez dans le projet:**
   ```bash
   # Créer le dossier data
   mkdir -p changedetectionpann/data

   # Extraire (exemple avec fires)
   unzip fires.zip -d changedetectionpann/data/
   ```

### Structure attendue

```
changedetectionpann/data/
└── fires/
    ├── EONET_4766/               # Californie 2018
    │   ├── pre_event/
    │   │   ├── S2A_MSIL1C_20181027T184931_N0206_R113_T10TFK_20181027T202554_B01.tif
    │   │   ├── S2A_MSIL1C_20181027T184931_N0206_R113_T10TFK_20181027T202554_B02.tif
    │   │   ├── ... (13 bandes, multiple dates)
    │   ├── post_event/
    │   │   ├── S2A_MSIL1C_20181116T184921_N0207_R113_T10TFK_20181116T202950_B01.tif
    │   │   └── ... (13 bandes)
    │   └── EONET_4766_post_fire.tif  # Masque de référence
    └── EONET_5068/               # Autre incendie
        └── ...
```

### Format des données

- **Mission:** Sentinel-2
- **Niveau:** L1C (Top-of-Atmosphere Reflectance)
- **Format:** GeoTIFF (.tif)
- **Bandes:** 13 bandes spectrales (B01-B12, B8A)
- **Résolution:**
  - 10m: B02 (Blue), B03 (Green), B04 (Red), B08 (NIR)
  - 20m: B05, B06, B07, B8A, B11, B12
  - 60m: B01, B09, B10
- **Valeurs:** Digital Numbers (DN) 0-65535

---

## 🛠️ Option 2: Téléchargement manuel via API

### A. Copernicus Open Access Hub (Sentinel-2)

1. **Créer un compte gratuit:**
   https://scihub.copernicus.eu/

2. **Rechercher des scènes:**
   - Utilisez https://scihub.copernicus.eu/dhus/
   - Filtrez par date, location, couverture nuageuse

3. **Télécharger via Python:**
   ```bash
   pip install sentinelsat
   ```

   ```python
   from sentinelsat import SentinelAPI

   api = SentinelAPI('username', 'password', 'https://scihub.copernicus.eu/dhus')

   # Rechercher une scène
   products = api.query(
       area='POLYGON((-122.5 37.5, -122.5 38.5, -121.5 38.5, -121.5 37.5, -122.5 37.5))',
       date=('20181001', '20181130'),
       platformname='Sentinel-2',
       cloudcoverpercentage=(0, 10)
   )

   # Télécharger
   api.download_all(products)
   ```

### B. USGS Earth Explorer (Landsat)

1. **Accédez à:** https://earthexplorer.usgs.gov/
2. **Créez un compte gratuit**
3. **Recherchez et téléchargez des scènes Landsat 8**

### C. AWS Open Data (Landsat)

Landsat sur AWS S3 (accès public):
```python
import boto3
from botocore import UNSIGNED
from botocore.config import Config

s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

# Exemple: Landsat 8, Path 042, Row 034
bucket = 'usgs-landsat'
prefix = 'collection02/level-1/standard/oli-tirs/2017/042/034/LC08_L1TP_042034_20170616_20200903_02_T1/'

# Lister les fichiers
objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
for obj in objects.get('Contents', []):
    print(obj['Key'])
```

---

## 🐍 Script Python pour lire de vraies images

Voici un script qui lit de **vraies** images GeoTIFF:

```python
#!/usr/bin/env python3
"""
Lecture de vraies images Sentinel-2 / Landsat
"""

import rasterio
import numpy as np
import matplotlib.pyplot as plt

def read_satellite_band(tif_path, band_number=1):
    """
    Lit une bande d'une image satellite GeoTIFF

    Args:
        tif_path: chemin vers le fichier .tif
        band_number: numéro de la bande (1-indexed)

    Returns:
        data: array numpy avec les valeurs de pixels
        metadata: informations sur l'image
    """
    with rasterio.open(tif_path) as src:
        # Lire la bande
        data = src.read(band_number)

        # Métadonnées
        metadata = {
            'width': src.width,
            'height': src.height,
            'crs': src.crs,
            'transform': src.transform,
            'bounds': src.bounds,
            'dtype': src.dtypes[band_number-1]
        }

        return data, metadata

# Exemple d'utilisation
if __name__ == "__main__":
    # Remplacer par votre chemin
    tif_file = "data/fires/EONET_4766/pre_event/S2A_..._B08.tif"

    # Lire la bande NIR (B08)
    nir_data, meta = read_satellite_band(tif_file, band_number=1)

    print(f"Image: {meta['width']}×{meta['height']} pixels")
    print(f"Valeurs: min={nir_data.min()}, max={nir_data.max()}, mean={nir_data.mean():.1f}")
    print(f"CRS: {meta['crs']}")

    # Visualiser
    plt.figure(figsize=(10, 8))
    plt.imshow(nir_data, cmap='gray')
    plt.colorbar(label='DN (Digital Numbers)')
    plt.title(f'Sentinel-2 Bande NIR\n{tif_file}')
    plt.tight_layout()
    plt.savefig('vraie_image_sentinel2.png', dpi=150)
    print("Image sauvegardée: vraie_image_sentinel2.png")
```

---

## 🔧 Script PANN avec vraies images

Voici comment adapter le modèle PANN pour de vraies images:

```python
import rasterio
import numpy as np
from pathlib import Path

def load_sentinel2_scene(scene_dir, band='B08', event='pre'):
    """
    Charge toutes les images d'une scène Sentinel-2

    Args:
        scene_dir: dossier de la scène (ex: data/fires/EONET_4766)
        band: bande à charger ('B01' à 'B12', 'B8A')
        event: 'pre' ou 'post'

    Returns:
        images: liste d'arrays numpy
    """
    event_dir = Path(scene_dir) / f"{event}_event"

    # Trouver tous les fichiers de cette bande
    band_files = sorted(event_dir.glob(f"*_{band}.tif"))

    print(f"Trouvé {len(band_files)} images {event}-événement (bande {band})")

    images = []
    for f in band_files:
        with rasterio.open(f) as src:
            data = src.read(1)  # Première bande du fichier
            images.append(data)
            print(f"  - {f.name}: {data.shape}, DN range [{data.min()}-{data.max()}]")

    return images

# Utilisation
scene_dir = "data/fires/EONET_4766"

# Charger les images pré et post
pre_images = load_sentinel2_scene(scene_dir, band='B08', event='pre')
post_images = load_sentinel2_scene(scene_dir, band='B08', event='post')

# Utiliser la dernière image pré et la post
pre_image = pre_images[-1]
post_image = post_images[0]

# Maintenant appliquer le prétraitement PANN
from your_pann_module import normalize_sentinel2, apply_max_pooling

pre_norm = normalize_sentinel2(pre_image, band=8)
post_norm = normalize_sentinel2(post_image, band=8)

pre_pooled = apply_max_pooling(pre_norm, pool_size=16, stride=16)
post_pooled = apply_max_pooling(post_norm, pool_size=16, stride=16)

# ... continuer avec le modèle PANN
```

---

## 📋 Checklist pour utiliser de vraies images

- [ ] Télécharger le dataset RaVAEn ou des scènes Sentinel-2/Landsat
- [ ] Installer rasterio: `pip install rasterio`
- [ ] Vérifier la structure des dossiers
- [ ] Tester la lecture d'un fichier GeoTIFF
- [ ] Adapter les scripts pour pointer vers vos données
- [ ] Exécuter le modèle PANN sur les vraies images

---

## ❓ FAQ

### Q: Les scripts demo_*.py utilisent de vraies images?

**Non.** Ces scripts **simulent** des images avec numpy. Pour de vraies images, suivez ce guide.

### Q: Quelle bande utiliser?

Pour la détection de végétation/incendies:
- **Sentinel-2:** Bande B08 (NIR, 842nm) - Excellente pour végétation
- **Landsat 8:** Bande B5 (NIR, 865nm)

Pour d'autres types d'événements:
- Inondations: B11 (SWIR1) ou B12 (SWIR2)
- Ouragans: B02 (Blue), B03 (Green), B04 (Red) en RGB

### Q: Combien d'espace disque nécessaire?

- Une scène RaVAEn: ~100-500 MB
- Dataset complet (19 événements): ~10 GB

### Q: Les images doivent être prétraitées?

Le modèle PANN attend:
- Format: GeoTIFF
- Type: Sentinel-2 L1C ou Landsat 8 L1
- Pas besoin de correction atmosphérique (L1C suffit)

---

## 🔗 Ressources

- **RaVAEn Dataset:** https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn
- **Sentinel Hub:** https://www.sentinel-hub.com/
- **Copernicus Open Access:** https://scihub.copernicus.eu/
- **USGS Earth Explorer:** https://earthexplorer.usgs.gov/
- **AWS Landsat:** https://registry.opendata.aws/landsat-8/
- **Documentation rasterio:** https://rasterio.readthedocs.io/

---

## 💡 Conclusion

**Pour résumer:**
1. Les scripts actuels = simulations (PAS de vraies images)
2. Pour des vraies images = télécharger RaVAEn ou Sentinel-2/Landsat
3. Utiliser `rasterio` pour lire les GeoTIFF
4. Adapter les chemins dans les scripts

**Je ne peux pas télécharger les vraies images dans cet environnement (restrictions réseau 403), mais vous pouvez le faire sur votre machine!**
