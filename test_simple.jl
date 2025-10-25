#!/usr/bin/env julia

"""
Script de test simple pour ChangeDetectionPANN

Ce script montre comment exécuter le modèle PANN sur une scène.
Modifiez les chemins ci-dessous selon votre configuration.
"""

using Pkg
Pkg.activate(@__DIR__)

using ChangeDetectionPANN

function main()
    println("=" ^ 60)
    println("Test ChangeDetectionPANN - Détection de changements")
    println("=" ^ 60)
    println()

    # ========================================
    # CONFIGURATION - MODIFIEZ CES VALEURS
    # ========================================

    # Chemin vers le dossier contenant les données RaVAEn
    # Exemple: "/home/user/data/ravaen/"
    dataPath = "/path/to/Data/"

    # Fichier de connectivité du réseau (topologie)
    # Ce fichier .mat décrit la structure du réseau neuromorphique
    connectivityFile = "803nw12279junctions256electrodes.mat"

    # Paramètres du modèle
    poolSize = 16        # Taille du pooling kernel
    numNodes = 803       # Nombre de nœuds dans le réseau
    numTimesteps = 400   # Nombre de pas de temps pour la simulation
    expName = "test_01"  # Nom de l'expérience (pour les fichiers de sortie)

    # Options d'exécution
    showProgressBar = true   # Afficher la barre de progression
    saveOutputFiles = true   # Sauvegarder les résultats

    # ========================================
    # VÉRIFICATIONS
    # ========================================

    if dataPath == "/path/to/Data/"
        println("⚠️  ATTENTION: Vous devez modifier 'dataPath' dans ce script!")
        println("   Actuellement: $dataPath")
        println("   Changer vers le chemin réel de vos données RaVAEn")
        println()
        println("Exemple:")
        println("   dataPath = \"/home/user/ravaen_data/\"")
        println()
        return
    end

    if !isdir(dataPath)
        println("❌ Erreur: Le chemin des données n'existe pas!")
        println("   Chemin spécifié: $dataPath")
        println("   Veuillez vérifier le chemin et réessayer.")
        return
    end

    # ========================================
    # EXÉCUTION
    # ========================================

    println("Configuration:")
    println("  • Données: $dataPath")
    println("  • Réseau: $connectivityFile")
    println("  • Nœuds: $numNodes")
    println("  • Timesteps: $numTimesteps")
    println("  • Expérience: $expName")
    println()
    println("Lancement du modèle...")
    println()

    try
        runScenes(
            connectivityFile,
            poolSize,
            numNodes,
            numTimesteps,
            expName,
            dataPath,
            enableProgBar=showProgressBar,
            saveFiles=saveOutputFiles
        )

        println()
        println("=" ^ 60)
        println("✓ Exécution terminée avec succès!")
        println("=" ^ 60)

        if saveOutputFiles
            println()
            println("Les résultats ont été sauvegardés.")
            println("Utilisez scripts/exampleEvaluation.jl pour analyser les résultats.")
        end

    catch e
        println()
        println("=" ^ 60)
        println("❌ Erreur durant l'exécution:")
        println("=" ^ 60)
        println(e)
        println()
        println("Suggestions:")
        println("  1. Vérifiez que toutes les dépendances sont installées")
        println("  2. Vérifiez le format des données (Sentinel-2 .tif)")
        println("  3. Vérifiez que le fichier de connectivité existe")
        println("  4. Consultez GUIDE_INSTALLATION_FR.md pour plus d'aide")
    end
end

# Exécuter le script
main()
