#!/usr/bin/env python3
"""
Agent GCP pour orchestration F5-TTS sur Google Cloud Platform.
Provision de VM GPU avec startup script pour training automatisé.
"""

import time
from typing import Dict, Optional, List
from google.oauth2 import service_account
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import json


class GCPAgent:
    """Agent pour provisionner et gérer des instances GPU sur GCP."""
    
    # Types de GPU disponibles par zone
    GPU_TYPES = {
        'nvidia-tesla-t4': 'T4 (16GB, économique)',
        'nvidia-tesla-v100': 'V100 (16GB, performant)',
        'nvidia-tesla-a100': 'A100 (40GB, très performant)',
        'nvidia-l4': 'L4 (24GB, nouvelle génération)'
    }
    
    def __init__(
        self,
        project_id: str,
        zone: str = 'us-west1-b',
        credentials_path: str = 'gcp-sa.json'
    ):
        """
        Initialise l'agent GCP.
        
        Args:
            project_id: ID du projet GCP
            zone: Zone GCP (ex: us-west1-b, europe-west4-a)
            credentials_path: Chemin vers service account JSON
        """
        self.project_id = project_id
        self.zone = zone
        
        # Authentification
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        
        self.compute = discovery.build('compute', 'v1', credentials=self.credentials)
        
        print(f"✅ Agent GCP initialisé")
        print(f"   Projet: {project_id}")
        print(f"   Zone: {zone}")
    
    def create_training_instance(
        self,
        name: str,
        gpu_type: str = 'nvidia-tesla-t4',
        gpu_count: int = 1,
        machine_type: str = 'n1-standard-8',
        docker_image: str = None,
        dataset_gs: str = None,
        languages: List[str] = ['fr', 'ar'],
        epochs: int = 200,
        batch_size: int = 2,
        disk_size_gb: int = 100
    ) -> Dict:
        """
        Crée une instance GPU pour training F5-TTS.
        
        Args:
            name: Nom de l'instance
            gpu_type: Type de GPU (voir GPU_TYPES)
            gpu_count: Nombre de GPUs
            machine_type: Type de machine (n1-standard-8, n1-highmem-8, etc.)
            docker_image: Image Docker (ex: gcr.io/project/f5-tts:latest)
            dataset_gs: Chemin GCS du dataset (gs://bucket/path)
            languages: Langues à entraîner
            epochs: Nombre d'epochs
            batch_size: Taille de batch
            disk_size_gb: Taille du disque boot
        
        Returns:
            Opération de création
        """
        print(f"🚀 Création de l'instance: {name}")
        print(f"   GPU: {gpu_count}x {gpu_type}")
        print(f"   Machine: {machine_type}")
        
        # Startup script
        startup_script = self._generate_startup_script(
            docker_image=docker_image,
            dataset_gs=dataset_gs,
            languages=languages,
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Configuration de l'instance
        config = {
            "name": name,
            "machineType": f"zones/{self.zone}/machineTypes/{machine_type}",
            
            # Disque boot
            "disks": [{
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts",
                    "diskSizeGb": str(disk_size_gb)
                }
            }],
            
            # GPU
            "guestAccelerators": [{
                "acceleratorType": f"projects/{self.project_id}/zones/{self.zone}/acceleratorTypes/{gpu_type}",
                "acceleratorCount": gpu_count
            }],
            
            # Scheduling (requis pour GPU)
            "scheduling": {
                "onHostMaintenance": "TERMINATE",
                "automaticRestart": False
            },
            
            # Réseau
            "networkInterfaces": [{
                "network": "global/networks/default",
                "accessConfigs": [{
                    "type": "ONE_TO_ONE_NAT",
                    "name": "External NAT"
                }]
            }],
            
            # Metadata (startup script)
            "metadata": {
                "items": [
                    {
                        "key": "startup-script",
                        "value": startup_script
                    },
                    {
                        "key": "install-nvidia-driver",
                        "value": "True"
                    }
                ]
            },
            
            # Service account (pour accès GCS)
            "serviceAccounts": [{
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            }]
        }
        
        try:
            operation = self.compute.instances().insert(
                project=self.project_id,
                zone=self.zone,
                body=config
            ).execute()
            
            print(f"✅ Instance en cours de création")
            print(f"   Opération: {operation['name']}")
            
            return operation
            
        except HttpError as e:
            print(f"❌ Erreur: {e}")
            raise
    
    def _generate_startup_script(
        self,
        docker_image: str,
        dataset_gs: str,
        languages: List[str],
        epochs: int,
        batch_size: int
    ) -> str:
        """Génère le startup script pour l'instance."""
        
        langs_str = ','.join(languages)
        
        script = f"""#!/bin/bash
set -e

echo "🚀 Startup script F5-TTS Training"

# Mise à jour système
apt-get update -y
apt-get install -y docker.io nvidia-driver-525 google-cloud-sdk

# Démarrer Docker
systemctl start docker
systemctl enable docker

# Installer NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update -y
apt-get install -y nvidia-container-toolkit
systemctl restart docker

# Créer répertoires
mkdir -p /mnt/disks/model
mkdir -p /mnt/disks/dataset
mkdir -p /mnt/disks/checkpoints

# Télécharger dataset depuis GCS si spécifié
if [ -n "{dataset_gs}" ]; then
    echo "📥 Téléchargement dataset: {dataset_gs}"
    gsutil -m rsync -r {dataset_gs} /mnt/disks/dataset/
fi

# Lancer container de training
echo "🎓 Démarrage du training..."
docker run --gpus all \\
    -v /mnt/disks/dataset:/data \\
    -v /mnt/disks/checkpoints:/checkpoints \\
    -e DATASET=/data \\
    -e LANGUAGES={langs_str} \\
    -e EPOCHS={epochs} \\
    -e BATCH_SIZE={batch_size} \\
    {docker_image or 'swivid/f5-tts:latest'}

# Upload checkpoints vers GCS
if [ -n "{dataset_gs}" ]; then
    BUCKET=$(echo {dataset_gs} | cut -d'/' -f3)
    echo "📤 Upload checkpoints vers gs://$BUCKET/checkpoints/"
    gsutil -m rsync -r /mnt/disks/checkpoints/ gs://$BUCKET/checkpoints/
fi

echo "✅ Training terminé!"

# Auto-shutdown (optionnel, décommenter si souhaité)
# shutdown -h now
"""
        return script
    
    def get_instance_status(self, name: str) -> Optional[Dict]:
        """Récupère le statut d'une instance."""
        try:
            instance = self.compute.instances().get(
                project=self.project_id,
                zone=self.zone,
                instance=name
            ).execute()
            
            status = instance['status']
            print(f"📊 Instance: {name}")
            print(f"   Status: {status}")
            
            if 'networkInterfaces' in instance:
                external_ip = instance['networkInterfaces'][0]['accessConfigs'][0].get('natIP')
                print(f"   IP externe: {external_ip}")
            
            return instance
            
        except HttpError as e:
            if e.resp.status == 404:
                print(f"❌ Instance '{name}' non trouvée")
                return None
            raise
    
    def delete_instance(self, name: str) -> Dict:
        """Supprime une instance."""
        print(f"🗑️  Suppression de l'instance: {name}")
        
        try:
            operation = self.compute.instances().delete(
                project=self.project_id,
                zone=self.zone,
                instance=name
            ).execute()
            
            print(f"✅ Instance en cours de suppression")
            return operation
            
        except HttpError as e:
            print(f"❌ Erreur: {e}")
            raise
    
    def stream_logs(self, name: str):
        """
        Stream les logs d'une instance (via serial port).
        
        Args:
            name: Nom de l'instance
        
        Yields:
            Lignes de log
        """
        print(f"📜 Streaming logs de: {name}")
        
        start = 0
        while True:
            try:
                response = self.compute.instances().getSerialPortOutput(
                    project=self.project_id,
                    zone=self.zone,
                    instance=name,
                    start=start
                ).execute()
                
                contents = response.get('contents', '')
                if contents:
                    for line in contents.split('\n'):
                        yield line
                    start = response.get('next', start)
                
                time.sleep(5)
                
            except HttpError as e:
                if e.resp.status == 404:
                    print("Instance terminée")
                    break
                raise
            except KeyboardInterrupt:
                print("\nStreaming interrompu")
                break


def main():
    """Exemple d'utilisation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent GCP F5-TTS")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--zone", default="us-west1-b", help="GCP Zone")
    parser.add_argument("--credentials", default="gcp-sa.json", help="Service account JSON")
    parser.add_argument("--action", choices=["create", "status", "delete", "logs"], required=True)
    parser.add_argument("--name", required=True, help="Instance name")
    parser.add_argument("--gpu", default="nvidia-tesla-t4", help="GPU type")
    parser.add_argument("--image", help="Docker image")
    parser.add_argument("--dataset", help="GCS dataset path")
    parser.add_argument("--languages", nargs="+", default=["fr", "ar"])
    parser.add_argument("--epochs", type=int, default=200)
    
    args = parser.parse_args()
    
    agent = GCPAgent(
        project_id=args.project,
        zone=args.zone,
        credentials_path=args.credentials
    )
    
    if args.action == "create":
        agent.create_training_instance(
            name=args.name,
            gpu_type=args.gpu,
            docker_image=args.image,
            dataset_gs=args.dataset,
            languages=args.languages,
            epochs=args.epochs
        )
    
    elif args.action == "status":
        agent.get_instance_status(args.name)
    
    elif args.action == "delete":
        agent.delete_instance(args.name)
    
    elif args.action == "logs":
        for log in agent.stream_logs(args.name):
            print(log)


if __name__ == "__main__":
    main()
