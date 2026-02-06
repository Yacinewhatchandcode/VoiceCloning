#!/usr/bin/env python3
"""
Agent Colab pour orchestration F5-TTS via Google Drive.
Écrit des triggers dans Drive pour déclencher training sur Colab.
"""

import json
import io
import os
from pathlib import Path
from typing import Dict, List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import time


class ColabAgent:
    """Agent pour contrôler training F5-TTS sur Google Colab via Drive."""
    
    def __init__(
        self,
        credentials_path: str,
        drive_folder_name: str = "f5_tts_orchestration"
    ):
        """
        Initialise l'agent Colab.
        
        Args:
            credentials_path: Chemin vers service account JSON
            drive_folder_name: Nom du dossier Drive pour triggers
        """
        # Authentification
        SCOPES = ['https://www.googleapis.com/auth/drive']
        self.creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=SCOPES
        )
        
        self.drive = build('drive', 'v3', credentials=self.creds)
        self.folder_name = drive_folder_name
        self.folder_id = self._get_or_create_folder()
        
        print(f"✅ Agent Colab initialisé")
        print(f"   Dossier Drive: {drive_folder_name} (ID: {self.folder_id})")
    
    def _get_or_create_folder(self) -> str:
        """Récupère ou crée le dossier Drive."""
        # Chercher dossier existant
        query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Créer nouveau dossier
        file_metadata = {
            'name': self.folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.drive.files().create(body=file_metadata, fields='id').execute()
        return folder['id']
    
    def _upload_json(self, filename: str, data: Dict) -> str:
        """Upload un fichier JSON dans Drive."""
        # Supprimer ancien fichier si existe
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
        results = self.drive.files().list(q=query, fields="files(id)").execute()
        for file in results.get('files', []):
            self.drive.files().delete(fileId=file['id']).execute()
        
        # Upload nouveau fichier
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id]
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')),
            mimetype='application/json'
        )
        
        file = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return file['id']
    
    def _download_json(self, filename: str) -> Optional[Dict]:
        """Télécharge un fichier JSON depuis Drive."""
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"
        results = self.drive.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        if not files:
            return None
        
        request = self.drive.files().get_media(fileId=files[0]['id'])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        return json.load(fh)
    
    def start_training(
        self,
        languages: List[str],
        dataset_path: str,
        epochs: int = 200,
        batch_size: int = 2,
        gpu_type: str = "T4",
        learning_rate: float = 1e-5,
        checkpoint_interval: int = 5000
    ) -> str:
        """
        Démarre un training F5-TTS sur Colab.
        
        Args:
            languages: Liste de langues (ex: ['fr', 'ar'])
            dataset_path: Chemin GCS vers dataset (gs://...)
            epochs: Nombre d'epochs
            batch_size: Taille de batch
            gpu_type: Type de GPU suggéré (T4, V100, A100)
            learning_rate: Learning rate
            checkpoint_interval: Intervalle de sauvegarde
        
        Returns:
            Job ID
        """
        job_id = f"job_{int(time.time())}"
        
        trigger_data = {
            "job_id": job_id,
            "status": "pending",
            "config": {
                "languages": languages,
                "dataset_path": dataset_path,
                "epochs": epochs,
                "batch_size": batch_size,
                "gpu_type": gpu_type,
                "learning_rate": learning_rate,
                "checkpoint_interval": checkpoint_interval
            },
            "created_at": time.time()
        }
        
        self._upload_json("trigger.json", trigger_data)
        
        print(f"🚀 Training démarré!")
        print(f"   Job ID: {job_id}")
        print(f"   Langues: {', '.join(languages)}")
        print(f"   Dataset: {dataset_path}")
        print(f"   Epochs: {epochs}")
        
        return job_id
    
    def get_status(self) -> Optional[Dict]:
        """Récupère le statut du training en cours."""
        status = self._download_json("status.json")
        
        if status:
            print(f"📊 Statut: {status.get('status', 'unknown')}")
            if 'epoch' in status:
                print(f"   Epoch: {status['epoch']}/{status.get('total_epochs', '?')}")
            if 'loss' in status:
                print(f"   Loss: {status['loss']:.4f}")
        
        return status
    
    def stop_training(self):
        """Arrête le training en cours."""
        stop_data = {
            "command": "stop",
            "timestamp": time.time()
        }
        
        self._upload_json("command.json", stop_data)
        print("🛑 Commande d'arrêt envoyée")
    
    def download_checkpoint(self, output_path: str) -> bool:
        """
        Télécharge le dernier checkpoint.
        
        Args:
            output_path: Chemin local de sauvegarde
        
        Returns:
            True si succès
        """
        # Chercher fichier checkpoint
        query = f"name contains 'checkpoint' and '{self.folder_id}' in parents and trashed=false"
        results = self.drive.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields="files(id, name, size)"
        ).execute()
        
        files = results.get('files', [])
        if not files:
            print("❌ Aucun checkpoint trouvé")
            return False
        
        checkpoint = files[0]
        print(f"📥 Téléchargement: {checkpoint['name']} ({checkpoint.get('size', '?')} bytes)")
        
        request = self.drive.files().get_media(fileId=checkpoint['id'])
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"   Progression: {int(status.progress() * 100)}%")
        
        print(f"✅ Checkpoint sauvegardé: {output_path}")
        return True
    
    def monitor(self, interval: int = 30, max_duration: int = 3600):
        """
        Surveille le training en temps réel.
        
        Args:
            interval: Intervalle de polling (secondes)
            max_duration: Durée max de monitoring (secondes)
        """
        print(f"👁️  Monitoring démarré (intervalle: {interval}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < max_duration:
            status = self.get_status()
            
            if status and status.get('status') == 'completed':
                print("✅ Training terminé!")
                break
            
            if status and status.get('status') == 'error':
                print(f"❌ Erreur: {status.get('error', 'Unknown')}")
                break
            
            time.sleep(interval)
        
        print("Monitoring terminé")


def main():
    """Exemple d'utilisation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Colab F5-TTS")
    parser.add_argument("--credentials", required=True, help="Service account JSON")
    parser.add_argument("--action", choices=["start", "status", "stop", "download", "monitor"], required=True)
    parser.add_argument("--languages", nargs="+", default=["fr", "ar"])
    parser.add_argument("--dataset", help="Dataset GCS path")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--output", help="Output path for checkpoint")
    
    args = parser.parse_args()
    
    agent = ColabAgent(credentials_path=args.credentials)
    
    if args.action == "start":
        if not args.dataset:
            print("❌ --dataset requis pour start")
            return
        agent.start_training(
            languages=args.languages,
            dataset_path=args.dataset,
            epochs=args.epochs
        )
    
    elif args.action == "status":
        agent.get_status()
    
    elif args.action == "stop":
        agent.stop_training()
    
    elif args.action == "download":
        if not args.output:
            print("❌ --output requis pour download")
            return
        agent.download_checkpoint(args.output)
    
    elif args.action == "monitor":
        agent.monitor()


if __name__ == "__main__":
    main()
