# Quick Start - ChangeDetectionPANN

Guide rapide pour tester le projet en 5 étapes.

## 🎯 En bref

**Ce projet détecte les changements dans des images satellites sans entraînement.**
- ✅ Pas de GPU nécessaire
- ✅ Pas d'entraînement requis
- ✅ Fonctionne sur CPU standard

---

## 📦 Installation rapide (15 min)

### 1. Installer Julia
```bash
# Linux/Mac
wget https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.4-linux-x86_64.tar.gz
tar xzf julia-1.9.4-linux-x86_64.tar.gz
sudo mv julia-1.9.4 /opt/
sudo ln -s /opt/julia-1.9.4/bin/julia /usr/local/bin/julia

# Vérifier
julia --version
```

### 2. Installer les dépendances
```bash
cd changedetectionpann
julia
```

Dans Julia:
```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()  # Attend 5-10 min
exit()
```

### 3. Télécharger les données
- Lien: https://drive.google.com/drive/folders/1VEf49IDYFXGKcfvMsfh33VSiyx5MpHEn
- Choisir une catégorie (wildfire, flood, hurricane, landslide)
- Télécharger 1-2 scènes pour tester

### 4. Configurer le test
Éditer `test_simple.jl`:
```julia
dataPath = "/votre/chemin/vers/data/"  # ← MODIFIER ICI
```

### 5. Lancer
```bash
julia test_simple.jl
```

---

## 📊 Résultats attendus

Le modèle génère:
- **Change maps** (cartes des changements)
- **Métriques** (AUPRC, F1-score)
- **Visualisations** optionnelles

Temps: ~2-5 minutes par scène

---

## ❓ Problèmes courants

### Julia non trouvé
```bash
which julia  # Vérifier l'installation
```

### Packages manquants
```julia
using Pkg; Pkg.update(); Pkg.resolve()
```

### Fichier de connectivité manquant
Le fichier `.mat` devrait être fourni avec le projet. Si absent, voir le README original.

---

## 📚 Documentation complète

Voir `GUIDE_INSTALLATION_FR.md` pour plus de détails.

---

## 🔗 Liens utiles

- **Paper**: https://www.nature.com/articles/s41598-025-19057-9
- **Dataset**: https://github.com/spaceml-org/RaVAEn
- **Julia**: https://julialang.org/
