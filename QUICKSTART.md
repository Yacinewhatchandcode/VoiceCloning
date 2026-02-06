# 🎙️ Guide de Démarrage Rapide — Voice Cloning FR/AR

Ce guide vous permet de démarrer rapidement avec le pipeline de voice cloning.

## ⚡ Installation Express (5 minutes)

```bash
# 1. Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. Installer dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 3. Installer FFmpeg (macOS)
brew install ffmpeg sox

# 4. Vérifier installation
python scripts/check_setup.py
```

## 🚀 Workflow Complet (Exemple avec Common Voice FR)

### Étape 1 : Télécharger un dataset (30-60 min)

```bash
# Option A: Dataset complet (recommandé)
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr \
  --split all

# Option B: Seulement train (plus rapide)
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr \
  --split train
```

### Étape 2 : Prétraiter les audios (10-30 min)

```bash
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_fr/train \
  --output datasets/processed/commonvoice_fr \
  --metadata datasets/raw/commonvoice_fr/train/metadata.csv \
  --sample_rate 22050 \
  --trim_silence \
  --normalize \
  --workers 8
```

### Étape 3 : Générer metadata finale

```bash
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice \
  --input datasets/processed/commonvoice_fr \
  --language fr \
  --output datasets/metadata/fr_metadata.csv
```

### Étape 4 : Entraîner le modèle (12-48h selon GPU)

```bash
# Éditer configs/xtts_multilingual.yaml pour ajuster les chemins
# Puis lancer l'entraînement

python train.py \
  --config configs/xtts_multilingual.yaml
```

### Étape 5 : Tester le clonage

```bash
python demo/clone_voice.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --reference_audio samples/my_voice.wav \
  --text "Bonjour, ceci est un test de clonage vocal." \
  --language fr \
  --output output/test_clone.wav
```

## 🎯 Workflow Rapide (Test avec petit dataset)

Pour tester rapidement sans télécharger des GB de données :

```bash
# 1. Télécharger Arabic Speech Corpus (petit, ~1.5GB)
python scripts/download/download_arabic_corpus.py \
  --output datasets/raw/arabic_corpus

# 2. Prétraiter
python scripts/preprocess/process_audio.py \
  --input datasets/raw/arabic_corpus/audio \
  --output datasets/processed/arabic_corpus \
  --metadata datasets/raw/arabic_corpus/metadata.csv \
  --workers 4

# 3. Créer metadata
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice \
  --input datasets/processed/arabic_corpus \
  --language ar \
  --output datasets/metadata/ar_metadata.csv

# 4. Éditer configs/xtts_multilingual.yaml
# Changer:
#   data.train_csv: "datasets/metadata/ar_metadata.csv"
#   training.epochs: 50  # Réduire pour test rapide

# 5. Entraîner (test)
python train.py --config configs/xtts_multilingual.yaml
```

## 🔧 Commandes Utiles

### Vérifier un dataset

```bash
# Statistiques d'un metadata CSV
python -c "
import pandas as pd
df = pd.read_csv('datasets/metadata/fr_metadata.csv')
print(f'Samples: {len(df)}')
print(f'Durée totale: {df[\"duration\"].sum() / 3600:.1f}h')
print(f'Langues: {df[\"language\"].value_counts()}')
"
```

### Écouter un échantillon

```bash
# macOS
afplay datasets/processed/commonvoice_fr/fr_train_000001.wav

# Linux
aplay datasets/processed/commonvoice_fr/fr_train_000001.wav
```

### Monitorer l'entraînement

```bash
# TensorBoard
tensorboard --logdir tensorboard/xtts_multilingual --port 6006
# Ouvrir http://localhost:6006
```

## 📊 Temps Estimés

| Étape | CPU (M2 Max) | GPU (RTX 4090) |
|-------|--------------|----------------|
| Téléchargement (50h) | 30-60 min | 30-60 min |
| Prétraitement (50h) | 2-4h | 1-2h |
| Entraînement (200 epochs) | 5-7 jours | 12-24h |

## ⚠️ Troubleshooting

### Erreur: "CUDA out of memory"

```yaml
# Réduire batch_size dans configs/xtts_multilingual.yaml
training:
  batch_size: 8  # au lieu de 16
  gradient_accumulation_steps: 8  # au lieu de 4
```

### Erreur: "FFmpeg not found"

```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

### Audio de mauvaise qualité

- Vérifier que `trim_silence` et `normalize` sont activés
- Augmenter `min_audio_length` à 2.0s
- Filtrer les samples avec bruit de fond

## 📚 Ressources

- [Documentation XTTS](https://docs.coqui.ai/en/latest/models/xtts.html)
- [Common Voice](https://commonvoice.mozilla.org/)
- [HuggingFace Datasets](https://huggingface.co/datasets)

---

**Besoin d'aide ?** Ouvrez une issue sur GitHub ou consultez la documentation complète dans `README.md`.
