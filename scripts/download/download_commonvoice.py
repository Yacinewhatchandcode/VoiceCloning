#!/usr/bin/env python3
"""
Script de téléchargement automatisé pour Mozilla Common Voice.
Supporte français et arabe avec gestion de versions.
"""

import argparse
import os
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm
import pandas as pd


def download_commonvoice(language: str, version: str, output_dir: str, split: str = "train"):
    """
    Télécharge Mozilla Common Voice pour une langue donnée.
    
    Args:
        language: Code langue (fr, ar)
        version: Version du dataset (ex: 17.0)
        output_dir: Répertoire de sortie
        split: Split à télécharger (train, validation, test, all)
    """
    print(f"🚀 Téléchargement Common Voice {version} — Langue: {language}")
    
    # Créer répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Mapping des codes de langue
    lang_map = {
        "fr": "fr",
        "ar": "ar",
        "arabic": "ar",
        "french": "fr"
    }
    lang_code = lang_map.get(language.lower(), language)
    
    # Charger le dataset depuis HuggingFace
    dataset_name = f"mozilla-foundation/common_voice_{version.replace('.', '_')}"
    
    try:
        if split == "all":
            splits = ["train", "validation", "test"]
        else:
            splits = [split]
        
        for current_split in splits:
            print(f"\n📥 Téléchargement du split: {current_split}")
            
            dataset = load_dataset(
                dataset_name,
                lang_code,
                split=current_split,
                trust_remote_code=True
            )
            
            # Créer sous-répertoire pour le split
            split_dir = output_path / current_split
            split_dir.mkdir(exist_ok=True)
            
            # Sauvegarder les métadonnées
            metadata = []
            
            print(f"💾 Sauvegarde de {len(dataset)} fichiers audio...")
            for idx, item in enumerate(tqdm(dataset)):
                # Extraire les informations
                audio_data = item["audio"]
                text = item["sentence"]
                client_id = item.get("client_id", f"speaker_{idx}")
                
                # Nom de fichier
                filename = f"{lang_code}_{current_split}_{idx:06d}.wav"
                audio_path = split_dir / filename
                
                # Sauvegarder l'audio (déjà en format array numpy)
                import soundfile as sf
                sf.write(
                    str(audio_path),
                    audio_data["array"],
                    audio_data["sampling_rate"]
                )
                
                # Ajouter aux métadonnées
                metadata.append({
                    "filename": filename,
                    "path": str(audio_path),
                    "text": text,
                    "language": lang_code,
                    "speaker_id": client_id,
                    "duration": len(audio_data["array"]) / audio_data["sampling_rate"],
                    "sample_rate": audio_data["sampling_rate"]
                })
            
            # Sauvegarder metadata CSV
            df = pd.DataFrame(metadata)
            csv_path = split_dir / "metadata.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
            print(f"✅ Split '{current_split}' téléchargé: {len(dataset)} fichiers")
            print(f"   Metadata: {csv_path}")
        
        # Statistiques globales
        print(f"\n📊 Téléchargement terminé!")
        print(f"   Répertoire: {output_path}")
        print(f"   Langue: {lang_code}")
        print(f"   Splits: {', '.join(splits)}")
        
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement: {e}")
        print(f"   Vérifiez que la version {version} existe pour la langue {lang_code}")
        print(f"   Dataset: {dataset_name}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Télécharger Mozilla Common Voice (FR/AR)"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        required=True,
        choices=["fr", "ar", "french", "arabic"],
        help="Langue à télécharger"
    )
    parser.add_argument(
        "--version", "-v",
        type=str,
        default="17.0",
        help="Version de Common Voice (ex: 17.0, 16.1)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Répertoire de sortie"
    )
    parser.add_argument(
        "--split", "-s",
        type=str,
        default="train",
        choices=["train", "validation", "test", "all"],
        help="Split à télécharger"
    )
    
    args = parser.parse_args()
    
    download_commonvoice(
        language=args.language,
        version=args.version,
        output_dir=args.output,
        split=args.split
    )


if __name__ == "__main__":
    main()
