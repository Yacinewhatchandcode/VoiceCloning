# 🐳 Docker Build & Deploy — F5-TTS

Ce guide explique comment builder et déployer l'image Docker F5-TTS.

## 📋 Prérequis

- Docker installé (`docker --version`)
- NVIDIA Docker runtime (pour GPU local)
- Compte DockerHub ou Google Container Registry

---

## 🔨 Build de l'Image

### Option 1 : Build local

```bash
cd VoiceCloning/docker

# Build l'image
docker build -t f5-tts:latest -f Dockerfile.f5tts .

# Tester localement (avec GPU)
docker run --gpus all \
  -v $(pwd)/../datasets:/data \
  -v $(pwd)/../models:/checkpoints \
  -e DATASET=/data \
  -e LANGUAGES=fr,ar \
  -e EPOCHS=10 \
  f5-tts:latest
```

### Option 2 : Build pour production

```bash
# Tag pour DockerHub
docker build -t YOUR_USERNAME/f5-tts:latest -f Dockerfile.f5tts .
docker push YOUR_USERNAME/f5-tts:latest

# Tag pour Google Container Registry
docker build -t gcr.io/YOUR_PROJECT/f5-tts:latest -f Dockerfile.f5tts .
docker push gcr.io/YOUR_PROJECT/f5-tts:latest
```

---

## 🚀 Déploiement

### GCP (via agent)

```bash
# Utiliser l'agent GCP
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --zone us-west1-b \
  --action create \
  --name f5-tts-train-1 \
  --gpu nvidia-tesla-t4 \
  --image gcr.io/YOUR_PROJECT/f5-tts:latest \
  --dataset gs://YOUR_BUCKET/dataset \
  --languages fr ar \
  --epochs 200
```

### RunPod (via agent)

```bash
# Utiliser l'agent RunPod
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

### Local (test)

```bash
# Avec GPU NVIDIA
docker run --gpus all \
  -v /path/to/dataset:/data \
  -v /path/to/checkpoints:/checkpoints \
  -e DATASET=/data \
  -e LANGUAGES=fr,ar \
  -e EPOCHS=50 \
  -e BATCH_SIZE=2 \
  f5-tts:latest

# Sans GPU (CPU, très lent)
docker run \
  -v /path/to/dataset:/data \
  -v /path/to/checkpoints:/checkpoints \
  -e DEVICE=cpu \
  -e DATASET=/data \
  -e LANGUAGES=fr \
  -e EPOCHS=10 \
  -e BATCH_SIZE=1 \
  f5-tts:latest
```

---

## ⚙️ Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DATASET` | `/data` | Chemin du dataset |
| `LANGUAGES` | `fr,ar` | Langues (comma-separated) |
| `EPOCHS` | `200` | Nombre d'epochs |
| `BATCH_SIZE` | `2` | Taille de batch |
| `DEVICE` | `cuda` | Device (cuda/cpu) |
| `CHECKPOINT_DIR` | `/checkpoints` | Répertoire checkpoints |
| `LOG_DIR` | `/logs` | Répertoire logs |

---

## 📊 Monitoring

### Logs en temps réel

```bash
# Docker local
docker logs -f CONTAINER_ID

# GCP
python agents/gcp_agent.py \
  --project YOUR_PROJECT \
  --action logs \
  --name f5-tts-train-1

# RunPod
python agents/runpod_agent.py \
  --action logs \
  --pod_id POD_ID
```

### TensorBoard (optionnel)

```bash
# Exposer port TensorBoard
docker run --gpus all \
  -v /path/to/dataset:/data \
  -v /path/to/checkpoints:/checkpoints \
  -p 6006:6006 \
  f5-tts:latest

# Accéder à http://localhost:6006
```

---

## 🔐 Authentification GCR

```bash
# Configurer gcloud
gcloud auth configure-docker

# Push vers GCR
docker push gcr.io/YOUR_PROJECT/f5-tts:latest
```

---

## 💾 Récupération des Checkpoints

### Depuis container local

```bash
# Les checkpoints sont dans le volume monté
ls -lh /path/to/checkpoints/
```

### Depuis GCP

```bash
# Les checkpoints sont uploadés automatiquement vers GCS
gsutil ls gs://YOUR_BUCKET/checkpoints/

# Télécharger
gsutil -m cp -r gs://YOUR_BUCKET/checkpoints/ ./models/
```

### Depuis RunPod

```bash
# Via l'agent
python agents/runpod_agent.py \
  --action stop \
  --pod_id POD_ID

# Puis télécharger depuis le volume persistant
# (nécessite accès SSH ou API RunPod)
```

---

## 🧪 Tests

### Test rapide (10 epochs)

```bash
docker run --gpus all \
  -v $(pwd)/datasets/processed/arabic_corpus:/data \
  -v $(pwd)/models/test:/checkpoints \
  -e EPOCHS=10 \
  -e BATCH_SIZE=1 \
  f5-tts:latest
```

### Test multi-GPU (si disponible)

```bash
docker run --gpus all \
  -v /path/to/dataset:/data \
  -v /path/to/checkpoints:/checkpoints \
  -e EPOCHS=200 \
  -e BATCH_SIZE=4 \
  f5-tts:latest
```

---

## 📝 Notes

- **Taille de l'image** : ~5-7 GB (CUDA + PyTorch + dépendances)
- **Build time** : ~10-15 min selon connexion
- **RAM requise** : 16+ GB recommandé
- **GPU VRAM** : 16+ GB pour batch_size=2

---

## 🆘 Troubleshooting

### "CUDA out of memory"

```bash
# Réduire batch_size
docker run --gpus all \
  -e BATCH_SIZE=1 \
  ...
```

### "Dataset not found"

```bash
# Vérifier le montage du volume
docker run --gpus all \
  -v /ABSOLUTE/path/to/dataset:/data \
  ...
```

### "Permission denied"

```bash
# Donner les permissions au répertoire de checkpoints
chmod -R 777 /path/to/checkpoints
```

---

**Prochaine étape** : Consultez `F5_TTS_INTEGRATION.md` pour l'orchestration complète !
