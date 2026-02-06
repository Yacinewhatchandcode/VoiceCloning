#!/usr/bin/env python3
"""
Prépare le dataset StarConnect pour F5-TTS training sur Colab.
"""

import json
import os
import shutil
from pathlib import Path
from tqdm import tqdm


def prepare_starconnect_dataset(
    source_dir: str,
    output_dir: str,
    min_duration: float = 0.5,
    max_duration: float = 20.0
):
    """
    Prépare le dataset StarConnect pour F5-TTS.
    
    Args:
        source_dir: Répertoire source (StarConnect)
        output_dir: Répertoire de sortie
        min_duration: Durée minimale (secondes)
        max_duration: Durée maximale (secondes)
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Créer structure
    audio_dir = output_path / "wavs"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Source: {source_path}")
    print(f"📂 Output: {output_path}")
    
    # Lire transcriptions combinées
    combined_file = source_path / "combined_transcriptions.json"
    
    if combined_file.exists():
        print(f"✅ Fichier combiné trouvé: {combined_file}")
        with open(combined_file, 'r', encoding='utf-8') as f:
            transcriptions = json.load(f)
    else:
        print("⚠️  Pas de fichier combiné, lecture des fichiers individuels...")
        transcriptions = []
        
        # Lire tous les fichiers de transcription
        for trans_file in sorted(source_path.glob("segment_*_transcription.json")):
            with open(trans_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Trouver le fichier audio correspondant
                segment_num = trans_file.stem.replace("_transcription", "")
                audio_file = source_path / f"{segment_num}.wav"
                
                if audio_file.exists():
                    transcriptions.append({
                        "text": data.get("text", ""),
                        "file": str(audio_file),
                        "duration": data.get("duration", 0)
                    })
    
    print(f"📊 Total segments trouvés: {len(transcriptions)}")
    
    # Filtrer et préparer
    metadata = []
    valid_count = 0
    skipped_count = 0
    
    for idx, item in enumerate(tqdm(transcriptions, desc="Traitement")):
        text = item.get("text", "").strip()
        duration = item.get("duration", 0)
        
        # Filtrer par durée
        if duration < min_duration or duration > max_duration:
            skipped_count += 1
            continue
        
        # Filtrer texte vide
        if not text or len(text) < 3:
            skipped_count += 1
            continue
        
        # Trouver fichier audio source
        if "file" in item:
            # Chemin depuis combined_transcriptions
            source_audio = source_path / Path(item["file"]).name
        else:
            # Construire depuis segment number
            source_audio = source_path / f"segment_{idx+1:03d}.wav"
        
        if not source_audio.exists():
            # Essayer sans padding
            source_audio = source_path / f"segment_{idx+1}.wav"
        
        if not source_audio.exists():
            print(f"⚠️  Audio manquant: {source_audio}")
            skipped_count += 1
            continue
        
        # Copier audio
        target_audio = audio_dir / f"starconnect_{valid_count:04d}.wav"
        shutil.copy2(source_audio, target_audio)
        
        # Ajouter métadonnées
        metadata.append({
            "audio_path": f"wavs/{target_audio.name}",
            "text": text,
            "speaker": "starconnect",
            "language": "fr",
            "duration": duration
        })
        
        valid_count += 1
    
    print(f"\n✅ Segments valides: {valid_count}")
    print(f"⚠️  Segments ignorés: {skipped_count}")
    
    # Sauvegarder métadonnées
    metadata_file = output_path / "metadata.jsonl"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        for item in metadata:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"✅ Métadonnées: {metadata_file}")
    
    # Créer fichier de stats
    stats = {
        "total_segments": len(transcriptions),
        "valid_segments": valid_count,
        "skipped_segments": skipped_count,
        "total_duration": sum(item["duration"] for item in metadata),
        "avg_duration": sum(item["duration"] for item in metadata) / valid_count if valid_count > 0 else 0,
        "language": "fr",
        "speaker": "starconnect"
    }
    
    stats_file = output_path / "stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Statistiques:")
    print(f"   Durée totale: {stats['total_duration']:.1f}s ({stats['total_duration']/60:.1f} min)")
    print(f"   Durée moyenne: {stats['avg_duration']:.2f}s")
    print(f"   Segments: {valid_count}")
    
    # Créer README
    readme = f"""# StarConnect Dataset (F5-TTS Ready)

## Statistiques

- **Segments valides**: {valid_count}
- **Durée totale**: {stats['total_duration']/60:.1f} minutes
- **Durée moyenne**: {stats['avg_duration']:.2f} secondes
- **Langue**: Français
- **Speaker**: StarConnect

## Structure

```
{output_path.name}/
├── wavs/                    # Fichiers audio
│   ├── starconnect_0000.wav
│   ├── starconnect_0001.wav
│   └── ...
├── metadata.jsonl          # Métadonnées (1 ligne par segment)
├── stats.json              # Statistiques
└── README.md               # Ce fichier
```

## Format metadata.jsonl

Chaque ligne est un JSON avec:
- `audio_path`: Chemin relatif vers l'audio
- `text`: Transcription
- `speaker`: ID du speaker
- `language`: Code langue (fr)
- `duration`: Durée en secondes

## Utilisation avec F5-TTS

### Sur Colab

1. Uploader ce dossier sur Google Drive
2. Utiliser l'agent Colab pour lancer le training

### Localement

```bash
python train.py \\
  --dataset_path {output_path} \\
  --languages fr \\
  --epochs 200
```
"""
    
    readme_file = output_path / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"✅ README: {readme_file}")
    print(f"\n🎉 Dataset prêt: {output_path}")
    
    return valid_count, stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prépare StarConnect pour F5-TTS")
    parser.add_argument(
        "--source",
        default="/Users/yacinebenhamou/VoiceCloning/StarConnect",
        help="Répertoire source"
    )
    parser.add_argument(
        "--output",
        default="/Users/yacinebenhamou/VoiceCloning/datasets/starconnect_f5tts",
        help="Répertoire de sortie"
    )
    parser.add_argument(
        "--min-duration",
        type=float,
        default=0.5,
        help="Durée minimale (secondes)"
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=20.0,
        help="Durée maximale (secondes)"
    )
    
    args = parser.parse_args()
    
    count, stats = prepare_starconnect_dataset(
        args.source,
        args.output,
        args.min_duration,
        args.max_duration
    )
    
    print(f"\n✅ {count} segments préparés avec succès!")
