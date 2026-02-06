# 🚀 Guide Complet — F5-TTS avec Orchestration GPU

Ce guide vous montre comment utiliser **toutes** les solutions d'orchestration GPU pour F5-TTS.

---

## 📋 Table des Matières

1. [Option A : Colab + Agent Drive](#option-a--colab--agent-drive)
2. [Option B : GCP + Agent](#option-b--gcp--agent)
3. [Option C : RunPod + Agent](#option-c--runpod--agent)
4. [Comparaison des Options](#comparaison-des-options)
5. [Troubleshooting](#troubleshooting)

---

## Option A : Colab + Agent Drive

### 🎯 Cas d'usage
- Prototypage rapide
- Tests avec petits datasets
- Budget limité (gratuit avec limites)

### 📝 Setup (10 minutes)

#### 1. Créer Service Account Google Cloud

```bash
# Via Google Cloud Console
# 1. IAM & Admin → Service Accounts → Create
# 2. Donner rôle "Editor" (ou juste Drive API)
# 3. Créer clé JSON → télécharger sa.json
```

#### 2. Partager dossier Drive

```bash
# 1. Créer dossier "f5_tts_orchestration" dans MyDrive
# 2. Partager avec email du service account (editor)
# 3. Noter le folder ID (dans l'URL)
```

#### 3. Configurer agent

```python
# Éditer agents/colab_agent.py
# Remplacer placeholders:
# - credentials_path: chemin vers sa.json
# - drive_folder_name: "f5_tts_orchestration"
```

#### 4. Ouvrir notebook Colab

```
1. Aller sur https://colab.research.google.com/
2. File → Upload notebook
3. Uploader notebooks/F5_TTS_Colab_Training.ipynb
4. Runtime → Change runtime type → GPU (T4)
5. Lancer Cell 1-4 pour setup
6. Lancer Cell 5 (polling) et laisser tourner
```

### 🚀 Lancer Training

```bash
# Sur votre machine locale
python agents/colab_agent.py \
  --credentials sa.json \
  --action start \
  --languages fr ar \
  --dataset gs://your-bucket/dataset \
  --epochs 200
```

### 📊 Monitoring

```bash
# Vérifier statut
python agents/colab_agent.py \
  --credentials sa.json \
  --action status

# Monitoring continu
python agents/colab_agent.py \
  --credentials sa.json \
  --action monitor
```

### 📥 Récupération

```bash
# Télécharger checkpoint
python agents/colab_agent.py \
  --credentials sa.json \
  --action download \
  --output models/f5_tts_checkpoint.pth
```

---

## Option B : GCP + Agent

### 🎯 Cas d'usage
- Production
- Gros datasets
- Contrôle total du GPU
- Entraînements longs

### 📝 Setup (30 minutes)

#### 1. Activer APIs GCP

```bash
# Installer gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authentifier
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Activer APIs
gcloud services enable compute.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 2. Vérifier quotas GPU

```bash
# Vérifier quotas
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# Demander augmentation si nécessaire
# Console → IAM & Admin → Quotas
# Chercher "NVIDIA T4 GPUs" → Request increase
```

#### 3. Builder et pusher image Docker

```bash
cd docker

# Builder
docker build -t gcr.io/YOUR_PROJECT/f5-tts:latest -f Dockerfile.f5tts .

# Authentifier Docker pour GCR
gcloud auth configure-docker

# Push
docker push gcr.io/YOUR_PROJECT/f5-tts:latest
```

#### 4. Uploader dataset vers GCS

```bash
# Créer bucket
gsutil mb gs://YOUR_BUCKET

# Upload dataset
gsutil -m rsync -r datasets/processed/commonvoice_fr gs://YOUR_BUCKET/dataset/
```

### 🚀 Lancer Training

```bash
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --zone us-west1-b \
  --credentials gcp-sa.json \
  --action create \
  --name f5-tts-train-1 \
  --gpu nvidia-tesla-t4 \
  --image gcr.io/YOUR_PROJECT/f5-tts:latest \
  --dataset gs://YOUR_BUCKET/dataset \
  --languages fr ar \
  --epochs 200
```

### 📊 Monitoring

```bash
# Vérifier statut
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --action status \
  --name f5-tts-train-1

# Stream logs
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --action logs \
  --name f5-tts-train-1
```

### 📥 Récupération & Cleanup

```bash
# Checkpoints sont automatiquement uploadés vers GCS
gsutil -m cp -r gs://YOUR_BUCKET/checkpoints/ models/

# Supprimer instance
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --action delete \
  --name f5-tts-train-1
```

---

## Option C : RunPod + Agent

### 🎯 Cas d'usage
- GPU haute performance (RTX 4090, A100, H100)
- Meilleur rapport qualité/prix
- Setup plus simple que GCP

### 📝 Setup (15 minutes)

#### 1. Créer compte RunPod

```
1. Aller sur https://www.runpod.io/
2. Sign up
3. Add credits ($10 minimum)
4. Settings → API Keys → Create
5. Copier API key
```

#### 2. Builder et pusher image Docker

```bash
cd docker

# Builder pour DockerHub (RunPod supporte DockerHub)
docker build -t YOUR_USERNAME/f5-tts:latest -f Dockerfile.f5tts .

# Login DockerHub
docker login

# Push
docker push YOUR_USERNAME/f5-tts:latest
```

### 🚀 Lancer Training

```bash
export RUNPOD_API_KEY=your_key

python agents/runpod_agent.py \
  --action create \
  --name f5-tts-train \
  --gpu rtx-4090 \
  --image YOUR_USERNAME/f5-tts:latest \
  --dataset /workspace/dataset \
  --languages fr ar \
  --epochs 200
```

### 📊 Monitoring

```bash
# Lister pods
python agents/runpod_agent.py --action list

# Statut
python agents/runpod_agent.py \
  --action status \
  --pod_id POD_ID

# Logs
python agents/runpod_agent.py \
  --action logs \
  --pod_id POD_ID

# Monitoring continu
python agents/runpod_agent.py \
  --action monitor \
  --pod_id POD_ID
```

### 📥 Récupération & Cleanup

```bash
# Arrêter pod (garde volume)
python agents/runpod_agent.py \
  --action stop \
  --pod_id POD_ID

# Terminer pod (supprime tout)
python agents/runpod_agent.py \
  --action terminate \
  --pod_id POD_ID
```

---

## Comparaison des Options

| Critère | Colab | GCP | RunPod |
|---------|-------|-----|--------|
| **Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Coût** | Gratuit (limites) | $0.35-$3/h | $0.20-$2/h |
| **GPU** | T4 aléatoire | T4/V100/A100/L4 | RTX 4090/A100/H100 |
| **Durée max** | 12h (24h Pro) | Illimitée | Illimitée |
| **Contrôle** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Scalabilité** | ❌ | ✅ | ✅ |
| **Production** | ❌ | ✅ | ✅ |

### Recommandations

- **Prototypage** : Colab (gratuit, rapide)
- **Production** : GCP (contrôle total, intégration)
- **Meilleur prix/perf** : RunPod (GPU puissants, moins cher)

---

## Troubleshooting

### Colab

**"Runtime disconnected"**
```
- Colab gratuit a des limites de temps
- Utiliser Colab Pro pour 24h
- Ou migrer vers GCP/RunPod
```

**"Trigger not detected"**
```
- Vérifier permissions Drive
- Vérifier folder_id dans agent
- Vérifier que Cell 5 tourne
```

### GCP

**"Quota exceeded"**
```
# Demander augmentation quota
# Console → IAM & Admin → Quotas
# Ou changer de zone/GPU
```

**"Permission denied"**
```
# Vérifier service account permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member=serviceAccount:SA_EMAIL \
  --role=roles/compute.admin
```

### RunPod

**"Insufficient funds"**
```
# Ajouter credits
# RunPod → Billing → Add Credits
```

**"No GPUs available"**
```
# Essayer autre type de GPU
# Ou attendre (demande élevée)
```

### Docker

**"CUDA out of memory"**
```
# Réduire batch_size
-e BATCH_SIZE=1
```

**"Dataset not found"**
```
# Vérifier montage volume
# GCP: dataset doit être dans GCS
# RunPod: uploader dans volume persistant
```

---

## 💡 Tips & Best Practices

### Optimisation Coûts

```bash
# GCP: Utiliser preemptible instances (70% moins cher)
# Ajouter dans gcp_agent.py:
"scheduling": {
    "preemptible": True
}

# RunPod: Utiliser Spot instances
# (automatique si disponible)
```

### Sauvegarde Automatique

```bash
# GCP: Checkpoints auto-uploadés vers GCS
# Colab: Sauvegardés dans Drive
# RunPod: Utiliser volume persistant
```

### Monitoring Avancé

```bash
# TensorBoard (tous)
# Exposer port 6006 et accéder via tunnel SSH

# Weights & Biases (optionnel)
# Ajouter dans entrypoint.sh:
export WANDB_API_KEY=your_key
```

---

## 📚 Ressources

- [F5-TTS GitHub](https://github.com/SWivid/F5-TTS)
- [GCP Compute Docs](https://cloud.google.com/compute/docs)
- [RunPod Docs](https://docs.runpod.io/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Prochaine étape** : Choisissez votre option et lancez votre premier training ! 🚀
