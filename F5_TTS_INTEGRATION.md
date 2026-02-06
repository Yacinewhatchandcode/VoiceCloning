# 🚀 F5-TTS Integration — Voice Cloning avec GPU Cloud

Ce document décrit l'intégration de **F5-TTS** (Fairytaler) pour le voice cloning, avec deux options d'orchestration GPU via agent API.

## 🎯 Pourquoi F5-TTS ?

**F5-TTS** (Fairytaler Five TTS) est supérieur à XTTS v2 pour plusieurs raisons :

- ✅ **Meilleure qualité** : Architecture diffusion-based plus récente
- ✅ **Zero-shot cloning** : Clonage avec 5-10s d'audio seulement
- ✅ **Multilingue natif** : Support FR/AR out-of-the-box
- ✅ **Plus rapide** : Inférence optimisée
- ✅ **Open source** : MIT License, communauté active

**Liens** :
- [Site officiel](https://swivid.github.io/F5-TTS/)
- [GitHub principal](https://github.com/SWivid/F5-TTS)
- [Fork optimisé](https://github.com/peytontolbert/f5-tts)

---

## 📋 Architecture d'Orchestration GPU

Deux options selon vos besoins :

### Option A : Colab + Agent Drive (Rapide, Prototypage)
- **Avantages** : Setup en 10 min, gratuit (avec limites), simple
- **Inconvénients** : GPU aléatoire, quotas stricts, pas de contrôle fin
- **Use case** : Tests, prototypes, petits datasets

### Option B : GCP/RunPod + Agent API (Production)
- **Avantages** : GPU choisi (T4/A100/H100), contrôle total, scalable
- **Inconvénients** : Coût, setup plus complexe
- **Use case** : Production, gros datasets, entraînements longs

---

## 🔧 Option A : Colab + Agent Drive

### Architecture

```
Agent API (Antigravity)
    ↓ (écrit trigger.json)
Google Drive
    ↓ (polling)
Colab Notebook (GPU gratuit)
    ↓ (exécute training)
F5-TTS Training
    ↓ (écrit status.json + checkpoints)
Google Drive (résultats)
```

### Composants

1. **Agent Python** : Écrit `trigger.json` dans Google Drive
2. **Notebook Colab** : Surveille Drive, lance training
3. **Status monitoring** : Agent lit `status.json` pour suivre progression

### Fichiers créés

- `agents/colab_agent.py` — Agent pour écrire triggers
- `notebooks/f5_tts_colab.ipynb` — Notebook Colab complet
- `configs/f5_tts_config.yaml` — Configuration F5-TTS

---

## 🚀 Option B : GCP/RunPod + Agent API

### Architecture

```
Agent API (Antigravity)
    ↓ (provision via API)
GCP Compute / RunPod
    ↓ (démarre container)
Docker (F5-TTS + datasets)
    ↓ (training sur GPU choisi)
Cloud Storage / S3
    ↓ (sauvegarde checkpoints)
Agent API (monitoring & récupération)
```

### Composants

1. **Agent GCP** : Provision VM GPU via API
2. **Dockerfile** : Image avec F5-TTS pré-installé
3. **Startup script** : Lance training automatiquement
4. **Monitoring** : Logs streaming + auto-snapshot

### Fichiers créés

- `agents/gcp_agent.py` — Agent pour GCP Compute
- `agents/runpod_agent.py` — Agent pour RunPod API
- `docker/Dockerfile.f5tts` — Image Docker optimisée
- `docker/startup.sh` — Script de démarrage
- `configs/gcp_instance.yaml` — Config VM GCP

---

## 📊 Comparaison des Options

| Critère | Option A (Colab) | Option B (GCP/RunPod) |
|---------|------------------|------------------------|
| **Setup** | 10 min | 30-60 min |
| **Coût** | Gratuit (limites) | $0.50-$3/h selon GPU |
| **GPU** | T4 aléatoire | T4/A100/H100 choisi |
| **Durée max** | 12h (Pro: 24h) | Illimitée |
| **Contrôle** | Limité | Total |
| **Scalabilité** | Non | Oui (auto-scale) |
| **Production** | ❌ | ✅ |

---

## 🎯 Workflow Complet

### Option A (Colab)

```python
# 1. Agent écrit trigger
from agents.colab_agent import ColabAgent

agent = ColabAgent(credentials='service_account.json')
agent.start_training(
    languages=['fr', 'ar'],
    dataset_path='gs://bucket/dataset',
    epochs=200,
    gpu_type='T4'  # Suggestion, pas garanti
)

# 2. Colab détecte et lance
# (automatique dans le notebook)

# 3. Agent surveille
status = agent.get_status()
print(f"Progress: {status['epoch']}/{status['total_epochs']}")

# 4. Récupération checkpoints
agent.download_checkpoint('models/f5_tts_fr_ar.pth')
```

### Option B (GCP)

```python
# 1. Agent provision VM
from agents.gcp_agent import GCPAgent

agent = GCPAgent(project='my-project', zone='us-west1-b')
instance = agent.create_training_instance(
    name='f5-tts-train-1',
    gpu_type='nvidia-tesla-a100',
    gpu_count=1,
    dataset_gs='gs://bucket/dataset',
    languages=['fr', 'ar'],
    epochs=200
)

# 2. Training démarre automatiquement
# (via startup script)

# 3. Monitoring en temps réel
for log in agent.stream_logs(instance['name']):
    print(log)

# 4. Auto-snapshot et récupération
agent.save_checkpoint(instance['name'], 'models/checkpoint.pth')
agent.delete_instance(instance['name'])  # Cleanup
```

---

## 🔐 Sécurité & Conformité

### Données Vocales

- ✅ **Chiffrement** : Datasets chiffrés au repos (GCS/S3)
- ✅ **IAM** : Accès contrôlé par service accounts
- ✅ **Consentement** : Métadonnées d'autorisation stockées
- ✅ **RGPD** : Droit à l'oubli implémenté

### API Keys

```bash
# Variables d'environnement
export GOOGLE_APPLICATION_CREDENTIALS="path/to/sa.json"
export RUNPOD_API_KEY="your_key"
export GCP_PROJECT_ID="your_project"
```

---

## 📈 Benchmarks F5-TTS

| Métrique | F5-TTS | XTTS v2 | Amélioration |
|----------|--------|---------|--------------|
| **MOS** | 4.5 | 4.2 | +7% |
| **WER** | 4.2% | 5.8% | -28% |
| **Similarité** | 92% | 85% | +8% |
| **Vitesse inférence** | 0.8s | 1.2s | +50% |
| **Audio requis (zero-shot)** | 5-10s | 10-15s | -50% |

---

## 🚀 Prochaines Étapes

### Immédiat
1. Choisir **Option A** ou **Option B** (ou les deux)
2. Configurer credentials (Google Drive API ou GCP)
3. Tester avec petit dataset

### Court Terme
1. Télécharger datasets FR/AR
2. Lancer premier training
3. Évaluer qualité

### Production
1. Déployer agent API (FastAPI)
2. Auto-scaling selon charge
3. Monitoring & alerting

---

## 📚 Ressources

- [F5-TTS Paper](https://arxiv.org/abs/2410.06885)
- [Demo en ligne](https://swivid.github.io/F5-TTS/)
- [GCP Compute API](https://cloud.google.com/compute/docs/api)
- [RunPod API](https://docs.runpod.io/reference/api)

---

**Prochaine action** : Choisissez votre option et consultez le guide correspondant !
