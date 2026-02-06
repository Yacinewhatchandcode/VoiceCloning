#!/bin/bash
# Script de téléchargement automatisé pour tous les datasets prioritaires

set -e  # Exit on error

echo "🚀 Téléchargement de tous les datasets prioritaires"
echo "=================================================="

# Répertoire de base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATASETS_DIR="${BASE_DIR}/datasets/raw"

echo "📁 Répertoire de base: ${BASE_DIR}"
echo "📁 Datasets: ${DATASETS_DIR}"
echo ""

# Créer répertoires
mkdir -p "${DATASETS_DIR}"

# Activer environnement virtuel si disponible
if [ -d "${BASE_DIR}/venv" ]; then
    echo "🐍 Activation de l'environnement virtuel..."
    source "${BASE_DIR}/venv/bin/activate"
fi

# 1. Mozilla Common Voice - Français
echo ""
echo "📥 [1/4] Téléchargement Common Voice Français..."
python "${BASE_DIR}/scripts/download/download_commonvoice.py" \
    --language fr \
    --version 17.0 \
    --output "${DATASETS_DIR}/commonvoice_fr" \
    --split train

# 2. Mozilla Common Voice - Arabe
echo ""
echo "📥 [2/4] Téléchargement Common Voice Arabe..."
python "${BASE_DIR}/scripts/download/download_commonvoice.py" \
    --language ar \
    --version 17.0 \
    --output "${DATASETS_DIR}/commonvoice_ar" \
    --split train

# 3. Arabic Speech Corpus
echo ""
echo "📥 [3/4] Téléchargement Arabic Speech Corpus..."
python "${BASE_DIR}/scripts/download/download_arabic_corpus.py" \
    --output "${DATASETS_DIR}/arabic_speech_corpus"

# 4. CSS10 French (optionnel, plus petit)
echo ""
echo "📥 [4/4] Téléchargement CSS10 French..."
# Note: CSS10 nécessite un script dédié ou téléchargement manuel
# Pour l'instant, on skip
echo "⚠️  CSS10 French: téléchargement manuel requis"
echo "   URL: https://github.com/Kyubyong/css10"

echo ""
echo "=================================================="
echo "✅ Téléchargements terminés!"
echo ""
echo "📊 Résumé:"
echo "   - Common Voice FR: ${DATASETS_DIR}/commonvoice_fr"
echo "   - Common Voice AR: ${DATASETS_DIR}/commonvoice_ar"
echo "   - Arabic Corpus: ${DATASETS_DIR}/arabic_speech_corpus"
echo ""
echo "🔄 Prochaine étape: Prétraitement"
echo "   python scripts/preprocess/process_audio.py --input datasets/raw/commonvoice_fr --output datasets/processed/commonvoice_fr"
