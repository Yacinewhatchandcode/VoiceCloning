#!/usr/bin/env python3
"""
Script simplifié pour créer un trigger de training Colab.
Crée directement le fichier trigger.json dans Google Drive.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def create_trigger(
    dataset_path: str,
    languages: str = "fr",
    epochs: int = 200,
    batch_size: int = 4,
    job_id: str = "starconnect_v1"
):
    """Crée un fichier trigger pour Colab."""
    
    # Configuration du trigger
    trigger_config = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "config": {
            "dataset_path": dataset_path,
            "languages": languages,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": 0.0001,
            "save_every": 10,
            "output_dir": f"/content/drive/MyDrive/f5_tts_checkpoints/{job_id}"
        },
        "status": "pending"
    }
    
    # Chemin vers Google Drive (monté localement si disponible)
    # Sinon, afficher les instructions
    drive_paths = [
        os.path.expanduser("~/Google Drive/My Drive/f5_tts_orchestration"),
        os.path.expanduser("~/GoogleDrive/My Drive/f5_tts_orchestration"),
        "/Volumes/GoogleDrive/My Drive/f5_tts_orchestration"
    ]
    
    trigger_file = None
    for drive_path in drive_paths:
        if os.path.exists(os.path.dirname(drive_path)):
            os.makedirs(drive_path, exist_ok=True)
            trigger_file = os.path.join(drive_path, "trigger.json")
            break
    
    if trigger_file:
        # Écrire le trigger
        with open(trigger_file, 'w') as f:
            json.dump(trigger_config, f, indent=2)
        print(f"✅ Trigger créé: {trigger_file}")
        return trigger_file
    else:
        # Google Drive non monté localement
        # Créer le fichier localement et donner les instructions
        local_trigger = "/tmp/trigger.json"
        with open(local_trigger, 'w') as f:
            json.dump(trigger_config, f, indent=2)
        
        print("⚠️  Google Drive non détecté localement")
        print(f"✅ Trigger créé localement: {local_trigger}")
        print("\n📋 INSTRUCTIONS MANUELLES:")
        print("1. Ouvrir Google Drive dans le navigateur")
        print("2. Créer un dossier: MyDrive/f5_tts_orchestration/")
        print("3. Uploader le fichier trigger.json dans ce dossier")
        print(f"4. Fichier à uploader: {local_trigger}")
        print("\nContenu du trigger:")
        print(json.dumps(trigger_config, indent=2))
        
        return local_trigger


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Créer trigger pour Colab")
    parser.add_argument(
        "--dataset",
        default="/content/drive/MyDrive/f5_tts_datasets/starconnect_f5tts",
        help="Chemin dataset dans Colab"
    )
    parser.add_argument("--languages", default="fr", help="Langues")
    parser.add_argument("--epochs", type=int, default=200, help="Nombre d'epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--job-id", default="starconnect_v1", help="Job ID")
    
    args = parser.parse_args()
    
    print("🚀 Création du trigger de training Colab\n")
    print(f"📊 Configuration:")
    print(f"   Dataset: {args.dataset}")
    print(f"   Langues: {args.languages}")
    print(f"   Epochs: {args.epochs}")
    print(f"   Batch Size: {args.batch_size}")
    print(f"   Job ID: {args.job_id}")
    print()
    
    trigger_file = create_trigger(
        args.dataset,
        args.languages,
        args.epochs,
        args.batch_size,
        args.job_id
    )
    
    print("\n✅ Prêt ! Le notebook Colab va détecter le trigger.")
