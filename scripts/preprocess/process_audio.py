#!/usr/bin/env python3
"""
Pipeline de prétraitement audio pour voice cloning.
Normalisation, resampling, nettoyage silences, et validation qualité.
"""

import argparse
import os
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import subprocess


class AudioProcessor:
    """Processeur audio avec pipeline complet de nettoyage."""
    
    def __init__(
        self,
        target_sr: int = 22050,
        trim_silence: bool = True,
        normalize: bool = True,
        noise_reduce: bool = False,
        min_duration: float = 1.0,
        max_duration: float = 15.0
    ):
        self.target_sr = target_sr
        self.trim_silence = trim_silence
        self.normalize = normalize
        self.noise_reduce = noise_reduce
        self.min_duration = min_duration
        self.max_duration = max_duration
    
    def process_file(self, input_path: str, output_path: str) -> Optional[dict]:
        """
        Traite un fichier audio unique.
        
        Returns:
            dict avec stats si succès, None si échec
        """
        try:
            # Charger l'audio
            audio, sr = librosa.load(input_path, sr=None, mono=True)
            
            # Vérifier durée
            duration = len(audio) / sr
            if duration < self.min_duration or duration > self.max_duration:
                return None
            
            # Resample si nécessaire
            if sr != self.target_sr:
                audio = librosa.resample(
                    audio,
                    orig_sr=sr,
                    target_sr=self.target_sr
                )
                sr = self.target_sr
            
            # Trim silence
            if self.trim_silence:
                audio, _ = librosa.effects.trim(
                    audio,
                    top_db=20,
                    frame_length=2048,
                    hop_length=512
                )
            
            # Normalisation
            if self.normalize:
                # Peak normalization
                peak = np.abs(audio).max()
                if peak > 0:
                    audio = audio / peak * 0.95
                
                # RMS normalization (optionnel)
                rms = np.sqrt(np.mean(audio ** 2))
                target_rms = 0.1
                if rms > 0:
                    audio = audio * (target_rms / rms)
                    # Re-clip pour éviter clipping
                    audio = np.clip(audio, -1.0, 1.0)
            
            # Réduction de bruit (optionnel, coûteux)
            if self.noise_reduce:
                try:
                    import noisereduce as nr
                    audio = nr.reduce_noise(y=audio, sr=sr)
                except ImportError:
                    pass
            
            # Sauvegarder
            sf.write(output_path, audio, sr, subtype='PCM_16')
            
            # Retourner stats
            return {
                "duration": len(audio) / sr,
                "sample_rate": sr,
                "samples": len(audio),
                "rms": float(np.sqrt(np.mean(audio ** 2))),
                "peak": float(np.abs(audio).max())
            }
            
        except Exception as e:
            print(f"❌ Erreur traitement {input_path}: {e}")
            return None


def process_dataset(
    input_dir: str,
    output_dir: str,
    metadata_csv: Optional[str] = None,
    target_sr: int = 22050,
    trim_silence: bool = True,
    normalize: bool = True,
    noise_reduce: bool = False,
    workers: int = 4
):
    """
    Traite un dataset complet en parallèle.
    
    Args:
        input_dir: Répertoire source
        output_dir: Répertoire destination
        metadata_csv: Chemin vers metadata.csv (optionnel)
        target_sr: Sample rate cible
        trim_silence: Activer trim des silences
        normalize: Activer normalisation
        noise_reduce: Activer réduction de bruit
        workers: Nombre de workers parallèles
    """
    print(f"🎵 Prétraitement audio: {input_dir}")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Créer processeur
    processor = AudioProcessor(
        target_sr=target_sr,
        trim_silence=trim_silence,
        normalize=normalize,
        noise_reduce=noise_reduce
    )
    
    # Trouver tous les fichiers audio
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(input_path.rglob(f"*{ext}"))
    
    print(f"📁 Fichiers trouvés: {len(audio_files)}")
    
    # Charger metadata si disponible
    metadata_df = None
    if metadata_csv and os.path.exists(metadata_csv):
        metadata_df = pd.read_csv(metadata_csv)
        print(f"📋 Metadata chargée: {len(metadata_df)} entrées")
    
    # Traiter en parallèle
    results = []
    processed_metadata = []
    
    def process_single(audio_file):
        # Créer chemin de sortie
        rel_path = audio_file.relative_to(input_path)
        output_file = output_path / rel_path.with_suffix(".wav")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Traiter
        stats = processor.process_file(str(audio_file), str(output_file))
        
        if stats:
            # Trouver metadata correspondante
            meta_row = None
            if metadata_df is not None:
                matches = metadata_df[metadata_df["filename"] == audio_file.name]
                if not matches.empty:
                    meta_row = matches.iloc[0].to_dict()
            
            return {
                "input_path": str(audio_file),
                "output_path": str(output_file),
                "filename": output_file.name,
                "stats": stats,
                "metadata": meta_row
            }
        return None
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_single, f) for f in audio_files]
        
        for future in tqdm(futures, desc="Traitement"):
            result = future.result()
            if result:
                results.append(result)
                
                # Construire nouvelle metadata
                new_meta = {
                    "filename": result["filename"],
                    "path": result["output_path"],
                    "duration": result["stats"]["duration"],
                    "sample_rate": result["stats"]["sample_rate"]
                }
                
                # Ajouter metadata originale si disponible
                if result["metadata"]:
                    new_meta.update({
                        "text": result["metadata"].get("text", ""),
                        "language": result["metadata"].get("language", ""),
                        "speaker_id": result["metadata"].get("speaker_id", "")
                    })
                
                processed_metadata.append(new_meta)
    
    # Sauvegarder nouvelle metadata
    if processed_metadata:
        new_df = pd.DataFrame(processed_metadata)
        new_csv = output_path / "metadata.csv"
        new_df.to_csv(new_csv, index=False, encoding="utf-8")
        
        # Statistiques
        total_duration = new_df["duration"].sum()
        print(f"\n✅ Traitement terminé!")
        print(f"   Fichiers traités: {len(results)} / {len(audio_files)}")
        print(f"   Durée totale: {total_duration / 60:.1f} minutes")
        print(f"   Sample rate: {target_sr} Hz")
        print(f"   Répertoire: {output_path}")
        print(f"   Metadata: {new_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Prétraiter des fichiers audio pour voice cloning"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Répertoire d'entrée"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Répertoire de sortie"
    )
    parser.add_argument(
        "--metadata",
        type=str,
        help="Chemin vers metadata.csv (optionnel)"
    )
    parser.add_argument(
        "--sample_rate",
        type=int,
        default=22050,
        help="Sample rate cible (défaut: 22050)"
    )
    parser.add_argument(
        "--trim_silence",
        action="store_true",
        default=True,
        help="Trim les silences"
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        default=True,
        help="Normaliser l'audio"
    )
    parser.add_argument(
        "--noise_reduce",
        action="store_true",
        help="Réduire le bruit (lent)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Nombre de workers parallèles"
    )
    
    args = parser.parse_args()
    
    process_dataset(
        input_dir=args.input,
        output_dir=args.output,
        metadata_csv=args.metadata,
        target_sr=args.sample_rate,
        trim_silence=args.trim_silence,
        normalize=args.normalize,
        noise_reduce=args.noise_reduce,
        workers=args.workers
    )


if __name__ == "__main__":
    main()
