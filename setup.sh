#!/bin/bash
# Script de setup initial pour Voice Cloning Pipeline

set -e

echo "🚀 Voice Cloning Pipeline — Setup Initial"
echo "=========================================="
echo ""

# Couleurs pour output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher succès
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Fonction pour afficher warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Fonction pour afficher erreur
error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Vérifier Python
echo "1️⃣  Vérification de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    success "Python $PYTHON_VERSION trouvé"
else
    error "Python 3 non trouvé. Installez Python 3.9+"
    exit 1
fi

# 2. Créer environnement virtuel
echo ""
echo "2️⃣  Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Environnement virtuel créé"
else
    warning "Environnement virtuel existe déjà"
fi

# 3. Activer environnement
echo ""
echo "3️⃣  Activation de l'environnement virtuel..."
source venv/bin/activate
success "Environnement activé"

# 4. Mettre à jour pip
echo ""
echo "4️⃣  Mise à jour de pip..."
pip install --upgrade pip --quiet
success "pip mis à jour"

# 5. Installer dépendances
echo ""
echo "5️⃣  Installation des dépendances Python..."
echo "   (Cela peut prendre 5-10 minutes...)"
pip install -r requirements.txt --quiet
success "Dépendances installées"

# 6. Vérifier FFmpeg
echo ""
echo "6️⃣  Vérification de FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    success "FFmpeg trouvé"
else
    warning "FFmpeg non trouvé"
    echo "   Installation recommandée: brew install ffmpeg"
fi

# 7. Vérifier SoX
echo ""
echo "7️⃣  Vérification de SoX..."
if command -v sox &> /dev/null; then
    success "SoX trouvé"
else
    warning "SoX non trouvé"
    echo "   Installation recommandée: brew install sox"
fi

# 8. Créer répertoires
echo ""
echo "8️⃣  Création des répertoires..."
mkdir -p datasets/{raw,processed,metadata}
mkdir -p models/{pretrained,finetuned}
mkdir -p logs tensorboard output samples
success "Répertoires créés"

# 9. Rendre scripts exécutables
echo ""
echo "9️⃣  Configuration des permissions..."
chmod +x scripts/download/download_all.sh
chmod +x scripts/check_setup.py
success "Permissions configurées"

# 10. Vérification finale
echo ""
echo "🔟  Vérification finale de l'environnement..."
python scripts/check_setup.py

echo ""
echo "=========================================="
echo "✅ Setup terminé avec succès!"
echo ""
echo "📚 Prochaines étapes:"
echo "   1. Lire QUICKSTART.md pour démarrer rapidement"
echo "   2. Télécharger un dataset:"
echo "      python scripts/download/download_commonvoice.py --language fr --version 17.0 --output datasets/raw/commonvoice_fr --split train"
echo "   3. Consulter EXAMPLES.md pour plus d'exemples"
echo ""
echo "💡 Pour activer l'environnement virtuel à l'avenir:"
echo "   source venv/bin/activate"
echo ""
echo "🎙️ Bon clonage vocal!"
echo "=========================================="
