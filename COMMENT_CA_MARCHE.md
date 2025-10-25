# Comment fonctionne le modèle PANN?

## 🧠 Principe de base

Le modèle PANN (Physics Aware Neuromorphic Network) simule un **réseau physique de memristors** pour détecter les changements dans les images satellites.

### Memristor = Résistance avec mémoire
- Composant électronique dont la résistance change selon le courant qui le traverse
- "Se souvient" de son état précédent
- Permet de créer des réseaux neuronaux physiques sans entraînement

---

## 📊 Architecture du système

```
Images satellites (avant/après catastrophe)
           ↓
    [Prétraitement]
    - Normalisation
    - Extraction de bandes spectrales
    - Max pooling
           ↓
    [Signaux d'entrée]
    - Série temporelle de valeurs
    - Un signal par région de l'image
           ↓
    [Réseau PANN]
    - 803 nœuds (jonctions)
    - 12279 arêtes (connections memristors)
    - 256 électrodes d'entrée
           ↓
    [Simulation physique]
    - Équations de Kirchhoff (conservation courant)
    - Dynamique des memristors
    - 400 pas de temps
           ↓
    [Valeurs de sortie]
    - Lecture aux nœuds de sortie
    - Caractéristiques dynamiques
           ↓
    [Détection de changements]
    - Calcul de distance (Euclidienne)
    - Génération de carte de changements
           ↓
    [Résultats]
    - Change map (zones modifiées)
    - Métriques (AUPRC, F1-score)
```

---

## 🔬 Détails techniques

### 1. Chargement des données (dataLoader.jl)

```julia
# Structure qui charge les images .tif
struct DataLoader
    minVal, maxVal    # Normalisation
    band              # Bande spectrale (1-13 pour Sentinel-2)
    buffer            # Stockage temporaire
    signals           # Signaux pour le réseau
    poolSz, stride    # Taille du pooling
end
```

**Ce qui se passe:**
1. Lit les fichiers .tif (images multispectrales)
2. Normalise les valeurs (log-transform pour Sentinel-2)
3. Applique max-pooling pour réduire la dimension
4. Crée une matrice de signaux (temporel × spatial)

### 2. Modèle PANN (pannModel.jl)

```julia
struct PannModel
    nw              # Réseau (Network)
    es              # État des arêtes (EdgeState)
    lhs, rhs        # Matrices pour résolution système linéaire
    inputNodes      # Nœuds d'entrée
    readoutNodes    # Nœuds de lecture
end
```

**Paramètres physiques des memristors:**
- `Ron = 1.287e4 Ω` - Résistance minimale (état ON)
- `Roff = 1.287e7 Ω` - Résistance maximale (état OFF)
- `Vset = 1e-2 V` - Voltage pour activer
- `Vreset = 5e-3 V` - Voltage pour désactiver

### 3. Simulation (simulate.jl)

**À chaque pas de temps:**

1. **Mise à jour des conductances** (inverse de la résistance)
   ```julia
   updateConductance!(edgeState)
   ```

2. **Construction du système linéaire** (lois de Kirchhoff)
   ```julia
   # Pour chaque arête i: G[i] * (V[n1] - V[n2])
   # Conservation du courant à chaque nœud
   lhs * V = rhs
   ```

3. **Résolution du système**
   ```julia
   sol = lhs \ rhs  # Backslash operator = résolution
   ```

4. **Mise à jour de l'état des memristors**
   ```julia
   # La résistance change selon le voltage appliqué
   updateEdgeState!(edgeState, dt)
   ```

5. **Enregistrement des valeurs**
   ```julia
   network.nodeVoltage[:,t] = sol[1:V]
   ```

---

## 🎯 Exemple concret: Détection d'incendie

### Input:
- **Scène avant:** Forêt verte (reflectance haute en IR proche)
- **Scène après:** Zone brûlée (reflectance basse, cendres)

### Flux de traitement:

```
Image pre (t=0 à t=15):  [Band 8A - NIR]
   Forêt:    pixel = 8000 → log(8000) = 3.9
   ↓ Normalisation: (3.9 - 6.5) / (8 - 6.5) = -1.73 → 0.005

Image post (t=16):  [Band 8A - NIR]
   Brûlé:    pixel = 1000 → log(1000) = 3.0
   ↓ Normalisation: (3.0 - 6.5) / (8 - 6.5) = -2.33 → 0.001

Max pooling (16x16):
   → Signal temporel: [0.005, 0.005, ..., 0.001]
   → Changement abrupt détecté!

Réseau PANN:
   → État des memristors change différemment
   → Les nœuds de sortie montrent une réponse différente

Distance entre features:
   Pre:  [v1_pre, v2_pre, ..., v803_pre]
   Post: [v1_post, v2_post, ..., v803_post]

   Distance = ||Pre - Post|| = 0.85 (élevée!)

Seuil: si distance > 0.5 → CHANGEMENT DÉTECTÉ ✓
```

---

## ⚡ Pourquoi c'est "Training-Free"?

### Approche classique (nécessite entraînement):
```
CNN/Transformer → Millions de paramètres
                → Nécessite GPU
                → Entraînement sur milliers d'images
                → Heures/jours d'entraînement
```

### Approche PANN (sans entraînement):
```
Réseau physique → Topologie fixe (fichier .mat)
                → Paramètres physiques fixes (Ron, Roff)
                → Dynamique émergente naturelle
                → Utilise les propriétés physiques des memristors
```

**Avantages:**
- ✅ Pas besoin de données d'entraînement
- ✅ Fonctionne sur CPU basique
- ✅ Déployable sur satellite (ressources limitées)
- ✅ Résultats comparables aux modèles entraînés

---

## 📈 Métriques de performance

D'après le paper (Scientific Reports 2025):

| Catastrophe | AUPRC | vs SOTA |
|-------------|-------|---------|
| Wildfire    | 0.87  | Comparable |
| Flood       | 0.82  | Meilleur |
| Hurricane   | 0.85  | Comparable |
| Landslide   | 0.79  | Comparable |

**SOTA = State of the Art** (modèles entraînés classiques)

---

## 🔧 Fichiers importants

### Code principal:
- `src/changeDetection/pannModel.jl` - Définition du modèle
- `src/core/simulate.jl` - Boucle de simulation physique
- `src/changeDetection/dataLoader.jl` - Chargement des données

### Configuration:
- `src/connectivityData/803nw12279junctions256electrodes.mat` - Topologie du réseau

### Scripts d'exemple:
- `scripts/exampleRun.jl` - Exécuter le modèle
- `scripts/exampleEvaluation.jl` - Évaluer les résultats
- `scripts/exampleFeatureSpace.jl` - Visualiser l'espace des features

---

## 💡 Pour aller plus loin

### Comprendre la physique des memristors:
- Équation d'état: dw/dt = f(V, w)
- w = état du filament (entre 0 et 1)
- G = 1/R = w/Ron + (1-w)/Roff

### Visualisation du réseau:
Le fichier .mat contient:
- `adjMat`: Matrice d'adjacence (803×803)
- `edgeList`: Liste des connections
- Position des électrodes

### Applications:
- Détection de catastrophes en temps réel sur satellite
- Priorisation des données à téléverser
- Traitement embarqué low-power

---

## 🎓 Références

- **Paper:** Training-free AI for Earth Observation Change Detection using Physics Aware Neuromorphic Networks
- **Journal:** Nature Scientific Reports (2025)
- **DOI:** https://doi.org/10.1038/s41598-025-19057-9
- **Dataset:** RaVAEn (https://github.com/spaceml-org/RaVAEn)
