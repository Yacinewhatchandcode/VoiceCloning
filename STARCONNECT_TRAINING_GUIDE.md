# 🚀 Guide Rapide : Training StarConnect sur Colab (GRATUIT)

## ✅ Dataset Prêt

Le dataset StarConnect est préparé dans :
```
/Users/yacinebenhamou/VoiceCloning/datasets/starconnect_f5tts/
```

**Statistiques** :
- 650 segments audio
- 50.4 minutes d'audio
- Langue : Français
- Format : F5-TTS ready

---

## 📤 Étape 1 : Upload sur Google Drive

### Option A : Via Interface Web (Recommandé)

1. Ouvrir Google Drive : https://drive.google.com/
2. Créer un dossier `f5_tts_datasets`
3. Uploader le dossier `starconnect_f5tts` complet

### Option B : Via rclone (Plus rapide)

```bash
# Installer rclone si pas déjà fait
brew install rclone

# Configurer Google Drive
rclone config

# Uploader
rclone copy \
  /Users/yacinebenhamou/VoiceCloning/datasets/starconnect_f5tts \
  gdrive:f5_tts_datasets/starconnect_f5tts \
  --progress
```

---

## 🎓 Étape 2 : Lancer le Training sur Colab

### A. Ouvrir le Notebook Colab

Le notebook est déjà ouvert dans ton navigateur :
- **F5_TTS_Colab_Training.ipynb**
- GPU T4 activé ✅

### B. Exécuter les Cellules

**Cell 1** : Monter Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

**Cell 2** : Configuration
- Vérifie que `DRIVE_BASE` pointe vers ton dossier

**Cell 3** : Installation
- Installe F5-TTS et dépendances (~5 min)

**Cell 4** : Fonctions
- Charge les fonctions de training

**Cell 5** : Polling
- **LANCER CETTE CELL ET LAISSER TOURNER**
- Elle attend le trigger de l'agent

### C. Déclencher le Training depuis ton Mac

```bash
cd /Users/yacinebenhamou/VoiceCloning

# Lancer le training
python3 agents/colab_agent.py trigger \
  --dataset /content/drive/MyDrive/f5_tts_datasets/starconnect_f5tts \
  --languages fr \
  --epochs 200 \
  --batch_size 4 \
  --job_id starconnect_v1
```

---

## 📊 Étape 3 : Monitoring

### Depuis Colab

Le notebook affichera :
```
🚀 Trigger détecté! (poll #X)
   Job ID: starconnect_v1
🎓 Démarrage du training...
   Config: {...}
   Commande: python train.py --dataset_path ...
```

### Depuis ton Mac

```bash
# Vérifier le statut
python3 agents/colab_agent.py status

# Télécharger les checkpoints
python3 agents/colab_agent.py download \
  --output /Users/yacinebenhamou/VoiceCloning/checkpoints/starconnect_v1
```

---

## ⏱️ Temps Estimé

- **Upload dataset** : ~5-10 min (150 MB)
- **Installation Colab** : ~5 min
- **Training (200 epochs)** : ~2-4 heures
  - Colab gratuit : 12h max par session
  - Tu peux faire plusieurs sessions si nécessaire

---

## 🎯 Résultat Attendu

Après le training, tu auras :
- **Checkpoints** : Modèle entraîné sur la voix StarConnect
- **Logs** : Progression du training
- **Métriques** : Loss, accuracy, etc.

Tu pourras ensuite :
1. **Cloner la voix** avec n'importe quel texte en français
2. **Fine-tuner** davantage si nécessaire
3. **Déployer** le modèle en production

---

## 💡 Astuces

### Optimiser le Training

```python
# Dans le trigger, ajuster :
--epochs 200        # Plus = meilleur (mais plus long)
--batch_size 4      # Plus = plus rapide (mais plus de VRAM)
```

### Sauvegarder Régulièrement

Le notebook sauvegarde automatiquement :
- Checkpoints tous les 10 epochs
- Logs en temps réel
- Status dans `status.json`

### En Cas de Déconnexion

Si Colab se déconnecte :
1. Relancer la Cell 5 (polling)
2. Re-trigger depuis ton Mac
3. Le training reprendra au dernier checkpoint

---

## 🆘 Troubleshooting

### "No GPU available"
- Runtime → Change runtime type → GPU (T4)

### "Drive not mounted"
- Relancer Cell 1
- Autoriser l'accès à Drive

### "Dataset not found"
- Vérifier le chemin dans le trigger
- S'assurer que l'upload est terminé

### "Out of memory"
- Réduire `batch_size` à 2 ou 1
- Réduire la longueur max des segments

---

## ✅ Checklist

- [ ] Dataset uploadé sur Google Drive
- [ ] Notebook Colab ouvert avec GPU T4
- [ ] Cell 1-4 exécutées
- [ ] Cell 5 en cours (polling)
- [ ] Trigger envoyé depuis Mac
- [ ] Training en cours
- [ ] Checkpoints téléchargés

---

## 🎉 Prochaines Étapes

Une fois le training terminé :

```bash
# Tester le modèle
python3 demo/clone_voice.py \
  --checkpoint checkpoints/starconnect_v1/best.pth \
  --reference StarConnect/segment_001.wav \
  --text "Ceci est un test de clonage vocal avec F5-TTS" \
  --output test_starconnect.wav
```

**C'est parti ! 🚀**
