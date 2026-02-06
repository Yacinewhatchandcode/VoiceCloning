#!/usr/bin/env python3
"""
Script d'entraînement principal pour voice cloning multilingue.
Supporte XTTS v2 avec fine-tuning sur datasets français et arabe.
"""

import argparse
import os
from pathlib import Path
import yaml
import torch
from torch.utils.data import DataLoader
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from TTS.tts.datasets import load_tts_samples
from TTS.utils.audio import AudioProcessor
from trainer import Trainer, TrainerArgs
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Charge la configuration YAML."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_model(config: dict) -> Xtts:
    """
    Initialise le modèle XTTS.
    
    Args:
        config: Configuration du modèle
    
    Returns:
        Modèle XTTS initialisé
    """
    logger.info("🚀 Initialisation du modèle XTTS v2")
    
    # Configuration XTTS
    model_config = XttsConfig()
    
    # Appliquer config custom
    model_cfg = config["model"]
    model_config.sample_rate = model_cfg["sample_rate"]
    model_config.languages = model_cfg["languages"]
    
    # Créer le modèle
    model = Xtts.init_from_config(model_config)
    
    # Charger checkpoint pré-entraîné si disponible
    pretrained_path = config.get("paths", {}).get("pretrained_checkpoint")
    if pretrained_path and os.path.exists(pretrained_path):
        logger.info(f"📥 Chargement checkpoint: {pretrained_path}")
        checkpoint = torch.load(pretrained_path, map_location="cpu")
        model.load_state_dict(checkpoint["model"])
    else:
        logger.info("⚠️  Pas de checkpoint pré-entraîné, démarrage from scratch")
    
    return model


def setup_datasets(config: dict):
    """
    Prépare les datasets d'entraînement et validation.
    
    Args:
        config: Configuration des données
    
    Returns:
        Tuple (train_samples, val_samples)
    """
    logger.info("📊 Chargement des datasets")
    
    data_cfg = config["data"]
    
    # Charger metadata
    train_samples = load_tts_samples(
        data_cfg["train_csv"],
        eval_split=False
    )
    
    val_samples = load_tts_samples(
        data_cfg["val_csv"],
        eval_split=True
    )
    
    logger.info(f"   Train: {len(train_samples)} samples")
    logger.info(f"   Val: {len(val_samples)} samples")
    
    # Filtrer par durée
    min_len = data_cfg["min_audio_length"]
    max_len = data_cfg["max_audio_length"]
    
    train_samples = [
        s for s in train_samples
        if min_len <= s.get("duration", 0) <= max_len
    ]
    val_samples = [
        s for s in val_samples
        if min_len <= s.get("duration", 0) <= max_len
    ]
    
    logger.info(f"   Après filtrage - Train: {len(train_samples)}, Val: {len(val_samples)}")
    
    return train_samples, val_samples


def train(config_path: str, resume_from: str = None):
    """
    Lance l'entraînement.
    
    Args:
        config_path: Chemin vers config YAML
        resume_from: Chemin vers checkpoint pour reprendre (optionnel)
    """
    # Charger config
    config = load_config(config_path)
    
    # Setup device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"🖥️  Device: {device}")
    
    # Créer répertoires de sortie
    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_dir = Path(config["paths"]["log_dir"])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup model
    model = setup_model(config)
    model = model.to(device)
    
    # Setup datasets
    train_samples, val_samples = setup_datasets(config)
    
    # Configuration du trainer
    train_cfg = config["training"]
    
    trainer_args = TrainerArgs(
        output_path=str(output_dir),
        log_path=str(log_dir),
        
        # Training params
        epochs=train_cfg["epochs"],
        batch_size=train_cfg["batch_size"],
        learning_rate=train_cfg["learning_rate"],
        
        # Checkpointing
        save_step=train_cfg["save_every_n_steps"],
        eval_step=train_cfg["eval_every_n_steps"],
        keep_n_checkpoints=train_cfg["keep_n_checkpoints"],
        
        # Mixed precision
        use_fp16=train_cfg["use_fp16"],
        
        # Logging
        print_step=config["logging"]["log_every_n_steps"],
        dashboard_logger="tensorboard" if config["logging"]["use_tensorboard"] else None,
        
        # Reproducibility
        seed=config["seed"]
    )
    
    # Créer trainer
    trainer = Trainer(
        args=trainer_args,
        model=model,
        train_samples=train_samples,
        eval_samples=val_samples,
        training_assets=None
    )
    
    # Reprendre depuis checkpoint si demandé
    if resume_from:
        logger.info(f"🔄 Reprise depuis: {resume_from}")
        trainer.restore_checkpoint(resume_from)
    
    # Lancer entraînement
    logger.info("🎯 Démarrage de l'entraînement...")
    trainer.fit()
    
    logger.info("✅ Entraînement terminé!")
    logger.info(f"   Modèle sauvegardé: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Entraîner un modèle de voice cloning multilingue"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Chemin vers fichier de configuration YAML"
    )
    parser.add_argument(
        "--resume_from",
        type=str,
        help="Chemin vers checkpoint pour reprendre l'entraînement"
    )
    parser.add_argument(
        "--gpus",
        type=str,
        help="GPU IDs à utiliser (ex: 0,1)"
    )
    
    args = parser.parse_args()
    
    # Setup GPU
    if args.gpus:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus
    
    # Lancer entraînement
    train(
        config_path=args.config,
        resume_from=args.resume_from
    )


if __name__ == "__main__":
    main()
