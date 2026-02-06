#!/usr/bin/env python3
"""
Interface de démonstration pour tester le clonage de voix.
Permet de cloner une voix à partir d'un échantillon de référence.
"""

import argparse
import os
from pathlib import Path
import torch
import soundfile as sf
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceCloner:
    """Classe pour cloner des voix avec XTTS."""
    
    def __init__(self, checkpoint_path: str, config_path: str = None):
        """
        Initialise le cloner.
        
        Args:
            checkpoint_path: Chemin vers le checkpoint du modèle
            config_path: Chemin vers config (optionnel)
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🖥️  Device: {self.device}")
        
        # Charger config
        if config_path and os.path.exists(config_path):
            self.config = XttsConfig()
            self.config.load_json(config_path)
        else:
            self.config = XttsConfig()
        
        # Charger modèle
        logger.info(f"📥 Chargement du modèle: {checkpoint_path}")
        self.model = Xtts.init_from_config(self.config)
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model"])
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info("✅ Modèle chargé avec succès")
    
    def clone_voice(
        self,
        reference_audio: str,
        text: str,
        language: str,
        output_path: str,
        temperature: float = 0.75,
        speed: float = 1.0
    ):
        """
        Clone une voix et génère un audio.
        
        Args:
            reference_audio: Chemin vers audio de référence (5-15s recommandé)
            text: Texte à synthétiser
            language: Code langue (fr, ar)
            output_path: Chemin de sortie
            temperature: Température de sampling (0.5-1.0, défaut 0.75)
            speed: Vitesse de parole (0.5-2.0, défaut 1.0)
        """
        logger.info(f"🎙️  Clonage de voix...")
        logger.info(f"   Référence: {reference_audio}")
        logger.info(f"   Langue: {language}")
        logger.info(f"   Texte: {text[:50]}...")
        
        # Vérifier que la référence existe
        if not os.path.exists(reference_audio):
            raise FileNotFoundError(f"Audio de référence introuvable: {reference_audio}")
        
        # Générer
        with torch.no_grad():
            outputs = self.model.synthesize(
                text=text,
                config=self.config,
                speaker_wav=reference_audio,
                language=language,
                temperature=temperature,
                speed=speed
            )
        
        # Sauvegarder
        audio = outputs["wav"]
        sample_rate = self.config.sample_rate
        
        sf.write(output_path, audio, sample_rate)
        
        logger.info(f"✅ Audio généré: {output_path}")
        logger.info(f"   Durée: {len(audio) / sample_rate:.2f}s")
        
        return output_path
    
    def batch_clone(
        self,
        reference_audio: str,
        texts: list,
        language: str,
        output_dir: str,
        **kwargs
    ):
        """
        Clone une voix pour plusieurs textes.
        
        Args:
            reference_audio: Audio de référence
            texts: Liste de textes
            language: Code langue
            output_dir: Répertoire de sortie
            **kwargs: Arguments additionnels pour clone_voice
        
        Returns:
            Liste de chemins des audios générés
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        outputs = []
        
        for i, text in enumerate(texts):
            output_file = output_path / f"cloned_{i:03d}.wav"
            
            self.clone_voice(
                reference_audio=reference_audio,
                text=text,
                language=language,
                output_path=str(output_file),
                **kwargs
            )
            
            outputs.append(str(output_file))
        
        logger.info(f"✅ Batch terminé: {len(outputs)} audios générés")
        return outputs


def main():
    parser = argparse.ArgumentParser(
        description="Cloner une voix avec XTTS"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Chemin vers checkpoint du modèle"
    )
    parser.add_argument(
        "--reference_audio",
        type=str,
        required=True,
        help="Audio de référence pour clonage (5-15s recommandé)"
    )
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Texte à synthétiser"
    )
    parser.add_argument(
        "--language",
        type=str,
        required=True,
        choices=["fr", "ar"],
        help="Langue du texte"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Chemin de sortie pour l'audio généré"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.75,
        help="Température de sampling (0.5-1.0)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Vitesse de parole (0.5-2.0)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Chemin vers config (optionnel)"
    )
    
    args = parser.parse_args()
    
    # Créer cloner
    cloner = VoiceCloner(
        checkpoint_path=args.checkpoint,
        config_path=args.config
    )
    
    # Cloner voix
    cloner.clone_voice(
        reference_audio=args.reference_audio,
        text=args.text,
        language=args.language,
        output_path=args.output,
        temperature=args.temperature,
        speed=args.speed
    )


if __name__ == "__main__":
    main()
