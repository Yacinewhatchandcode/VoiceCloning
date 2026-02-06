#!/usr/bin/env python3
"""
Agent RunPod pour orchestration F5-TTS sur RunPod.io.
Provision de pods GPU avec API RunPod.
"""

import requests
import time
from typing import Dict, Optional, List
import json


class RunPodAgent:
    """Agent pour provisionner et gérer des pods GPU sur RunPod."""
    
    API_BASE = "https://api.runpod.io/v2"
    
    # Types de GPU disponibles
    GPU_TYPES = {
        'rtx-4090': 'RTX 4090 (24GB)',
        'rtx-a6000': 'RTX A6000 (48GB)',
        'a100-80gb': 'A100 (80GB)',
        'a100-40gb': 'A100 (40GB)',
        'h100': 'H100 (80GB)'
    }
    
    def __init__(self, api_key: str):
        """
        Initialise l'agent RunPod.
        
        Args:
            api_key: Clé API RunPod
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"✅ Agent RunPod initialisé")
    
    def create_training_pod(
        self,
        name: str,
        gpu_type: str = 'rtx-4090',
        gpu_count: int = 1,
        docker_image: str = 'swivid/f5-tts:latest',
        dataset_path: str = '/workspace/dataset',
        languages: List[str] = ['fr', 'ar'],
        epochs: int = 200,
        batch_size: int = 2,
        volume_size_gb: int = 50
    ) -> Dict:
        """
        Crée un pod GPU pour training F5-TTS.
        
        Args:
            name: Nom du pod
            gpu_type: Type de GPU
            gpu_count: Nombre de GPUs
            docker_image: Image Docker
            dataset_path: Chemin du dataset dans le pod
            languages: Langues à entraîner
            epochs: Nombre d'epochs
            batch_size: Taille de batch
            volume_size_gb: Taille du volume persistant
        
        Returns:
            Informations du pod créé
        """
        print(f"🚀 Création du pod: {name}")
        print(f"   GPU: {gpu_count}x {gpu_type}")
        print(f"   Image: {docker_image}")
        
        # Commande de training
        langs_str = ' '.join(languages)
        command = [
            "bash", "-c",
            f"python train.py --dataset_path {dataset_path} "
            f"--multilingual true --languages {langs_str} "
            f"--epochs {epochs} --batch_size {batch_size} --device cuda"
        ]
        
        # Configuration du pod
        payload = {
            "name": name,
            "imageName": docker_image,
            "gpuTypeId": gpu_type,
            "gpuCount": gpu_count,
            "volumeInGb": volume_size_gb,
            "containerDiskInGb": 20,
            "minVcpuCount": 4,
            "minMemoryInGb": 16,
            "dockerArgs": " ".join(command),
            "ports": "8888/http",  # Jupyter si besoin
            "volumeMountPath": "/workspace",
            "env": [
                {"key": "DATASET", "value": dataset_path},
                {"key": "LANGUAGES", "value": ','.join(languages)},
                {"key": "EPOCHS", "value": str(epochs)},
                {"key": "BATCH_SIZE", "value": str(batch_size)}
            ]
        }
        
        try:
            response = requests.post(
                f"{self.API_BASE}/pods",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            pod = response.json()
            
            print(f"✅ Pod créé")
            print(f"   ID: {pod.get('id')}")
            print(f"   Status: {pod.get('status')}")
            
            return pod
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Détails: {e.response.text}")
            raise
    
    def get_pod_status(self, pod_id: str) -> Optional[Dict]:
        """Récupère le statut d'un pod."""
        try:
            response = requests.get(
                f"{self.API_BASE}/pods/{pod_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            pod = response.json()
            
            print(f"📊 Pod: {pod_id}")
            print(f"   Status: {pod.get('status')}")
            print(f"   Runtime: {pod.get('runtime', {}).get('uptimeInSeconds', 0)}s")
            
            return pod
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def list_pods(self) -> List[Dict]:
        """Liste tous les pods actifs."""
        try:
            response = requests.get(
                f"{self.API_BASE}/pods",
                headers=self.headers
            )
            response.raise_for_status()
            
            pods = response.json()
            
            print(f"📋 Pods actifs: {len(pods)}")
            for pod in pods:
                print(f"   - {pod.get('name')} ({pod.get('id')}): {pod.get('status')}")
            
            return pods
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def stop_pod(self, pod_id: str) -> bool:
        """Arrête un pod."""
        print(f"🛑 Arrêt du pod: {pod_id}")
        
        try:
            response = requests.post(
                f"{self.API_BASE}/pods/{pod_id}/stop",
                headers=self.headers
            )
            response.raise_for_status()
            
            print(f"✅ Pod arrêté")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def terminate_pod(self, pod_id: str) -> bool:
        """Termine (supprime) un pod."""
        print(f"🗑️  Suppression du pod: {pod_id}")
        
        try:
            response = requests.delete(
                f"{self.API_BASE}/pods/{pod_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            print(f"✅ Pod supprimé")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def get_logs(self, pod_id: str) -> str:
        """Récupère les logs d'un pod."""
        try:
            response = requests.get(
                f"{self.API_BASE}/pods/{pod_id}/logs",
                headers=self.headers
            )
            response.raise_for_status()
            
            logs = response.text
            print(f"📜 Logs du pod {pod_id}:")
            print(logs)
            
            return logs
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            return ""
    
    def monitor(self, pod_id: str, interval: int = 30, max_duration: int = 3600):
        """
        Surveille un pod en temps réel.
        
        Args:
            pod_id: ID du pod
            interval: Intervalle de polling (secondes)
            max_duration: Durée max de monitoring (secondes)
        """
        print(f"👁️  Monitoring du pod: {pod_id}")
        
        start_time = time.time()
        
        while time.time() - start_time < max_duration:
            status = self.get_pod_status(pod_id)
            
            if not status:
                print("❌ Pod non trouvé")
                break
            
            pod_status = status.get('status')
            
            if pod_status == 'COMPLETED':
                print("✅ Training terminé!")
                break
            
            if pod_status == 'FAILED':
                print(f"❌ Erreur: {status.get('error', 'Unknown')}")
                break
            
            time.sleep(interval)
        
        print("Monitoring terminé")


def main():
    """Exemple d'utilisation."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Agent RunPod F5-TTS")
    parser.add_argument("--api_key", default=os.getenv('RUNPOD_API_KEY'), help="RunPod API key")
    parser.add_argument("--action", choices=["create", "status", "list", "stop", "terminate", "logs", "monitor"], required=True)
    parser.add_argument("--pod_id", help="Pod ID")
    parser.add_argument("--name", help="Pod name (for create)")
    parser.add_argument("--gpu", default="rtx-4090", help="GPU type")
    parser.add_argument("--image", default="swivid/f5-tts:latest", help="Docker image")
    parser.add_argument("--dataset", default="/workspace/dataset", help="Dataset path")
    parser.add_argument("--languages", nargs="+", default=["fr", "ar"])
    parser.add_argument("--epochs", type=int, default=200)
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("❌ API key requis (--api_key ou RUNPOD_API_KEY)")
        return
    
    agent = RunPodAgent(api_key=args.api_key)
    
    if args.action == "create":
        if not args.name:
            print("❌ --name requis pour create")
            return
        agent.create_training_pod(
            name=args.name,
            gpu_type=args.gpu,
            docker_image=args.image,
            dataset_path=args.dataset,
            languages=args.languages,
            epochs=args.epochs
        )
    
    elif args.action == "status":
        if not args.pod_id:
            print("❌ --pod_id requis")
            return
        agent.get_pod_status(args.pod_id)
    
    elif args.action == "list":
        agent.list_pods()
    
    elif args.action == "stop":
        if not args.pod_id:
            print("❌ --pod_id requis")
            return
        agent.stop_pod(args.pod_id)
    
    elif args.action == "terminate":
        if not args.pod_id:
            print("❌ --pod_id requis")
            return
        agent.terminate_pod(args.pod_id)
    
    elif args.action == "logs":
        if not args.pod_id:
            print("❌ --pod_id requis")
            return
        agent.get_logs(args.pod_id)
    
    elif args.action == "monitor":
        if not args.pod_id:
            print("❌ --pod_id requis")
            return
        agent.monitor(args.pod_id)


if __name__ == "__main__":
    main()
