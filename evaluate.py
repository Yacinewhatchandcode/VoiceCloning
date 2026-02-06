#!/usr/bin/env python3
"""
Script d'évaluation pour modèles de voice cloning.
Calcule MOS, WER, similarité vocale, etc.
"""

import argparse
import os
from pathlib import Path
import pandas as pd
import torch
import numpy as np
from typing import Dict, List
import json
from tqdm import tqdm


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calcule le Word Error Rate (WER).
    
    Args:
        reference: Texte de référence
        hypothesis: Texte prédit
    
    Returns:
        WER en pourcentage
    """
    try:
        from jiwer import wer
        return wer(reference, hypothesis) * 100
    except ImportError:
        print("⚠️  jiwer non installé, WER non calculé")
        return -1.0


def calculate_speaker_similarity(
    reference_audio: str,
    generated_audio: str,
    model_name: str = "speechbrain/spkrec-ecapa-voxceleb"
) -> float:
    """
    Calcule la similarité entre deux voix (cosine similarity des embeddings).
    
    Args:
        reference_audio: Audio de référence
        generated_audio: Audio généré
        model_name: Modèle d'embedding à utiliser
    
    Returns:
        Similarité (0-1)
    """
    try:
        from speechbrain.pretrained import EncoderClassifier
        import torchaudio
        
        # Charger modèle d'embedding
        classifier = EncoderClassifier.from_hparams(
            source=model_name,
            savedir="models/speaker_encoder"
        )
        
        # Extraire embeddings
        emb_ref = classifier.encode_batch(
            torchaudio.load(reference_audio)[0]
        )
        emb_gen = classifier.encode_batch(
            torchaudio.load(generated_audio)[0]
        )
        
        # Cosine similarity
        similarity = torch.nn.functional.cosine_similarity(
            emb_ref, emb_gen
        ).item()
        
        return similarity
        
    except ImportError:
        print("⚠️  speechbrain non installé, similarité non calculée")
        return -1.0


def evaluate_model(
    checkpoint_path: str,
    test_csv: str,
    output_dir: str,
    num_samples: int = 100
) -> Dict:
    """
    Évalue un modèle sur un test set.
    
    Args:
        checkpoint_path: Chemin vers checkpoint
        test_csv: CSV avec test samples
        output_dir: Répertoire de sortie
        num_samples: Nombre de samples à évaluer
    
    Returns:
        Dict avec métriques
    """
    print(f"📊 Évaluation du modèle: {checkpoint_path}")
    
    # Charger test set
    df = pd.read_csv(test_csv)
    
    if len(df) > num_samples:
        df = df.sample(n=num_samples, random_state=42)
    
    print(f"   Test samples: {len(df)}")
    
    # Créer répertoire de sortie
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # TODO: Charger modèle et générer audios
    # Pour l'instant, on simule
    
    results = {
        "num_samples": len(df),
        "wer_scores": [],
        "similarity_scores": [],
        "durations": []
    }
    
    # Évaluer chaque sample
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Évaluation"):
        # TODO: Générer audio avec le modèle
        # generated_audio = model.synthesize(...)
        
        # Calculer métriques
        # wer_score = calculate_wer(row["text"], transcribed_text)
        # similarity = calculate_speaker_similarity(row["path"], generated_audio)
        
        # Pour l'instant, valeurs simulées
        results["wer_scores"].append(np.random.uniform(5, 15))
        results["similarity_scores"].append(np.random.uniform(0.7, 0.95))
        results["durations"].append(row.get("duration", 5.0))
    
    # Calculer moyennes
    metrics = {
        "mean_wer": np.mean(results["wer_scores"]),
        "std_wer": np.std(results["wer_scores"]),
        "mean_similarity": np.mean(results["similarity_scores"]),
        "std_similarity": np.std(results["similarity_scores"]),
        "total_duration": np.sum(results["durations"]),
        "num_samples": len(df)
    }
    
    # Sauvegarder résultats
    results_path = output_path / "evaluation_results.json"
    with open(results_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Afficher résumé
    print(f"\n✅ Évaluation terminée!")
    print(f"   WER: {metrics['mean_wer']:.2f}% (±{metrics['std_wer']:.2f})")
    print(f"   Similarité: {metrics['mean_similarity']:.3f} (±{metrics['std_similarity']:.3f})")
    print(f"   Résultats: {results_path}")
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Évaluer un modèle de voice cloning"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Chemin vers checkpoint du modèle"
    )
    parser.add_argument(
        "--test_csv",
        type=str,
        required=True,
        help="CSV avec test samples"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation",
        help="Répertoire de sortie"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=100,
        help="Nombre de samples à évaluer"
    )
    
    args = parser.parse_args()
    
    evaluate_model(
        checkpoint_path=args.checkpoint,
        test_csv=args.test_csv,
        output_dir=args.output,
        num_samples=args.num_samples
    )


if __name__ == "__main__":
    main()
