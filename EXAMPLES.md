# 🎯 Exemples d'Utilisation — Voice Cloning Pipeline

Ce document contient des exemples pratiques pour chaque étape du pipeline.

## 📥 1. Téléchargement de Datasets

### Exemple 1.1 : Common Voice Français (complet)

```bash
# Télécharger tous les splits (train, validation, test)
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr \
  --split all
```

### Exemple 1.2 : Common Voice Arabe (train uniquement)

```bash
# Seulement le split train (plus rapide)
python scripts/download/download_commonvoice.py \
  --language ar \
  --version 17.0 \
  --output datasets/raw/commonvoice_ar \
  --split train
```

### Exemple 1.3 : Arabic Speech Corpus

```bash
# Dataset single-speaker MSA
python scripts/download/download_arabic_corpus.py \
  --output datasets/raw/arabic_corpus
```

### Exemple 1.4 : Télécharger tous les datasets prioritaires

```bash
# Script automatisé
./scripts/download/download_all.sh
```

---

## 🔧 2. Prétraitement Audio

### Exemple 2.1 : Prétraitement basique

```bash
# Normalisation + resampling à 22050 Hz
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_fr/train \
  --output datasets/processed/commonvoice_fr \
  --sample_rate 22050 \
  --workers 8
```

### Exemple 2.2 : Prétraitement avancé (avec nettoyage)

```bash
# Avec trim silence + normalisation + réduction de bruit
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_ar/train \
  --output datasets/processed/commonvoice_ar \
  --metadata datasets/raw/commonvoice_ar/train/metadata.csv \
  --sample_rate 22050 \
  --trim_silence \
  --normalize \
  --noise_reduce \
  --workers 4
```

### Exemple 2.3 : Traitement batch de plusieurs datasets

```bash
# Boucle pour traiter plusieurs datasets
for dataset in commonvoice_fr commonvoice_ar arabic_corpus; do
  python scripts/preprocess/process_audio.py \
    --input datasets/raw/${dataset} \
    --output datasets/processed/${dataset} \
    --sample_rate 22050 \
    --trim_silence \
    --normalize \
    --workers 8
done
```

---

## 📋 3. Génération de Metadata

### Exemple 3.1 : Générer metadata pour un dataset

```bash
# Common Voice FR
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice \
  --input datasets/processed/commonvoice_fr \
  --language fr \
  --output datasets/metadata/fr_metadata.csv
```

### Exemple 3.2 : Fusionner plusieurs datasets multilingues

```bash
# Créer un dataset combiné FR + AR
python scripts/metadata/generate_metadata.py merge \
  --inputs \
    datasets/metadata/fr_metadata.csv \
    datasets/metadata/ar_metadata.csv \
  --output datasets/metadata/multilingual \
  --train_split 0.9 \
  --val_split 0.05 \
  --test_split 0.05
```

---

## 🎓 4. Entraînement

### Exemple 4.1 : Entraînement basique (single GPU)

```bash
# Utiliser config par défaut
python train.py \
  --config configs/xtts_multilingual.yaml
```

### Exemple 4.2 : Entraînement multi-GPU

```bash
# Utiliser GPU 0 et 1
python train.py \
  --config configs/xtts_multilingual.yaml \
  --gpus 0,1
```

### Exemple 4.3 : Reprendre depuis un checkpoint

```bash
# Continuer l'entraînement
python train.py \
  --config configs/xtts_multilingual.yaml \
  --resume_from models/finetuned/xtts_multilingual/checkpoint_50000.pth
```

### Exemple 4.4 : Entraînement rapide (test)

```bash
# Créer une config de test
cat > configs/quick_test.yaml << EOF
model:
  type: xtts_v2
  languages: [fr]
  sample_rate: 22050

training:
  batch_size: 4
  epochs: 10
  learning_rate: 1e-5

data:
  train_csv: datasets/metadata/fr_metadata.csv
  val_csv: datasets/metadata/fr_metadata.csv
  min_audio_length: 1.0
  max_audio_length: 10.0

paths:
  output_dir: models/test
  log_dir: logs/test
EOF

# Lancer
python train.py --config configs/quick_test.yaml
```

---

## 🎙️ 5. Clonage de Voix

### Exemple 5.1 : Clonage simple (français)

```bash
# Créer un échantillon de référence (5-15s recommandé)
# Puis cloner
python demo/clone_voice.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --reference_audio samples/my_voice_fr.wav \
  --text "Bonjour, ceci est un test de clonage vocal en français." \
  --language fr \
  --output output/cloned_fr.wav
```

### Exemple 5.2 : Clonage arabe

```bash
python demo/clone_voice.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --reference_audio samples/my_voice_ar.wav \
  --text "مرحبا، هذا اختبار لاستنساخ الصوت باللغة العربية." \
  --language ar \
  --output output/cloned_ar.wav
```

### Exemple 5.3 : Ajuster la température et vitesse

```bash
# Température basse = plus stable, haute = plus variée
# Vitesse < 1.0 = plus lent, > 1.0 = plus rapide
python demo/clone_voice.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --reference_audio samples/reference.wav \
  --text "Texte à synthétiser" \
  --language fr \
  --output output/custom.wav \
  --temperature 0.65 \
  --speed 1.2
```

### Exemple 5.4 : Clonage batch (plusieurs textes)

```python
# Script Python pour batch
from demo.clone_voice import VoiceCloner

cloner = VoiceCloner(
    checkpoint_path="models/finetuned/xtts_multilingual/best_model.pth"
)

texts = [
    "Premier texte à synthétiser.",
    "Deuxième texte avec une voix clonée.",
    "Troisième exemple de clonage vocal."
]

cloner.batch_clone(
    reference_audio="samples/reference.wav",
    texts=texts,
    language="fr",
    output_dir="output/batch"
)
```

---

## 📊 6. Évaluation

### Exemple 6.1 : Évaluer sur test set

```bash
python evaluate.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --test_csv datasets/metadata/test.csv \
  --output evaluation \
  --num_samples 100
```

### Exemple 6.2 : Évaluation rapide (10 samples)

```bash
python evaluate.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --test_csv datasets/metadata/test.csv \
  --output evaluation/quick \
  --num_samples 10
```

---

## 🔍 7. Utilitaires

### Exemple 7.1 : Vérifier l'installation

```bash
python scripts/check_setup.py
```

### Exemple 7.2 : Inspecter un metadata CSV

```python
import pandas as pd

df = pd.read_csv("datasets/metadata/train.csv")

print(f"Total samples: {len(df)}")
print(f"Total duration: {df['duration'].sum() / 3600:.1f} hours")
print(f"\nLanguage distribution:")
print(df['language'].value_counts())
print(f"\nDuration stats:")
print(df['duration'].describe())
```

### Exemple 7.3 : Convertir audio (FFmpeg)

```bash
# MP3 → WAV
ffmpeg -i input.mp3 -ar 22050 -ac 1 -sample_fmt s16 output.wav

# Trim silence (SoX)
sox input.wav output_trimmed.wav silence 1 0.1 1% reverse silence 1 0.1 1% reverse

# Normaliser niveau RMS
ffmpeg -i input.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" output_normalized.wav
```

### Exemple 7.4 : Monitorer l'entraînement (TensorBoard)

```bash
# Lancer TensorBoard
tensorboard --logdir tensorboard/xtts_multilingual --port 6006

# Ouvrir dans le navigateur
open http://localhost:6006
```

---

## 🐍 8. Exemples Python (API)

### Exemple 8.1 : Utiliser le cloner en Python

```python
from demo.clone_voice import VoiceCloner

# Initialiser
cloner = VoiceCloner(
    checkpoint_path="models/finetuned/xtts_multilingual/best_model.pth"
)

# Cloner une voix
cloner.clone_voice(
    reference_audio="samples/reference.wav",
    text="Texte à synthétiser",
    language="fr",
    output_path="output/result.wav",
    temperature=0.75,
    speed=1.0
)
```

### Exemple 8.2 : Prétraiter un fichier audio

```python
from scripts.preprocess.process_audio import AudioProcessor

processor = AudioProcessor(
    target_sr=22050,
    trim_silence=True,
    normalize=True
)

stats = processor.process_file(
    input_path="input.wav",
    output_path="output.wav"
)

print(f"Duration: {stats['duration']:.2f}s")
print(f"RMS: {stats['rms']:.4f}")
```

---

## 🚀 9. Workflows Complets

### Workflow 9.1 : Du dataset au modèle (français uniquement)

```bash
# 1. Télécharger
python scripts/download/download_commonvoice.py \
  --language fr --version 17.0 \
  --output datasets/raw/commonvoice_fr --split all

# 2. Prétraiter
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_fr \
  --output datasets/processed/commonvoice_fr \
  --sample_rate 22050 --trim_silence --normalize --workers 8

# 3. Metadata
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice --input datasets/processed/commonvoice_fr \
  --language fr --output datasets/metadata/fr_metadata.csv

python scripts/metadata/generate_metadata.py merge \
  --inputs datasets/metadata/fr_metadata.csv \
  --output datasets/metadata --train_split 0.9 --val_split 0.05 --test_split 0.05

# 4. Entraîner
python train.py --config configs/xtts_multilingual.yaml

# 5. Évaluer
python evaluate.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --test_csv datasets/metadata/test.csv --output evaluation

# 6. Tester
python demo/clone_voice.py \
  --checkpoint models/finetuned/xtts_multilingual/best_model.pth \
  --reference_audio samples/test.wav \
  --text "Test final du modèle" --language fr \
  --output output/final_test.wav
```

---

**💡 Astuce**: Consultez `QUICKSTART.md` pour des workflows simplifiés et `RESOURCES.md` pour plus de datasets.
