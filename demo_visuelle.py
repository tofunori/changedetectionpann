#!/usr/bin/env python3
"""
Démonstration visuelle du modèle PANN
======================================

Ce script simule le flux de traitement du modèle PANN pour la détection
de changements, sans nécessiter Julia ou les données réelles.

Il montre:
1. Comment les images sont prétraitées
2. Comment les signaux sont créés
3. Comment le réseau PANN réagit (simulation simplifiée)
4. Comment la carte de changements est générée
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Vérifier que matplotlib fonctionne
print("=" * 60)
print("Démonstration visuelle - Modèle PANN")
print("=" * 60)
print()

# ============================================================================
# 1. SIMULATION DE DONNÉES SATELLITES
# ============================================================================

def simulate_satellite_images():
    """
    Simule des images satellites avant/après catastrophe
    """
    print("📡 Simulation d'images satellites Sentinel-2...")

    # Créer une scène simple (128x128 pixels)
    size = 128

    # Image pré-événement: forêt uniforme
    pre_image = np.ones((size, size)) * 8000  # Haute reflectance NIR

    # Ajouter du bruit réaliste
    pre_image += np.random.normal(0, 200, (size, size))

    # Image post-événement: avec zone brûlée (cercle)
    post_image = pre_image.copy()

    # Créer une zone de changement (incendie circulaire)
    center = (size // 2, size // 2)
    radius = 30
    y, x = np.ogrid[:size, :size]
    mask = (x - center[0])**2 + (y - center[1])**2 <= radius**2

    # Zone brûlée = basse reflectance
    post_image[mask] = 1000 + np.random.normal(0, 100, np.sum(mask))

    # Vérité terrain (ground truth)
    ground_truth = mask.astype(float)

    print(f"  ✓ Images créées: {size}x{size} pixels")
    print(f"  ✓ Zone de changement: {np.sum(mask)} pixels")

    return pre_image, post_image, ground_truth


def normalize_sentinel2(image, band=8):
    """
    Normalise les données Sentinel-2 comme dans le code Julia
    Band 8 (NIR): log range [6.5, 8]
    """
    # Valeurs de normalisation pour la bande 8 (NIR)
    log_min, log_max = 6.5, 8.0
    output_min, output_max = 0.005, 1.0

    # Éviter log(0)
    image = np.clip(image, 1, None)

    # Log-transform et normalisation
    log_image = np.log(image)
    normalized = ((log_image - log_min) / (log_max - log_min)) * \
                 (output_max - output_min) + output_min

    # Clipper les valeurs
    normalized = np.clip(normalized, output_min, output_max)

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
            pool_region = image[y_start:y_start+pool_size,
                               x_start:x_start+pool_size]
            pooled[i, j] = np.max(pool_region)

    return pooled


# ============================================================================
# 2. SIMULATION DU RÉSEAU PANN
# ============================================================================

def simulate_pann_network(signals, num_nodes=803, num_timesteps=400):
    """
    Simule la réponse du réseau PANN (version simplifiée)

    Dans le vrai modèle:
    - 803 nœuds avec topologie complexe
    - 12279 connections (memristors)
    - Simulation physique complète

    Ici on simule une réponse approximative pour la démonstration

    Returns:
        features: array de shape (num_features, num_signals)
                  où chaque colonne est le vecteur de features pour une position spatiale
    """
    print("\n🧠 Simulation du réseau PANN...")
    print(f"  • Nœuds: {num_nodes}")
    print(f"  • Pas de temps: {num_timesteps}")
    print(f"  • Signaux d'entrée: {len(signals)}")

    num_signals = len(signals)

    # Paramètres physiques des memristors
    Ron = 1.287e4   # Résistance ON (Ohms)
    Roff = 1.287e7  # Résistance OFF (Ohms)

    # Nombre de features par signal (dimensions du vecteur de caractéristiques)
    num_features = 50

    # Pour chaque signal spatial, générer un vecteur de features
    # basé sur une dynamique temporelle simplifiée
    features = np.zeros((num_features, num_signals))

    np.random.seed(42)  # Reproductibilité

    # Poids du réseau (matrice aléatoire représentant la topologie)
    network_weights = np.random.randn(num_features, num_features) * 0.05

    for sig_idx, signal_value in enumerate(signals):
        # État initial du réseau
        state = np.random.randn(num_features) * 0.1

        # Simulation temporelle simplifiée
        for t in range(num_timesteps):
            # Influence du signal d'entrée
            input_effect = signal_value * np.random.randn(num_features) * 0.3

            # Dynamique du réseau (effet mémoire + input)
            state = np.tanh(network_weights @ state * 0.9 + input_effect)

        # Le vecteur final est notre caractéristique
        features[:, sig_idx] = state

    print(f"  ✓ Simulation terminée")
    print(f"  ✓ Features extraites: {num_features} dim × {num_signals} positions")

    return features


def compute_change_map(pre_features, post_features, pooled_shape):
    """
    Calcule la carte de changements basée sur la distance Euclidienne

    Args:
        pre_features: array (num_features, num_positions)
        post_features: array (num_features, num_positions)
        pooled_shape: tuple (height, width) de la grille spatiale
    """
    print("\n📊 Calcul de la carte de changements...")

    # Calculer la distance Euclidienne pour chaque position spatiale
    # (chaque colonne de features correspond à une position)
    distances = np.sqrt(np.sum((post_features - pre_features)**2, axis=0))

    print(f"  • Distances calculées: {len(distances)} positions")
    print(f"  • Shape attendue: {pooled_shape} = {pooled_shape[0] * pooled_shape[1]} positions")

    # Normaliser entre 0 et 1
    distances = (distances - distances.min()) / (distances.max() - distances.min() + 1e-8)

    # Reshaper en 2D
    change_map = distances.reshape(pooled_shape)

    print(f"  ✓ Carte générée: {change_map.shape}")
    print(f"  ✓ Valeur min: {change_map.min():.3f}")
    print(f"  ✓ Valeur max: {change_map.max():.3f}")
    print(f"  ✓ Valeur moyenne: {change_map.mean():.3f}")

    return change_map


# ============================================================================
# 3. VISUALISATION
# ============================================================================

def visualize_results(pre_img, post_img, change_map, ground_truth):
    """
    Crée une visualisation complète des résultats
    """
    print("\n📈 Création de la visualisation...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Démonstration PANN - Détection de changements',
                 fontsize=16, fontweight='bold')

    # Images brutes
    axes[0, 0].imshow(pre_img, cmap='YlGn', vmin=0, vmax=10000)
    axes[0, 0].set_title('1. Image Pré-événement\n(Forêt - haute reflectance NIR)')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(post_img, cmap='YlGn', vmin=0, vmax=10000)
    axes[0, 1].set_title('2. Image Post-événement\n(Zone brûlée - basse reflectance)')
    axes[0, 1].axis('off')

    # Différence simple
    diff = np.abs(post_img - pre_img)
    axes[0, 2].imshow(diff, cmap='hot')
    axes[0, 2].set_title('3. Différence simple\n(|Post - Pre|)')
    axes[0, 2].axis('off')

    # Carte de changements PANN
    im = axes[1, 0].imshow(change_map, cmap='hot', vmin=0, vmax=1)
    axes[1, 0].set_title('4. Carte PANN\n(Features neuromorphiques)')
    axes[1, 0].axis('off')
    plt.colorbar(im, ax=axes[1, 0], fraction=0.046)

    # Vérité terrain
    axes[1, 1].imshow(ground_truth, cmap='Reds', vmin=0, vmax=1)
    axes[1, 1].set_title('5. Vérité terrain\n(Ground truth)')
    axes[1, 1].axis('off')

    # Détection finale (avec seuil)
    threshold = 0.5
    detection = (change_map > threshold).astype(float)
    axes[1, 2].imshow(detection, cmap='Reds', vmin=0, vmax=1)
    axes[1, 2].set_title(f'6. Détection finale\n(Seuil = {threshold})')
    axes[1, 2].axis('off')

    plt.tight_layout()

    # Sauvegarder
    output_file = 'demo_pann_results.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"  ✓ Image sauvegardée: {output_file}")

    # Afficher (si possible)
    try:
        plt.show(block=False)
        print("  ✓ Visualisation affichée")
    except:
        print("  ⚠ Affichage graphique non disponible (mode headless)")


def compute_metrics(change_map, ground_truth, threshold=0.5):
    """
    Calcule des métriques de performance
    """
    print("\n📊 Métriques de performance...")

    # Redimensionner la carte de changements à la taille du ground truth
    from scipy.ndimage import zoom
    scale_factor = ground_truth.shape[0] / change_map.shape[0]
    change_map_resized = zoom(change_map, scale_factor, order=1)

    # Binariser
    prediction = (change_map_resized > threshold).astype(bool)
    gt = ground_truth.astype(bool)

    # Calculer TP, FP, FN, TN
    TP = np.sum(prediction & gt)
    FP = np.sum(prediction & ~gt)
    FN = np.sum(~prediction & gt)
    TN = np.sum(~prediction & ~gt)

    # Métriques
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (TP + TN) / (TP + FP + FN + TN)

    print(f"  • Précision: {precision:.3f}")
    print(f"  • Rappel:    {recall:.3f}")
    print(f"  • F1-Score:  {f1:.3f}")
    print(f"  • Accuracy:  {accuracy:.3f}")
    print()
    print(f"  • TP (Vrais Positifs):  {TP:5d} pixels")
    print(f"  • FP (Faux Positifs):   {FP:5d} pixels")
    print(f"  • FN (Faux Négatifs):   {FN:5d} pixels")
    print(f"  • TN (Vrais Négatifs):  {TN:5d} pixels")

    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


# ============================================================================
# PROGRAMME PRINCIPAL
# ============================================================================

def main():
    """
    Fonction principale - Démo complète
    """
    print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Générer les images simulées
    pre_img, post_img, ground_truth = simulate_satellite_images()

    # 2. Prétraitement (comme dans le code Julia)
    print("\n🔧 Prétraitement des données...")
    pre_norm = normalize_sentinel2(pre_img, band=8)
    post_norm = normalize_sentinel2(post_img, band=8)
    print("  ✓ Normalisation appliquée (log-transform)")

    # 3. Max pooling
    pool_size = 16
    stride = 16
    pre_pooled = apply_max_pooling(pre_norm, pool_size, stride)
    post_pooled = apply_max_pooling(post_norm, pool_size, stride)
    print(f"  ✓ Max pooling ({pool_size}x{pool_size}): {pre_pooled.shape}")

    # 4. Créer les signaux (aplatir en vecteurs)
    pre_signals = pre_pooled.flatten()
    post_signals = post_pooled.flatten()
    print(f"  ✓ Signaux créés: {len(pre_signals)} entrées")

    # 5. Simuler le réseau PANN
    num_nodes = 803
    num_timesteps = 100  # Réduit pour la démo (vs 400 en production)

    pre_features = simulate_pann_network(pre_signals, num_nodes, num_timesteps)
    post_features = simulate_pann_network(post_signals, num_nodes, num_timesteps)

    # 6. Calculer la carte de changements
    change_map = compute_change_map(pre_features, post_features, pre_pooled.shape)

    # 7. Visualiser
    visualize_results(pre_img, post_img, change_map, ground_truth)

    # 8. Métriques
    metrics = compute_metrics(change_map, ground_truth, threshold=0.5)

    # Résumé
    print("\n" + "=" * 60)
    print("✅ Démonstration terminée!")
    print("=" * 60)
    print("\nCe que cette démo montre:")
    print("  1. Prétraitement des images satellites (normalisation)")
    print("  2. Réduction dimensionnelle (max pooling)")
    print("  3. Extraction de features dynamiques (réseau PANN simplifié)")
    print("  4. Détection de changements par distance Euclidienne")
    print("  5. Génération de carte de changements")
    print("\n⚠️  Note: C'est une simulation simplifiée!")
    print("    Le vrai modèle utilise:")
    print("    - Topologie complexe (803 nœuds, 12279 arêtes)")
    print("    - Simulation physique complète des memristors")
    print("    - Données Sentinel-2 réelles (13 bandes spectrales)")
    print()


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"\n❌ Erreur: {e}")
        print("\nInstallez les dépendances:")
        print("  pip install numpy matplotlib scipy")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
