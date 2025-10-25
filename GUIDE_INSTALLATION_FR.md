# Guide d'Installation et de Test - ChangeDetectionPANN

## Vue d'ensemble

Ce projet implémente un réseau neuromorphique physique (PANN) pour la détection de changements dans les images satellites, **sans nécessiter d'entraînement**. Il est conçu pour fonctionner sur des ressources limitées (satellites, etc.).

## Complexité: ⭐⭐☆☆☆ (Moyenne)

**Temps d'installation estimé:** 15-30 minutes
**Niveau requis:** Utilisateur intermédiaire (connaissances de base en ligne de commande)

---

## 1. Installation de Julia

### Linux/Mac:
```bash
# Télécharger Julia 1.8+ depuis https://julialang.org/downloads/
wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.4-linux-x86_64.tar.gz
tar zxvf julia-1.9.4-linux-x86_64.tar.gz
sudo mv julia-1.9.4 /opt/
sudo ln -s /opt/julia-1.9.4/bin/julia /usr/local/bin/julia
```

### Windows:
Télécharger l'installateur depuis https://julialang.org/downloads/ et suivre les instructions.

### Vérifier l'installation:
```bash
julia --version
# Devrait afficher: julia version 1.9.4 (ou supérieur)
```

---

## 2. Installation des dépendances du projet

```bash
# Naviguer vers le projet
cd /home/user/changedetectionpann

# Lancer Julia
julia
```

Dans Julia:
```julia
# Activer l'environnement du projet
using Pkg
Pkg.activate(".")

# Installer toutes les dépendances automatiquement
Pkg.instantiate()

# Ceci va installer:
# - ArchGDAL (lecture de fichiers GeoTIFF)
# - Distances, Graphs, UMAP (calculs)
# - PyPlot (visualisation)
# - Et autres dépendances (~15 packages)

# Attendre que l'installation se termine (5-10 minutes)
```

### Installation de Python (pour PyPlot):
Si PyCall ne trouve pas Python:
```julia
ENV["PYTHON"] = ""  # Utiliser Conda.jl
Pkg.build("PyCall")
```

---

## 3. Télécharger les données de test (RaVAEn)

### Option A: Google Drive (recommandé)
1. Accéder à: https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn?usp=sharing
2. Télécharger les données d'événements (au choix):
   - **Landslides** (glissements de terrain): 5 scènes
   - **Hurricanes** (ouragans): 5 scènes
   - **Fires** (incendies): 5 scènes
   - **Floods** (inondations): 4 scènes

### Option B: Notebook Colab
Pour explorer les données sans téléchargement:
https://github.com/spaceml-org/RaVAEn (voir notebooks/)

### Structure des données attendue:
```
/path/to/Data/
├── wildfire/
│   ├── scene1/
│   │   ├── pre_event/
│   │   │   ├── image_001.tif
│   │   │   └── ...
│   │   ├── post_event/
│   │   │   └── image_post.tif
│   │   └── mask.tif
│   └── scene2/
│       └── ...
├── hurricane/
├── flood/
└── landslide/
```

**Format:** Sentinel-2 L1C (fichiers .tif multispectraux)

---

## 4. Télécharger le fichier de connectivité

Le modèle nécessite un fichier `.mat` décrivant la topologie du réseau:
- Fichier exemple: `803nw12279junctions256electrodes.mat`
- Ce fichier devrait être fourni avec le projet ou généré

**Note:** Si ce fichier n'est pas disponible, contactez les auteurs du papier.

---

## 5. Exécuter un test simple

### Créer un script de test:

Créez `test_simple.jl`:
```julia
using Pkg
Pkg.activate(".")

using ChangeDetectionPANN

# MODIFIER CES CHEMINS SELON VOTRE CONFIGURATION
dataPath = "/path/to/Data/"  # Chemin vers les données RaVAEn
connectivityFile = "803nw12279junctions256electrodes.mat"

# Paramètres:
# - connectivityFile: fichier de topologie du réseau
# - 16: taille du pool
# - 803: nombre de nœuds dans le réseau
# - 400: nombre de timesteps
# - "testExp": nom de l'expérience
# - dataPath: chemin vers les données

runScenes(connectivityFile, 16, 803, 400, "testExp", dataPath,
          enableProgBar=true,   # Afficher la barre de progression
          saveFiles=true)       # Sauvegarder les résultats
```

### Lancer le test:
```bash
julia test_simple.jl
```

---

## 6. Analyser les résultats

### Script d'évaluation:
```julia
using Pkg
Pkg.activate(".")

using ChangeDetectionPANN

# Ce script évalue les cartes de changements générées
include("scripts/exampleEvaluation.jl")
```

### Visualisation de l'espace des caractéristiques:
```julia
using Pkg
Pkg.activate(".")

using ChangeDetectionPANN

# Créer des plots de l'espace des features (UMAP)
include("scripts/exampleFeatureSpace.jl")
```

---

## 7. Résultats attendus

Le modèle génère:
1. **Cartes de changements** (change maps) - détection des zones modifiées
2. **Métriques de performance** (AUPRC, F1-score, etc.)
3. **Visualisations** de l'espace des caractéristiques

### Exemple de sortie:
```
Processing scene: wildfire_01
├─ Loading images... ✓
├─ Running PANN model... ✓
├─ Computing change map... ✓
└─ Metrics: AUPRC=0.87, F1=0.82
```

---

## Dépannage

### Problème: Julia ne trouve pas les packages
```julia
Pkg.update()
Pkg.resolve()
```

### Problème: Erreur PyCall
```julia
ENV["PYTHON"] = ""
Pkg.build("PyCall")
```

### Problème: Fichiers .tif non reconnus
Vérifier l'installation d'ArchGDAL:
```julia
using ArchGDAL
# Si erreur, réinstaller:
Pkg.build("ArchGDAL")
```

### Problème: Mémoire insuffisante
Réduire la taille des scènes ou le nombre d'images simultanées.

---

## Performance

- **Temps de traitement:** ~2-5 minutes par scène (selon la taille)
- **Mémoire:** ~4-8 GB RAM recommandé
- **GPU:** Non requis (CPU uniquement)

---

## Ressources

- **Paper:** https://www.nature.com/articles/s41598-025-19057-9
- **Dataset RaVAEn:** https://github.com/spaceml-org/RaVAEn
- **Documentation Julia:** https://docs.julialang.org/

---

## Contact

Pour des questions sur le code ou le modèle, consulter le repository ou contacter les auteurs via GitHub Issues.
