# 🎙️ Voice Cloning Pipeline — Français & Arabe

Pipeline complet pour l'entraînement et le clonage de voix en **français** et **arabe**, avec support multilingue et architecture modulaire.

## 📋 Table des Matières

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Datasets Supportés](#datasets-supportés)
- [Utilisation Rapide](#utilisation-rapide)
- [Pipeline Complet](#pipeline-complet)
- [Configuration](#configuration)
- [Résultats & Benchmarks](#résultats--benchmarks)

---

## ✨ Fonctionnalités

- ✅ **Téléchargement automatisé** de 5+ datasets (Common Voice, Arabic Speech Corpus, MLS, etc.)
- ✅ **Prétraitement audio intelligent** (normalisation, nettoyage silences, resampling)
- ✅ **Génération automatique de metadata** multilingue
- ✅ **Support multi-speakers** avec speaker embeddings
- ✅ **Fine-tuning optimisé** pour GPU/CPU
- ✅ **Interface de test** pour validation rapide
- ✅ **Export production** (ONNX, TorchScript)

---

## 🏗️ Architecture

```
VoiceCloning/
├── datasets/              # Données brutes et traitées
│   ├── raw/              # Datasets téléchargés
│   ├── processed/        # Audio normalisé
│   └── metadata/         # CSV de transcriptions
├── scripts/              # Outils de prétraitement
│   ├── download/         # Téléchargement datasets
│   ├── preprocess/       # Nettoyage audio
│   └── metadata/         # Génération metadata
├── models/               # Checkpoints et configs
│   ├── pretrained/       # Modèles de base
│   └── finetuned/        # Modèles entraînés
├── configs/              # Configurations d'entraînement
├── notebooks/            # Jupyter pour exploration
├── tests/                # Tests unitaires
└── demo/                 # Interface de démo
```

---

## 🚀 Installation

### Prérequis
- Python 3.9+
- FFmpeg (pour traitement audio)
- CUDA 11.8+ (optionnel, pour GPU)
- 50+ GB d'espace disque

### Installation rapide

```bash
# Cloner et installer
cd VoiceCloning
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Installer FFmpeg (macOS)
brew install ffmpeg sox

# Vérifier installation
python scripts/check_setup.py
```

---

## 📦 Datasets Supportés

| Dataset | Langue | Durée | Speakers | Licence | Priorité |
|---------|--------|-------|----------|---------|----------|
| **Mozilla Common Voice 17.0** | FR + AR | ~500h (FR), ~300h (AR) | Multi | CC-0 | ⭐⭐⭐ |
| **Arabic Speech Corpus** | AR (MSA) | ~1.5h | 1 | Academic | ⭐⭐⭐ |
| **MLS French** | FR | ~1000h | Multi | CC-BY 4.0 | ⭐⭐ |
| **CSS10 French** | FR | ~24h | 1 | Public Domain | ⭐⭐ |
| **MGB-2 Arabic** | AR (dialectal) | ~1200h | Multi | Academic | ⭐ |

---

## ⚡ Utilisation Rapide

### 1. Télécharger un dataset (exemple : Common Voice FR)

```bash
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr
```

### 2. Prétraiter les audios

```bash
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_fr \
  --output datasets/processed/commonvoice_fr \
  --sample_rate 22050 \
  --trim_silence
```

### 3. Générer metadata

```bash
python scripts/metadata/generate_metadata.py \
  --dataset commonvoice \
  --language fr \
  --output datasets/metadata/fr_metadata.csv
```

### 4. Entraîner un modèle

```bash
python train.py \
  --config configs/xtts_multilingual.yaml \
  --languages fr ar \
  --batch_size 16 \
  --epochs 200
```

### 5. Tester le clonage

```bash
python demo/clone_voice.py \
  --reference_audio samples/voice_sample.wav \
  --text "Bonjour, ceci est un test de clonage vocal." \
  --language fr \
  --output output/cloned_voice.wav
```

---

## 🔧 Pipeline Complet

### Workflow recommandé

```bash
# 1. Télécharger tous les datasets prioritaires
./scripts/download/download_all.sh

# 2. Prétraitement complet (parallélisé)
python scripts/preprocess/batch_process.py \
  --datasets commonvoice_fr commonvoice_ar arabic_speech_corpus \
  --workers 8

# 3. Fusion metadata multilingue
python scripts/metadata/merge_datasets.py \
  --output datasets/metadata/multilingual_train.csv \
  --split 0.9 0.05 0.05  # train/val/test

# 4. Entraînement multi-GPU (si disponible)
python train.py \
  --config configs/production.yaml \
  --gpus 0,1 \
  --resume_from models/finetuned/last_checkpoint.pth

# 5. Évaluation
python evaluate.py \
  --checkpoint models/finetuned/best_model.pth \
  --test_set datasets/metadata/multilingual_test.csv

# 6. Export production
python export.py \
  --checkpoint models/finetuned/best_model.pth \
  --format onnx \
  --output models/production/voice_cloner.onnx
```

---

## ⚙️ Configuration

### Fichiers de configuration

- `configs/xtts_multilingual.yaml` — Configuration XTTS (Coqui)
- `configs/production.yaml` — Setup production optimisé
- `configs/quick_test.yaml` — Test rapide (petit dataset)

### Paramètres clés

```yaml
# configs/xtts_multilingual.yaml
model:
  type: xtts_v2
  languages: [fr, ar]
  sample_rate: 22050
  
training:
  batch_size: 16
  learning_rate: 1e-5
  epochs: 200
  gradient_accumulation: 4
  
data:
  min_audio_length: 1.0  # secondes
  max_audio_length: 15.0
  trim_silence: true
  normalize_audio: true
```

---

## 📊 Résultats & Benchmarks

### Qualité attendue (après fine-tuning)

| Métrique | Single-Speaker | Multi-Speaker | Zero-Shot |
|----------|----------------|---------------|-----------|
| **MOS** (Mean Opinion Score) | 4.2-4.5 | 3.8-4.1 | 3.5-3.8 |
| **WER** (Word Error Rate) | 5-8% | 8-12% | 12-18% |
| **Similarité vocale** | 85-92% | 75-85% | 65-75% |

### Temps d'entraînement (estimations)

- **GPU RTX 4090** : ~12-24h (200 epochs, 50h de données)
- **GPU RTX 3080** : ~24-48h
- **CPU (M2 Max)** : ~5-7 jours

---

## 📝 Notes Légales

⚠️ **Important** :
- Vérifiez les licences de chaque dataset avant utilisation commerciale
- Obtenez le **consentement explicite** pour cloner des voix de personnes réelles
- Common Voice (CC-0) : usage libre, mais vérifiez la version spécifique
- Datasets académiques : souvent limités à la recherche

---

## 🤝 Contribution

Contributions bienvenues ! Voir `CONTRIBUTING.md` pour les guidelines.

---

## 📄 Licence

MIT License — Voir `LICENSE` pour détails.

---

**Créé avec ❤️ pour la communauté francophone et arabophone**
