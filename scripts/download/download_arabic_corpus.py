#!/usr/bin/env python3
"""
Script de téléchargement pour Arabic Speech Corpus (MSA).
Dataset single-speaker haute qualité pour TTS arabe.
"""

import argparse
import os
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm
import pandas as pd
import soundfile as sf


def download_arabic_corpus(output_dir: str):
    """
    Télécharge Arabic Speech Corpus depuis HuggingFace.
    
    Args:
        output_dir: Répertoire de sortie
    """
    print("🚀 Téléchargement Arabic Speech Corpus (MSA)")
    
    # Créer répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Charger le dataset
        print("📥 Chargement depuis HuggingFace...")
        dataset = load_dataset(
            "tunis-ai/arabic_speech_corpus",
            split="train",
            trust_remote_code=True
        )
        
        print(f"💾 Sauvegarde de {len(dataset)} fichiers audio...")
        
        metadata = []
        audio_dir = output_path / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        for idx, item in enumerate(tqdm(dataset)):
            # Extraire les données
            audio_data = item["audio"]
            text = item["transcription"]
            
            # Nom de fichier
            filename = f"ar_msa_{idx:06d}.wav"
            audio_path = audio_dir / filename
            
            # Sauvegarder l'audio
            sf.write(
                str(audio_path),
                audio_data["array"],
                audio_data["sampling_rate"]
            )
            
            # Métadonnées
            metadata.append({
                "filename": filename,
                "path": str(audio_path),
                "text": text,
                "language": "ar",
                "dialect": "MSA",  # Modern Standard Arabic
                "speaker_id": "ar_msa_speaker_01",
                "duration": len(audio_data["array"]) / audio_data["sampling_rate"],
                "sample_rate": audio_data["sampling_rate"]
            })
        
        # Sauvegarder metadata
        df = pd.DataFrame(metadata)
        csv_path = output_path / "metadata.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        
        # Statistiques
        total_duration = df["duration"].sum()
        print(f"\n✅ Téléchargement terminé!")
        print(f"   Fichiers: {len(dataset)}")
        print(f"   Durée totale: {total_duration / 60:.1f} minutes")
        print(f"   Répertoire: {output_path}")
        print(f"   Metadata: {csv_path}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Télécharger Arabic Speech Corpus (MSA)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Répertoire de sortie"
    )
    
    args = parser.parse_args()
    download_arabic_corpus(args.output)


if __name__ == "__main__":
    main()
