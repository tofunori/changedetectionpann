#!/usr/bin/env python3
"""
Exécuter le modèle PANN sur de VRAIES images satellites
=========================================================

Ce script lit de vraies images GeoTIFF Sentinel-2 ou Landsat
et applique le modèle PANN pour la détection de changements.

Prérequis:
    pip install rasterio numpy matplotlib scipy

Usage:
    python3 run_pann_vraies_images.py --scene data/fires/EONET_4766 --band B08
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
import sys

print("=" * 70)
print("Modèle PANN - Détection de changements sur VRAIES images satellites")
print("=" * 70)
print()

# Vérifier rasterio
try:
    import rasterio
    from rasterio.errors import RasterioIOError
    print("✓ rasterio disponible")
except ImportError:
    print("❌ rasterio requis!")
    print("   Installation: pip install rasterio")
    sys.exit(1)

print()

# ============================================================================
# LECTURE DES VRAIES IMAGES GEOTIFF
# ============================================================================

def find_satellite_images(scene_dir, band='B08', event='pre'):
    """
    Trouve les fichiers GeoTIFF pour une bande spécifique

    Args:
        scene_dir: Chemin vers la scène (ex: data/fires/EONET_4766)
        band: Bande Sentinel-2 ('B01'-'B12', 'B8A') ou Landsat ('B1'-'B11')
        event: 'pre' ou 'post'

    Returns:
        list: Chemins vers les fichiers .tif
    """
    scene_path = Path(scene_dir)

    if not scene_path.exists():
        raise FileNotFoundError(f"Scène non trouvée: {scene_dir}")

    event_dir = scene_path / f"{event}_event"

    if not event_dir.exists():
        raise FileNotFoundError(f"Dossier {event}_event non trouvé dans {scene_dir}")

    # Chercher les fichiers de cette bande
    # Format Sentinel-2: *_B08.tif
    # Format Landsat: *_B5.TIF
    patterns = [f"*_{band}.tif", f"*_{band}.TIF"]

    files = []
    for pattern in patterns:
        files.extend(sorted(event_dir.glob(pattern)))

    return files


def load_geotiff(tif_path):
    """
    Charge une image GeoTIFF

    Returns:
        data: array numpy (height, width)
        metadata: dict avec informations de l'image
    """
    with rasterio.open(tif_path) as src:
        # Lire la première bande (les fichiers RaVAEn ont 1 bande par fichier)
        data = src.read(1)

        metadata = {
            'width': src.width,
            'height': src.height,
            'crs': src.crs.to_string() if src.crs else 'Unknown',
            'bounds': src.bounds,
            'transform': src.transform,
            'dtype': str(src.dtypes[0]),
            'nodata': src.nodata
        }

        return data, metadata


def load_satellite_scene(scene_dir, band='B08', event='pre', use_last=True):
    """
    Charge une scène satellite complète

    Args:
        scene_dir: Chemin vers la scène
        band: Bande à charger
        event: 'pre' ou 'post'
        use_last: Si True, utilise la dernière image (recommandé pour pre)

    Returns:
        image: array numpy
        metadata: dict
        file_path: chemin du fichier chargé
    """
    files = find_satellite_images(scene_dir, band, event)

    if not files:
        raise FileNotFoundError(
            f"Aucune image trouvée pour {event}_event, bande {band}\n"
            f"Dossier recherché: {scene_dir}/{event}_event/*_{band}.tif"
        )

    print(f"📡 {event.capitalize()}-événement:")
    print(f"   Trouvé {len(files)} image(s) pour la bande {band}")

    # Sélectionner l'image
    if use_last:
        selected_file = files[-1]
        print(f"   → Utilisation de la dernière: {selected_file.name}")
    else:
        selected_file = files[0]
        print(f"   → Utilisation de la première: {selected_file.name}")

    # Charger
    image, metadata = load_geotiff(selected_file)

    print(f"   • Dimensions: {image.shape[1]}×{image.shape[0]} pixels")
    print(f"   • Type: {metadata['dtype']}")
    print(f"   • Valeurs: min={image.min()}, max={image.max()}, mean={image.mean():.1f}")
    print(f"   • CRS: {metadata['crs']}")

    return image, metadata, selected_file


def load_ground_truth(scene_dir):
    """
    Charge le masque de vérité terrain (si disponible)

    Le fichier est typiquement nommé: EONET_XXXX_post_*.tif
    """
    scene_path = Path(scene_dir)

    # Chercher le masque
    mask_files = list(scene_path.glob("*_post_*.tif"))

    if not mask_files:
        print("⚠️  Pas de masque de vérité terrain trouvé")
        return None, None

    mask_file = mask_files[0]
    print(f"\n✓ Masque de vérité terrain: {mask_file.name}")

    mask, metadata = load_geotiff(mask_file)

    print(f"   • Dimensions: {mask.shape}")
    print(f"   • Valeurs uniques: {np.unique(mask)}")

    # Normaliser le masque (souvent 0 = pas de changement, 255 = changement)
    if mask.max() > 1:
        mask = (mask > 0).astype(float)

    return mask, metadata


# ============================================================================
# PRÉTRAITEMENT (comme dans le code Julia original)
# ============================================================================

def normalize_sentinel2(image, band=8):
    """
    Normalise les données Sentinel-2 comme dans dataLoader.jl

    Bandes Sentinel-2 et leurs plages log:
    B1 (443nm):  [7.3, 7.6]
    B2 (490nm):  [6.9, 7.5]
    B3 (560nm):  [6.5, 7.4]
    B4 (665nm):  [6.2, 7.5]
    B5 (705nm):  [6.1, 7.5]
    B6 (740nm):  [6.5, 8.0]
    B7 (783nm):  [6.5, 8.0]
    B8 (842nm):  [6.5, 8.0]  ← NIR, bon pour végétation
    B8A (865nm): [6.5, 8.0]
    B9 (945nm):  [6.0, 7.0]
    B10 (1375nm):[2.5, 4.5]
    B11 (1610nm):[6.0, 8.0]
    B12 (2190nm):[6.0, 8.0]
    """
    # Valeurs de normalisation (du code Julia)
    norm_values = {
        1: (7.3, 7.6),   # B1
        2: (6.9, 7.5),   # B2
        3: (6.5, 7.4),   # B3
        4: (6.2, 7.5),   # B4
        5: (6.1, 7.5),   # B5
        6: (6.5, 8.0),   # B6
        7: (6.5, 8.0),   # B7
        8: (6.5, 8.0),   # B8 (NIR)
        9: (6.5, 8.0),   # B8A
        10: (6.0, 7.0),  # B9
        11: (2.5, 4.5),  # B10
        12: (6.0, 8.0),  # B11
        13: (6.0, 8.0),  # B12
    }

    log_min, log_max = norm_values.get(band, (6.5, 8.0))
    output_min, output_max = 0.005, 1.0

    # Éviter log(0)
    image = np.clip(image, 1, None)

    # Log-transform
    log_image = np.log(image)

    # Normaliser
    normalized = ((log_image - log_min) / (log_max - log_min)) * \
                 (output_max - output_min) + output_min

    # Clipper
    normalized = np.clip(normalized, output_min, output_max)

    # Remplacer les NaN par 0.005
    normalized = np.nan_to_num(normalized, nan=0.005)

    return normalized


def apply_max_pooling(image, pool_size=16, stride=16):
    """
    Applique max-pooling comme dans dataLoader.jl
    """
    h, w = image.shape
    out_h = (h - pool_size) // stride + 1
    out_w = (w - pool_size) // stride + 1

    pooled = np.zeros((out_h, out_w))

    for i in range(out_h):
        for j in range(out_w):
            y_start = i * stride
            x_start = j * stride
            pooled[i, j] = np.max(image[y_start:y_start+pool_size,
                                        x_start:x_start+pool_size])

    return pooled


# ============================================================================
# MODÈLE PANN (simulation simplifiée)
# ============================================================================

def simulate_pann_network(signals, num_timesteps=200, seed=42):
    """
    Simulation simplifiée du réseau PANN
    (Le vrai modèle Julia utilise la simulation physique complète)
    """
    num_signals = len(signals)
    num_features = 100

    features = np.zeros((num_features, num_signals))

    np.random.seed(42)  # Topologie fixe
    network_weights = np.random.randn(num_features, num_features) * 0.1
    input_projection = np.random.randn(num_features, 10) * 0.2

    np.random.seed(seed)  # Bruit variable

    for sig_idx, signal_value in enumerate(signals):
        # Transformation du signal en vecteur de stimulation
        input_vector = np.zeros(10)
        input_vector[0] = signal_value
        input_vector[1:] = signal_value * np.sin(np.arange(1, 10) * signal_value * 10)

        # État initial
        state = np.random.randn(num_features) * 0.001

        # Simulation temporelle
        for t in range(num_timesteps):
            stimulation = input_projection @ input_vector
            state = 0.9 * (network_weights @ state) + 0.1 * stimulation
            state = np.tanh(state)

        features[:, sig_idx] = state

    return features


def compute_change_map(pre_features, post_features, pooled_shape):
    """
    Calcule la carte de changements par distance Euclidienne
    """
    distances = np.sqrt(np.sum((post_features - pre_features)**2, axis=0))
    distances = (distances - distances.min()) / (distances.max() - distances.min() + 1e-8)
    change_map = distances.reshape(pooled_shape)
    return change_map


# ============================================================================
# VISUALISATION
# ============================================================================

def visualize_results(pre_img, post_img, change_map, ground_truth,
                     pre_file, post_file, output_file='results_vraies_images.png'):
    """
    Visualise les résultats avec de vraies images satellites
    """
    fig = plt.figure(figsize=(18, 11))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # Images brutes
    ax1 = fig.add_subplot(gs[0, 0])
    im1 = ax1.imshow(pre_img, cmap='gray', vmin=0, vmax=np.percentile(pre_img, 98))
    ax1.set_title(f'Pré-événement\n{pre_file.name[:40]}...', fontsize=9)
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, fraction=0.046, label='DN')

    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(post_img, cmap='gray', vmin=0, vmax=np.percentile(post_img, 98))
    ax2.set_title(f'Post-événement\n{post_file.name[:40]}...', fontsize=9)
    ax2.axis('off')
    plt.colorbar(im2, ax=ax2, fraction=0.046, label='DN')

    # Différence
    ax3 = fig.add_subplot(gs[0, 2])
    diff = np.abs(post_img - pre_img)
    im3 = ax3.imshow(diff, cmap='hot')
    ax3.set_title('Différence simple\n|Post - Pre|', fontsize=10, fontweight='bold')
    ax3.axis('off')
    plt.colorbar(im3, ax=ax3, fraction=0.046)

    # Carte PANN
    ax4 = fig.add_subplot(gs[1, :])
    im4 = ax4.imshow(change_map, cmap='hot', vmin=0, vmax=1, interpolation='nearest')
    ax4.set_title(f'Carte de détection PANN (Résolution: {change_map.shape[0]}×{change_map.shape[1]} après pooling)',
                  fontsize=11, fontweight='bold')
    ax4.axis('off')
    plt.colorbar(im4, ax=ax4, fraction=0.02, label='Score de changement')

    # Vérité terrain et détection
    if ground_truth is not None:
        from scipy.ndimage import zoom

        scale_y = ground_truth.shape[0] / change_map.shape[0]
        scale_x = ground_truth.shape[1] / change_map.shape[1]
        change_map_upscaled = zoom(change_map, (scale_y, scale_x), order=1)

        ax5 = fig.add_subplot(gs[2, 0])
        im5 = ax5.imshow(ground_truth, cmap='Reds', vmin=0, vmax=1)
        ax5.set_title('Vérité terrain\n(Masque de référence)', fontsize=10, fontweight='bold')
        ax5.axis('off')

        ax6 = fig.add_subplot(gs[2, 1])
        detection = (change_map_upscaled > 0.5).astype(float)
        im6 = ax6.imshow(detection, cmap='Reds', vmin=0, vmax=1)
        ax6.set_title('Détection PANN\n(Seuil = 0.5)', fontsize=10, fontweight='bold')
        ax6.axis('off')

        # Comparaison
        ax7 = fig.add_subplot(gs[2, 2])
        comparison = np.zeros((*ground_truth.shape, 3))
        comparison[:, :, 0] = ground_truth  # Rouge = vérité
        comparison[:, :, 1] = detection  # Vert = détection
        ax7.imshow(comparison)
        ax7.set_title('Comparaison\n(Rouge=GT, Vert=Détection, Jaune=Match)', fontsize=10, fontweight='bold')
        ax7.axis('off')

    fig.suptitle('Modèle PANN - Détection sur VRAIES images satellites Sentinel-2/Landsat',
                 fontsize=14, fontweight='bold')

    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✓ Résultats sauvegardés: {output_file}")


# ============================================================================
# MÉTRIQUES
# ============================================================================

def compute_metrics(change_map, ground_truth, threshold=0.5):
    """
    Calcule les métriques de performance
    """
    if ground_truth is None:
        print("\n⚠️  Pas de vérité terrain - impossible de calculer les métriques")
        return {}

    from scipy.ndimage import zoom

    print("\n📊 Métriques de performance...")

    scale_y = ground_truth.shape[0] / change_map.shape[0]
    scale_x = ground_truth.shape[1] / change_map.shape[1]
    change_map_resized = zoom(change_map, (scale_y, scale_x), order=1)

    prediction = (change_map_resized > threshold).astype(bool)
    gt = ground_truth.astype(bool)

    TP = np.sum(prediction & gt)
    FP = np.sum(prediction & ~gt)
    FN = np.sum(~prediction & gt)
    TN = np.sum(~prediction & ~gt)

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (TP + TN) / (TP + FP + FN + TN)

    print(f"  • Précision: {precision:.3f}")
    print(f"  • Rappel:    {recall:.3f}")
    print(f"  • F1-Score:  {f1:.3f}")
    print(f"  • Accuracy:  {accuracy:.3f}")
    print()
    print(f"  • TP: {TP:7d} pixels")
    print(f"  • FP: {FP:7d} pixels")
    print(f"  • FN: {FN:7d} pixels")
    print(f"  • TN: {TN:7d} pixels")

    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


# ============================================================================
# PROGRAMME PRINCIPAL
# ============================================================================

def main():
    """
    Fonction principale
    """
    parser = argparse.ArgumentParser(description='Exécuter PANN sur des vraies images satellites')
    parser.add_argument('--scene', type=str, required=True,
                       help='Chemin vers la scène (ex: data/fires/EONET_4766)')
    parser.add_argument('--band', type=str, default='B08',
                       help='Bande à utiliser (ex: B08 pour Sentinel-2, B5 pour Landsat)')
    parser.add_argument('--pool-size', type=int, default=16,
                       help='Taille du pooling kernel (défaut: 16)')
    parser.add_argument('--output', type=str, default='results_vraies_images.png',
                       help='Fichier de sortie pour la visualisation')

    args = parser.parse_args()

    print(f"Scène: {args.scene}")
    print(f"Bande: {args.band}")
    print(f"Pool size: {args.pool_size}")
    print()

    try:
        # Charger les images
        print("📥 Chargement des images satellites...")
        pre_img, pre_meta, pre_file = load_satellite_scene(args.scene, args.band, 'pre')
        post_img, post_meta, post_file = load_satellite_scene(args.scene, args.band, 'post')

        # Charger la vérité terrain
        ground_truth, gt_meta = load_ground_truth(args.scene)

        # Prétraitement
        print("\n🔧 Prétraitement...")
        band_num = int(args.band.replace('B', '').replace('A', ''))
        pre_norm = normalize_sentinel2(pre_img, band=band_num)
        post_norm = normalize_sentinel2(post_img, band=band_num)
        print("  ✓ Normalisation log-transform")

        pre_pooled = apply_max_pooling(pre_norm, pool_size=args.pool_size, stride=args.pool_size)
        post_pooled = apply_max_pooling(post_norm, pool_size=args.pool_size, stride=args.pool_size)
        print(f"  ✓ Max pooling: {pre_img.shape} → {pre_pooled.shape}")

        # Signaux
        pre_signals = pre_pooled.flatten()
        post_signals = post_pooled.flatten()
        print(f"  ✓ Signaux: {len(pre_signals)} entrées spatiales")

        # Modèle PANN
        print("\n🧠 Simulation du réseau PANN...")
        pre_features = simulate_pann_network(pre_signals, num_timesteps=200, seed=42)
        post_features = simulate_pann_network(post_signals, num_timesteps=200, seed=43)
        print(f"  ✓ Features: {pre_features.shape}")

        # Détection
        print("\n📊 Détection de changements...")
        change_map = compute_change_map(pre_features, post_features, pre_pooled.shape)
        print(f"  ✓ Score moyen: {change_map.mean():.3f}")
        print(f"  ✓ Score max: {change_map.max():.3f}")

        # Visualisation
        print("\n📈 Génération de la visualisation...")
        visualize_results(pre_img, post_img, change_map, ground_truth,
                         pre_file, post_file, args.output)

        # Métriques
        metrics = compute_metrics(change_map, ground_truth)

        print("\n" + "=" * 70)
        print("✅ Traitement terminé!")
        print("=" * 70)
        if metrics:
            print(f"\n📈 Performance: F1={metrics['f1']:.3f}, Accuracy={metrics['accuracy']:.3f}")

    except FileNotFoundError as e:
        print(f"\n❌ Erreur: {e}")
        print("\nVérifiez:")
        print("  1. Le chemin vers la scène est correct")
        print("  2. Les dossiers pre_event/ et post_event/ existent")
        print("  3. Les fichiers .tif sont présents")
        print("\nStructure attendue:")
        print(f"  {args.scene}/")
        print(f"    ├── pre_event/*_{args.band}.tif")
        print(f"    └── post_event/*_{args.band}.tif")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
