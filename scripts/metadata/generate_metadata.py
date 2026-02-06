#!/usr/bin/env python3
"""
Générateur de metadata multilingue pour datasets de voice cloning.
Supporte Common Voice, Arabic Corpus, et formats personnalisés.
"""

import argparse
import os
from pathlib import Path
import pandas as pd
from typing import List, Dict
import json


def generate_commonvoice_metadata(
    dataset_dir: str,
    language: str,
    output_path: str
) -> pd.DataFrame:
    """
    Génère metadata pour Common Voice.
    
    Args:
        dataset_dir: Répertoire du dataset
        language: Code langue (fr, ar)
        output_path: Chemin de sortie CSV
    
    Returns:
        DataFrame avec metadata
    """
    print(f"📋 Génération metadata Common Voice ({language})")
    
    dataset_path = Path(dataset_dir)
    all_metadata = []
    
    # Parcourir les splits (train, validation, test)
    for split_dir in dataset_path.iterdir():
        if not split_dir.is_dir():
            continue
        
        # Chercher metadata.csv existant
        csv_path = split_dir / "metadata.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            all_metadata.append(df)
        else:
            # Générer depuis les fichiers audio
            audio_files = list(split_dir.glob("*.wav"))
            for audio_file in audio_files:
                all_metadata.append({
                    "filename": audio_file.name,
                    "path": str(audio_file),
                    "language": language,
                    "split": split_dir.name
                })
    
    # Fusionner
    if all_metadata:
        if isinstance(all_metadata[0], pd.DataFrame):
            df = pd.concat(all_metadata, ignore_index=True)
        else:
            df = pd.DataFrame(all_metadata)
        
        # Ajouter token de langue
        df["text_with_lang"] = df.apply(
            lambda row: f"<{row['language']}> {row.get('text', '')}",
            axis=1
        )
        
        # Sauvegarder
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"✅ Metadata générée: {len(df)} entrées → {output_path}")
        return df
    
    return pd.DataFrame()


def merge_multilingual_metadata(
    metadata_files: List[str],
    output_path: str,
    train_split: float = 0.9,
    val_split: float = 0.05,
    test_split: float = 0.05
) -> Dict[str, pd.DataFrame]:
    """
    Fusionne plusieurs metadata multilingues et crée splits train/val/test.
    
    Args:
        metadata_files: Liste de chemins CSV
        output_path: Répertoire de sortie
        train_split: Proportion train
        val_split: Proportion validation
        test_split: Proportion test
    
    Returns:
        Dict avec DataFrames {train, val, test}
    """
    print(f"🔗 Fusion de {len(metadata_files)} fichiers metadata")
    
    # Charger tous les CSV
    dfs = []
    for csv_file in metadata_files:
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            dfs.append(df)
            print(f"   ✓ {csv_file}: {len(df)} entrées")
    
    # Fusionner
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"📊 Total: {len(merged_df)} entrées")
    
    # Statistiques par langue
    if "language" in merged_df.columns:
        lang_counts = merged_df["language"].value_counts()
        print("\n🌍 Distribution par langue:")
        for lang, count in lang_counts.items():
            print(f"   {lang}: {count} ({count/len(merged_df)*100:.1f}%)")
    
    # Créer splits
    from sklearn.model_selection import train_test_split
    
    # Split train/temp
    train_df, temp_df = train_test_split(
        merged_df,
        train_size=train_split,
        random_state=42,
        stratify=merged_df["language"] if "language" in merged_df.columns else None
    )
    
    # Split val/test
    val_ratio = val_split / (val_split + test_split)
    val_df, test_df = train_test_split(
        temp_df,
        train_size=val_ratio,
        random_state=42,
        stratify=temp_df["language"] if "language" in temp_df.columns else None
    )
    
    # Sauvegarder
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    splits = {
        "train": train_df,
        "val": val_df,
        "test": test_df
    }
    
    for split_name, split_df in splits.items():
        csv_path = output_dir / f"{split_name}.csv"
        split_df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"   ✓ {split_name}: {len(split_df)} → {csv_path}")
    
    # Sauvegarder stats
    stats = {
        "total_samples": len(merged_df),
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "languages": lang_counts.to_dict() if "language" in merged_df.columns else {},
        "total_duration_hours": merged_df["duration"].sum() / 3600 if "duration" in merged_df.columns else 0
    }
    
    stats_path = output_dir / "stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fusion terminée!")
    print(f"   Répertoire: {output_dir}")
    print(f"   Stats: {stats_path}")
    
    return splits


def main():
    parser = argparse.ArgumentParser(
        description="Générer metadata pour datasets de voice cloning"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commande")
    
    # Commande: generate
    gen_parser = subparsers.add_parser("generate", help="Générer metadata")
    gen_parser.add_argument("--dataset", type=str, required=True, help="Type de dataset")
    gen_parser.add_argument("--input", type=str, required=True, help="Répertoire dataset")
    gen_parser.add_argument("--language", type=str, required=True, help="Code langue")
    gen_parser.add_argument("--output", type=str, required=True, help="Fichier CSV de sortie")
    
    # Commande: merge
    merge_parser = subparsers.add_parser("merge", help="Fusionner metadata")
    merge_parser.add_argument("--inputs", nargs="+", required=True, help="Fichiers CSV à fusionner")
    merge_parser.add_argument("--output", type=str, required=True, help="Répertoire de sortie")
    merge_parser.add_argument("--train_split", type=float, default=0.9, help="Proportion train")
    merge_parser.add_argument("--val_split", type=float, default=0.05, help="Proportion validation")
    merge_parser.add_argument("--test_split", type=float, default=0.05, help="Proportion test")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        if args.dataset == "commonvoice":
            generate_commonvoice_metadata(
                dataset_dir=args.input,
                language=args.language,
                output_path=args.output
            )
        else:
            print(f"❌ Dataset '{args.dataset}' non supporté")
    
    elif args.command == "merge":
        merge_multilingual_metadata(
            metadata_files=args.inputs,
            output_path=args.output,
            train_split=args.train_split,
            val_split=args.val_split,
            test_split=args.test_split
        )
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
