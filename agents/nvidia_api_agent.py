#!/usr/bin/env python3
"""
Agent NVIDIA API pour voice cloning avec tes crédits gratuits.
Utilise ta clé API NVIDIA existante.
"""

import os
import requests
import base64
from typing import Optional, Dict
import json


class NVIDIAAPIAgent:
    """Agent pour utiliser NVIDIA API avec tes crédits gratuits."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'agent NVIDIA API.
        
        Args:
            api_key: Clé API NVIDIA (ou utilise variable d'environnement)
        """
        self.api_key = api_key or os.getenv('NVIDIA_API_KEY')
        
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY non trouvée. Définir dans ~/.zshrc ou passer en argument")
        
        # URLs API
        self.nim_api = os.getenv('NVIDIA_NIM_API', 'https://integrate.api.nvidia.com/v1')
        self.ngc_api = os.getenv('NVIDIA_NGC_API', 'https://api.ngc.nvidia.com/v2')
        
        # Organisation
        self.org_id = os.getenv('NVIDIA_ORG_ID', '787299')
        self.org_name = os.getenv('NVIDIA_ORG_NAME', 'Prime.AI')
        
        # Headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"✅ Agent NVIDIA API initialisé")
        print(f"   Organisation: {self.org_name} (ID: {self.org_id})")
        print(f"   NIM API: {self.nim_api}")
    
    def check_credits(self) -> Dict:
        """Vérifie les crédits API restants."""
        try:
            # Endpoint pour vérifier les crédits
            response = requests.get(
                f"{self.nim_api}/credits",
                headers=self.headers
            )
            
            if response.status_code == 200:
                credits = response.json()
                print(f"💰 Crédits restants: {credits}")
                return credits
            else:
                print(f"⚠️  Impossible de vérifier les crédits: {response.status_code}")
                return {"error": response.text}
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return {"error": str(e)}
    
    def list_models(self) -> list:
        """Liste les modèles disponibles."""
        try:
            response = requests.get(
                f"{self.nim_api}/models",
                headers=self.headers
            )
            
            if response.status_code == 200:
                models = response.json()
                print(f"📋 Modèles disponibles: {len(models.get('data', []))}")
                for model in models.get('data', [])[:5]:
                    print(f"   - {model.get('id', 'unknown')}")
                return models.get('data', [])
            else:
                print(f"⚠️  Erreur: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def text_to_speech(
        self,
        text: str,
        voice: str = "default",
        language: str = "fr",
        output_path: str = "output.wav"
    ) -> bool:
        """
        Génère de la parole à partir de texte.
        
        Args:
            text: Texte à synthétiser
            voice: Voix à utiliser
            language: Langue (fr, ar, en)
            output_path: Chemin de sortie
        
        Returns:
            True si succès
        """
        try:
            print(f"🎙️  Génération TTS...")
            print(f"   Texte: {text[:50]}...")
            print(f"   Langue: {language}")
            
            response = requests.post(
                f"{self.nim_api}/audio/speech",
                headers=self.headers,
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": voice,
                    "language": language
                }
            )
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio généré: {output_path}")
                return True
            else:
                print(f"❌ Erreur: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def clone_voice(
        self,
        reference_audio: str,
        text: str,
        language: str = "fr",
        output_path: str = "cloned.wav"
    ) -> bool:
        """
        Clone une voix à partir d'un échantillon.
        
        Args:
            reference_audio: Chemin vers audio de référence
            text: Texte à synthétiser
            language: Langue
            output_path: Chemin de sortie
        
        Returns:
            True si succès
        """
        try:
            print(f"🎙️  Clonage de voix...")
            print(f"   Référence: {reference_audio}")
            print(f"   Texte: {text[:50]}...")
            
            # Encoder audio en base64
            with open(reference_audio, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode()
            
            response = requests.post(
                f"{self.nim_api}/audio/clone",
                headers=self.headers,
                json={
                    "text": text,
                    "voice_reference": audio_b64,
                    "language": language,
                    "model": "voice-clone-1"
                }
            )
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Voix clonée: {output_path}")
                return True
            else:
                print(f"❌ Erreur: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def get_usage_stats(self) -> Dict:
        """Récupère les statistiques d'utilisation."""
        try:
            response = requests.get(
                f"{self.nim_api}/usage",
                headers=self.headers
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"📊 Statistiques d'utilisation:")
                print(json.dumps(stats, indent=2))
                return stats
            else:
                print(f"⚠️  Erreur: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return {}


def main():
    """Exemple d'utilisation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent NVIDIA API")
    parser.add_argument("--action", choices=["credits", "models", "tts", "clone", "stats"], required=True)
    parser.add_argument("--text", help="Texte à synthétiser")
    parser.add_argument("--reference", help="Audio de référence pour clonage")
    parser.add_argument("--language", default="fr", help="Langue (fr, ar, en)")
    parser.add_argument("--output", default="output.wav", help="Fichier de sortie")
    
    args = parser.parse_args()
    
    # Créer agent
    agent = NVIDIAAPIAgent()
    
    if args.action == "credits":
        agent.check_credits()
    
    elif args.action == "models":
        agent.list_models()
    
    elif args.action == "tts":
        if not args.text:
            print("❌ --text requis pour TTS")
            return
        agent.text_to_speech(
            text=args.text,
            language=args.language,
            output_path=args.output
        )
    
    elif args.action == "clone":
        if not args.text or not args.reference:
            print("❌ --text et --reference requis pour clonage")
            return
        agent.clone_voice(
            reference_audio=args.reference,
            text=args.text,
            language=args.language,
            output_path=args.output
        )
    
    elif args.action == "stats":
        agent.get_usage_stats()


if __name__ == "__main__":
    main()
