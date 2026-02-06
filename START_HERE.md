# 🎙️ Voice Cloning Pipeline — Guide de Démarrage Ultra-Rapide

## ⚡ Installation en 3 Commandes

```bash
# 1. Lancer le setup automatisé
./setup.sh

# 2. Activer l'environnement (si pas déjà fait)
source venv/bin/activate

# 3. Vérifier que tout fonctionne
python scripts/check_setup.py
```

**C'est tout !** Votre environnement est prêt. 🎉

---

## 🚀 Premier Test (5 minutes)

### Option A : Test avec Arabic Speech Corpus (petit dataset)

```bash
# 1. Télécharger (rapide, ~1.5GB)
python scripts/download/download_arabic_corpus.py \
  --output datasets/raw/arabic_corpus

# 2. Prétraiter
python scripts/preprocess/process_audio.py \
  --input datasets/raw/arabic_corpus/audio \
  --output datasets/processed/arabic_corpus \
  --metadata datasets/raw/arabic_corpus/metadata.csv \
  --workers 4

# 3. Générer metadata
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice \
  --input datasets/processed/arabic_corpus \
  --language ar \
  --output datasets/metadata/ar_metadata.csv
```

### Option B : Test avec Common Voice (plus long mais plus de données)

```bash
# 1. Télécharger Common Voice FR (train uniquement)
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr \
  --split train

# 2. Prétraiter
python scripts/preprocess/process_audio.py \
  --input datasets/raw/commonvoice_fr/train \
  --output datasets/processed/commonvoice_fr \
  --sample_rate 22050 \
  --trim_silence \
  --normalize \
  --workers 8

# 3. Metadata
python scripts/metadata/generate_metadata.py generate \
  --dataset commonvoice \
  --input datasets/processed/commonvoice_fr \
  --language fr \
  --output datasets/metadata/fr_metadata.csv
```

---

## 📖 Documentation Complète

- **README.md** — Vue d'ensemble et architecture
- **QUICKSTART.md** — Guide détaillé étape par étape
- **EXAMPLES.md** — 50+ exemples pratiques
- **RESOURCES.md** — Tous les datasets et outils
- **DELIVERY_SUMMARY.md** — Résumé de ce qui a été livré

---

## 🆘 Problèmes Courants

### "FFmpeg not found"
```bash
brew install ffmpeg sox
```

### "CUDA out of memory"
Réduisez `batch_size` dans `configs/xtts_multilingual.yaml` :
```yaml
training:
  batch_size: 8  # au lieu de 16
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 💬 Questions ?

Consultez la documentation ou ouvrez une issue sur GitHub.

**Bon clonage vocal ! 🎙️✨**
