#!/bin/bash
# Entrypoint script pour container F5-TTS
# Lance le training avec les paramètres d'environnement

set -e

echo "🚀 F5-TTS Training Container"
echo "=============================="
echo ""

# Afficher configuration
echo "📋 Configuration:"
echo "   Dataset: ${DATASET}"
echo "   Languages: ${LANGUAGES}"
echo "   Epochs: ${EPOCHS}"
echo "   Batch size: ${BATCH_SIZE}"
echo "   Device: ${DEVICE}"
echo "   Checkpoint dir: ${CHECKPOINT_DIR}"
echo "   Log dir: ${LOG_DIR}"
echo ""

# Vérifier que le dataset existe
if [ ! -d "${DATASET}" ]; then
    echo "⚠️  Warning: Dataset directory not found: ${DATASET}"
    echo "   Assurez-vous de monter le volume correctement"
fi

# Vérifier GPU
if [ "${DEVICE}" = "cuda" ]; then
    echo "🖥️  Vérification GPU..."
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        echo "⚠️  nvidia-smi non disponible"
    fi
    echo ""
fi

# Convertir LANGUAGES (comma-separated) en arguments
IFS=',' read -ra LANG_ARRAY <<< "$LANGUAGES"
LANG_ARGS=""
for lang in "${LANG_ARRAY[@]}"; do
    LANG_ARGS="$LANG_ARGS $lang"
done

# Lancer training
echo "🎓 Démarrage du training..."
echo ""

cd /opt/F5-TTS

python3 train.py \
    --dataset_path "${DATASET}" \
    --multilingual true \
    --languages ${LANG_ARGS} \
    --epochs ${EPOCHS} \
    --batch_size ${BATCH_SIZE} \
    --device ${DEVICE} \
    --checkpoint_dir "${CHECKPOINT_DIR}" \
    --log_dir "${LOG_DIR}" \
    --save_every 5000 \
    --eval_every 2500 \
    2>&1 | tee "${LOG_DIR}/training.log"

EXIT_CODE=$?

echo ""
echo "=============================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Training terminé avec succès!"
else
    echo "❌ Training échoué (exit code: $EXIT_CODE)"
fi
echo "=============================="

# Lister les checkpoints créés
if [ -d "${CHECKPOINT_DIR}" ]; then
    echo ""
    echo "📦 Checkpoints créés:"
    ls -lh "${CHECKPOINT_DIR}"
fi

exit $EXIT_CODE
