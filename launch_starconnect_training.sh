#!/bin/bash
# Script pour lancer le training StarConnect sur Colab

echo "🚀 Lancement du training StarConnect sur Colab"
echo ""

# Configuration
DATASET_PATH="/content/drive/MyDrive/f5_tts_datasets/starconnect_f5tts"
LANGUAGES="fr"
EPOCHS=200
BATCH_SIZE=4
JOB_ID="starconnect_v1"

echo "📊 Configuration:"
echo "   Dataset: $DATASET_PATH"
echo "   Langue: $LANGUAGES"
echo "   Epochs: $EPOCHS"
echo "   Batch Size: $BATCH_SIZE"
echo "   Job ID: $JOB_ID"
echo ""

# Vérifier que l'agent existe
if [ ! -f "agents/colab_agent.py" ]; then
    echo "❌ Erreur: agents/colab_agent.py non trouvé"
    exit 1
fi

echo "🎯 Envoi du trigger à Colab..."
python3 agents/colab_agent.py trigger \
    --dataset "$DATASET_PATH" \
    --languages "$LANGUAGES" \
    --epochs "$EPOCHS" \
    --batch_size "$BATCH_SIZE" \
    --job_id "$JOB_ID"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Trigger envoyé avec succès!"
    echo ""
    echo "📝 Prochaines étapes:"
    echo "   1. Vérifier le notebook Colab (Cell 5 doit afficher le trigger)"
    echo "   2. Le training va démarrer automatiquement"
    echo "   3. Surveiller les logs dans Colab"
    echo ""
    echo "💡 Pour vérifier le statut:"
    echo "   python3 agents/colab_agent.py status"
    echo ""
    echo "💡 Pour télécharger les checkpoints:"
    echo "   python3 agents/colab_agent.py download --output checkpoints/starconnect_v1"
else
    echo ""
    echo "❌ Erreur lors de l'envoi du trigger"
    exit 1
fi
