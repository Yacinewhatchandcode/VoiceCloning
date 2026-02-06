# ✅ Checklist d'Installation — Voice Cloning Pipeline

Utilisez cette checklist pour vérifier que votre installation est complète.

---

## 📋 Pré-requis Système

- [ ] **macOS** (ou Linux/Windows avec adaptations)
- [ ] **50+ GB d'espace disque** libre
- [ ] **8+ GB RAM** (16+ GB recommandé)
- [ ] **GPU NVIDIA** (optionnel, mais fortement recommandé pour entraînement)

---

## 🐍 Python & Environnement

- [ ] **Python 3.9+** installé (`python3 --version`)
- [ ] **pip** à jour (`pip --version`)
- [ ] **Environnement virtuel** créé (`venv/` existe)
- [ ] **Environnement activé** (`which python` pointe vers `venv/bin/python`)

**Commandes de vérification** :
```bash
python3 --version  # Doit afficher 3.9+
pip --version
source venv/bin/activate
which python  # Doit pointer vers ./venv/bin/python
```

---

## 📦 Dépendances Python

- [ ] **PyTorch** installé (`python -c "import torch; print(torch.__version__)"`)
- [ ] **TTS (Coqui)** installé (`python -c "import TTS; print(TTS.__version__)"`)
- [ ] **Librosa** installé (`python -c "import librosa; print(librosa.__version__)"`)
- [ ] **Pandas** installé (`python -c "import pandas; print(pandas.__version__)"`)
- [ ] **Toutes les dépendances** (`pip list | grep -E "torch|TTS|librosa"`)

**Commande de vérification** :
```bash
python scripts/check_setup.py
```

---

## 🔧 Outils Système

- [ ] **FFmpeg** installé (`ffmpeg -version`)
- [ ] **SoX** installé (`sox --version`)
- [ ] **Git** installé (optionnel, `git --version`)

**Installation macOS** :
```bash
brew install ffmpeg sox
```

**Installation Linux (Ubuntu/Debian)** :
```bash
sudo apt-get install ffmpeg sox
```

---

## 📁 Structure de Répertoires

- [ ] `datasets/raw/` existe
- [ ] `datasets/processed/` existe
- [ ] `datasets/metadata/` existe
- [ ] `models/pretrained/` existe
- [ ] `models/finetuned/` existe
- [ ] `logs/` existe
- [ ] `output/` existe
- [ ] `samples/` existe

**Commande de création** :
```bash
mkdir -p datasets/{raw,processed,metadata} models/{pretrained,finetuned} logs output samples
```

---

## 📄 Fichiers Essentiels

- [ ] `README.md` (6.4K)
- [ ] `QUICKSTART.md` (4.7K)
- [ ] `EXAMPLES.md` (9.2K)
- [ ] `RESOURCES.md` (6.6K)
- [ ] `requirements.txt` (1.0K)
- [ ] `setup.sh` (3.1K, exécutable)
- [ ] `train.py` (5.9K)
- [ ] `evaluate.py` (5.4K)
- [ ] `configs/xtts_multilingual.yaml`
- [ ] `scripts/download/download_commonvoice.py`
- [ ] `scripts/preprocess/process_audio.py`
- [ ] `demo/clone_voice.py`

**Vérification** :
```bash
ls -lh *.md *.py *.sh
ls -lh configs/ scripts/ demo/
```

---

## 🧪 Tests de Fonctionnement

### Test 1 : Vérification environnement
```bash
python scripts/check_setup.py
```
- [ ] ✅ Python Version OK
- [ ] ✅ Python Packages OK
- [ ] ✅ FFmpeg OK
- [ ] ✅ SoX OK (optionnel)
- [ ] ✅ GPU détecté (optionnel)
- [ ] ✅ Disk Space OK

### Test 2 : Import des modules critiques
```bash
python -c "
import torch
import TTS
import librosa
import pandas
import numpy
print('✅ Tous les imports fonctionnent!')
"
```
- [ ] Pas d'erreur d'import

### Test 3 : Téléchargement test (optionnel)
```bash
# Test avec un petit dataset
python scripts/download/download_arabic_corpus.py \
  --output datasets/raw/test_download
```
- [ ] Téléchargement réussi
- [ ] Fichiers dans `datasets/raw/test_download/`

---

## 🎯 Statut Final

### ✅ Installation Complète
Si tous les items ci-dessus sont cochés :
- Votre environnement est **100% opérationnel**
- Vous pouvez commencer à télécharger des datasets
- Consultez `START_HERE.md` pour les prochaines étapes

### ⚠️ Installation Partielle
Si certains items manquent :
- **Python/Dépendances** : Relancez `./setup.sh`
- **FFmpeg/SoX** : Installez avec `brew install ffmpeg sox`
- **GPU** : Optionnel, mais entraînement sera lent sans GPU

### ❌ Problèmes Persistants
- Consultez `QUICKSTART.md` section "Troubleshooting"
- Vérifiez les logs d'erreur
- Ouvrez une issue sur GitHub

---

## 📊 Résumé Rapide

```bash
# Commande tout-en-un pour vérification
./setup.sh && python scripts/check_setup.py
```

Si cette commande se termine avec **"✅ Environnement prêt pour l'entraînement!"**, vous êtes bon ! 🎉

---

**Prochaine étape** : Lire `START_HERE.md` pour votre premier test ! 🚀
