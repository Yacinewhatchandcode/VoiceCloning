# 🎨 Notebook de Démonstration — Voice Cloning

Ce notebook vous guide à travers le pipeline complet de voice cloning.

## 📚 Table des Matières

1. [Installation & Setup](#1-installation--setup)
2. [Exploration des Datasets](#2-exploration-des-datasets)
3. [Prétraitement Audio](#3-prétraitement-audio)
4. [Visualisation](#4-visualisation)
5. [Clonage de Voix](#5-clonage-de-voix)
6. [Évaluation](#6-évaluation)

---

## 1. Installation & Setup

```python
# Imports
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import librosa
import librosa.display
import soundfile as sf
from IPython.display import Audio, display

# Configuration
%matplotlib inline
sns.set_style("whitegrid")

# Ajouter le répertoire parent au path
sys.path.append(str(Path.cwd().parent))

print("✅ Setup complet!")
```

---

## 2. Exploration des Datasets

### 2.1 Charger metadata

```python
# Charger metadata d'un dataset
metadata_path = "../datasets/metadata/fr_metadata.csv"

if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path)
    print(f"📊 Dataset: {len(df)} samples")
    display(df.head())
else:
    print("⚠️  Metadata non trouvée. Téléchargez d'abord un dataset.")
```

### 2.2 Statistiques

```python
# Statistiques de durée
if 'duration' in df.columns:
    print(f"\n📈 Statistiques de durée:")
    print(df['duration'].describe())
    
    # Histogramme
    plt.figure(figsize=(10, 5))
    plt.hist(df['duration'], bins=50, edgecolor='black')
    plt.xlabel('Durée (secondes)')
    plt.ylabel('Nombre de samples')
    plt.title('Distribution des durées audio')
    plt.show()
```

### 2.3 Distribution par langue

```python
if 'language' in df.columns:
    lang_counts = df['language'].value_counts()
    
    plt.figure(figsize=(8, 5))
    lang_counts.plot(kind='bar')
    plt.xlabel('Langue')
    plt.ylabel('Nombre de samples')
    plt.title('Distribution par langue')
    plt.xticks(rotation=0)
    plt.show()
    
    print(f"\n🌍 Langues:")
    for lang, count in lang_counts.items():
        duration_h = df[df['language'] == lang]['duration'].sum() / 3600
        print(f"  {lang}: {count} samples ({duration_h:.1f}h)")
```

---

## 3. Prétraitement Audio

### 3.1 Charger et visualiser un audio

```python
# Sélectionner un sample aléatoire
sample = df.sample(1).iloc[0]
audio_path = sample['path']

print(f"📁 Fichier: {audio_path}")
print(f"📝 Texte: {sample.get('text', 'N/A')}")

# Charger audio
audio, sr = librosa.load(audio_path, sr=None)

print(f"🎵 Sample rate: {sr} Hz")
print(f"⏱️  Durée: {len(audio) / sr:.2f}s")

# Écouter
display(Audio(audio, rate=sr))
```

### 3.2 Visualiser la forme d'onde

```python
plt.figure(figsize=(14, 4))
librosa.display.waveshow(audio, sr=sr)
plt.xlabel('Temps (s)')
plt.ylabel('Amplitude')
plt.title('Forme d\'onde')
plt.tight_layout()
plt.show()
```

### 3.3 Spectrogramme

```python
# Calculer spectrogramme mel
mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80)
mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)

# Visualiser
plt.figure(figsize=(14, 5))
librosa.display.specshow(
    mel_spec_db,
    sr=sr,
    x_axis='time',
    y_axis='mel',
    cmap='viridis'
)
plt.colorbar(format='%+2.0f dB')
plt.title('Spectrogramme Mel')
plt.tight_layout()
plt.show()
```

### 3.4 Prétraiter un audio

```python
# Importer processeur
sys.path.append('../scripts/preprocess')
from process_audio import AudioProcessor

# Créer processeur
processor = AudioProcessor(
    target_sr=22050,
    trim_silence=True,
    normalize=True
)

# Traiter
output_path = "../output/processed_sample.wav"
stats = processor.process_file(audio_path, output_path)

print(f"\n✅ Audio traité:")
print(f"   Durée: {stats['duration']:.2f}s")
print(f"   RMS: {stats['rms']:.4f}")
print(f"   Peak: {stats['peak']:.4f}")

# Écouter le résultat
processed_audio, processed_sr = librosa.load(output_path, sr=None)
display(Audio(processed_audio, rate=processed_sr))
```

---

## 4. Visualisation

### 4.1 Comparer avant/après prétraitement

```python
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Original
axes[0].set_title('Original')
librosa.display.waveshow(audio, sr=sr, ax=axes[0])
axes[0].set_xlabel('Temps (s)')
axes[0].set_ylabel('Amplitude')

# Traité
axes[1].set_title('Après prétraitement')
librosa.display.waveshow(processed_audio, sr=processed_sr, ax=axes[1])
axes[1].set_xlabel('Temps (s)')
axes[1].set_ylabel('Amplitude')

plt.tight_layout()
plt.show()
```

### 4.2 Analyse de la distribution RMS

```python
# Calculer RMS pour plusieurs samples
rms_values = []

for idx, row in df.head(100).iterrows():
    try:
        audio, sr = librosa.load(row['path'], sr=None)
        rms = np.sqrt(np.mean(audio ** 2))
        rms_values.append(rms)
    except:
        pass

# Visualiser
plt.figure(figsize=(10, 5))
plt.hist(rms_values, bins=30, edgecolor='black')
plt.xlabel('RMS')
plt.ylabel('Nombre de samples')
plt.title('Distribution RMS (100 premiers samples)')
plt.axvline(x=0.1, color='r', linestyle='--', label='Target RMS (0.1)')
plt.legend()
plt.show()
```

---

## 5. Clonage de Voix

### 5.1 Charger le modèle

```python
# Importer cloner
sys.path.append('../demo')
from clone_voice import VoiceCloner

# Chemin vers checkpoint
checkpoint_path = "../models/finetuned/xtts_multilingual/best_model.pth"

if os.path.exists(checkpoint_path):
    cloner = VoiceCloner(checkpoint_path=checkpoint_path)
    print("✅ Modèle chargé!")
else:
    print("⚠️  Checkpoint non trouvé. Entraînez d'abord un modèle.")
    cloner = None
```

### 5.2 Cloner une voix

```python
if cloner:
    # Audio de référence
    reference_audio = "../samples/reference.wav"
    
    # Texte à synthétiser
    text = "Bonjour, ceci est un test de clonage vocal."
    
    # Générer
    output_path = "../output/cloned_voice.wav"
    
    cloner.clone_voice(
        reference_audio=reference_audio,
        text=text,
        language="fr",
        output_path=output_path,
        temperature=0.75,
        speed=1.0
    )
    
    # Écouter
    cloned_audio, cloned_sr = librosa.load(output_path, sr=None)
    display(Audio(cloned_audio, rate=cloned_sr))
```

### 5.3 Comparer référence et clone

```python
if cloner and os.path.exists(reference_audio):
    # Charger référence
    ref_audio, ref_sr = librosa.load(reference_audio, sr=None)
    
    # Visualiser
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    axes[0].set_title('Audio de référence')
    librosa.display.waveshow(ref_audio, sr=ref_sr, ax=axes[0])
    
    axes[1].set_title('Audio cloné')
    librosa.display.waveshow(cloned_audio, sr=cloned_sr, ax=axes[1])
    
    plt.tight_layout()
    plt.show()
```

---

## 6. Évaluation

### 6.1 Calculer similarité vocale

```python
# TODO: Implémenter calcul de similarité
# Nécessite speechbrain ou modèle d'embedding

print("⚠️  Calcul de similarité non implémenté dans ce notebook")
print("   Utilisez evaluate.py pour une évaluation complète")
```

### 6.2 Statistiques du dataset

```python
# Résumé final
print("📊 Résumé du Dataset:")
print(f"   Total samples: {len(df)}")

if 'duration' in df.columns:
    total_hours = df['duration'].sum() / 3600
    print(f"   Durée totale: {total_hours:.1f}h")
    print(f"   Durée moyenne: {df['duration'].mean():.2f}s")
    print(f"   Durée médiane: {df['duration'].median():.2f}s")

if 'language' in df.columns:
    print(f"\n   Langues: {', '.join(df['language'].unique())}")

if 'speaker_id' in df.columns:
    print(f"   Speakers: {df['speaker_id'].nunique()}")
```

---

## 🎯 Prochaines Étapes

1. **Télécharger plus de données** : `scripts/download/download_all.sh`
2. **Entraîner un modèle** : `python train.py --config configs/xtts_multilingual.yaml`
3. **Évaluer** : `python evaluate.py --checkpoint <path> --test_csv <path>`

---

**📚 Documentation complète** : Voir `README.md`, `QUICKSTART.md`, `EXAMPLES.md`
