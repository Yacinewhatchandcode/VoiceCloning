# 📚 Ressources & Datasets — Voice Cloning FR/AR

Ce document liste toutes les ressources, datasets et liens utiles pour le voice cloning en français et arabe.

## 🎯 Datasets Prioritaires

### 1. Mozilla Common Voice

**Description**: Corpus communautaire massif avec contributions de locuteurs natifs.

- **Langues**: Français, Arabe (MSA + dialectes)
- **Durée**: ~500h (FR), ~300h (AR)
- **Format**: MP3 + TSV (transcriptions)
- **Licence**: CC-0 (domaine public)
- **Qualité**: Variable (crowdsourced)

**Liens**:
- [Site officiel](https://commonvoice.mozilla.org/)
- [HuggingFace](https://huggingface.co/datasets/mozilla-foundation/common_voice_17_0)
- [Documentation](https://commonvoice.mozilla.org/fr/datasets)

**Téléchargement**:
```bash
python scripts/download/download_commonvoice.py \
  --language fr \
  --version 17.0 \
  --output datasets/raw/commonvoice_fr
```

---

### 2. Arabic Speech Corpus (MSA)

**Description**: Dataset single-speaker haute qualité pour Modern Standard Arabic.

- **Langue**: Arabe (MSA uniquement)
- **Durée**: ~1.5h
- **Format**: WAV + TXT
- **Licence**: Academic use
- **Qualité**: Excellente (studio)

**Liens**:
- [HuggingFace](https://huggingface.co/datasets/tunis-ai/arabic_speech_corpus)
- [Paper original](https://www.researchgate.net/publication/308278946_Arabic_Speech_Corpus_for_Isolated_Words)

**Téléchargement**:
```bash
python scripts/download/download_arabic_corpus.py \
  --output datasets/raw/arabic_corpus
```

---

### 3. Multilingual LibriSpeech (MLS) — French

**Description**: Audiobooks lus en français, dérivé de LibriVox.

- **Langue**: Français
- **Durée**: ~1000h
- **Format**: FLAC + TXT
- **Licence**: CC-BY 4.0
- **Qualité**: Bonne (audiobooks)

**Liens**:
- [OpenSLR](https://www.openslr.org/94/)
- [Paper](https://arxiv.org/abs/2012.03411)

**Téléchargement**:
```bash
# Téléchargement manuel requis (très volumineux)
wget https://dl.fbaipublicfiles.com/mls/mls_french.tar.gz
tar -xzf mls_french.tar.gz -C datasets/raw/
```

---

### 4. CSS10 — French

**Description**: Single-speaker TTS dataset pour français.

- **Langue**: Français
- **Durée**: ~24h
- **Format**: WAV + TXT
- **Licence**: Public Domain
- **Qualité**: Bonne (single speaker)

**Liens**:
- [GitHub](https://github.com/Kyubyong/css10)
- [Kaggle](https://www.kaggle.com/datasets/bryanpark/french-single-speaker-speech-dataset)

**Téléchargement**:
```bash
# Via Kaggle API
kaggle datasets download -d bryanpark/french-single-speaker-speech-dataset
unzip french-single-speaker-speech-dataset.zip -d datasets/raw/css10_fr
```

---

### 5. MGB-2 Arabic (Aljazeera)

**Description**: Large-scale Arabic broadcast dataset (multi-dialectal).

- **Langue**: Arabe (MSA + dialectes)
- **Durée**: ~1200h
- **Format**: WAV + XML
- **Licence**: Academic use
- **Qualité**: Variable (broadcast)

**Liens**:
- [HuggingFace](https://huggingface.co/datasets/MohamedRashad/mgb2-arabic)
- [Official site](https://arabicspeech.org/mgb2/)

**Note**: Très volumineux, nécessite nettoyage important.

---

## 📊 Comparaison des Datasets

| Dataset | Langue | Durée | Speakers | Qualité | Licence | Difficulté |
|---------|--------|-------|----------|---------|---------|------------|
| **Common Voice** | FR/AR | 500h/300h | Multi | ⭐⭐⭐ | CC-0 | Facile |
| **Arabic Corpus** | AR (MSA) | 1.5h | 1 | ⭐⭐⭐⭐⭐ | Academic | Facile |
| **MLS French** | FR | 1000h | Multi | ⭐⭐⭐⭐ | CC-BY 4.0 | Moyen |
| **CSS10** | FR | 24h | 1 | ⭐⭐⭐⭐ | Public | Facile |
| **MGB-2** | AR | 1200h | Multi | ⭐⭐ | Academic | Difficile |

---

## 🔧 Outils & Bibliothèques

### Voice Cloning Frameworks

1. **Coqui TTS (XTTS v2)**
   - [GitHub](https://github.com/coqui-ai/TTS)
   - [Docs](https://docs.coqui.ai/)
   - ✅ Recommandé pour ce projet

2. **Tortoise TTS**
   - [GitHub](https://github.com/neonbjb/tortoise-tts)
   - Haute qualité, mais lent

3. **Bark**
   - [GitHub](https://github.com/suno-ai/bark)
   - Multilingue, mais nécessite beaucoup de VRAM

### Audio Processing

- **Librosa**: [Docs](https://librosa.org/)
- **SoX**: [Manual](http://sox.sourceforge.net/sox.html)
- **FFmpeg**: [Docs](https://ffmpeg.org/documentation.html)
- **Pydub**: [GitHub](https://github.com/jiaaro/pydub)

### NLP & Text Processing

- **CAMeL Tools** (Arabic): [GitHub](https://github.com/CAMeL-Lab/camel_tools)
- **Phonemizer**: [GitHub](https://github.com/bootphon/phonemizer)
- **SentencePiece**: [GitHub](https://github.com/google/sentencepiece)

---

## 📖 Ressources Académiques

### Papers Importants

1. **XTTS v2** (2023)
   - [Paper](https://arxiv.org/abs/2406.04904)
   - Multilingual zero-shot voice cloning

2. **YourTTS** (2021)
   - [Paper](https://arxiv.org/abs/2112.02418)
   - Zero-shot multi-speaker TTS

3. **Arabic TTS Survey** (2022)
   - [Paper](https://ieeexplore.ieee.org/document/9721204)
   - État de l'art pour l'arabe

### Tutoriels & Guides

- [Coqui TTS Fine-tuning Guide](https://tts.readthedocs.io/en/latest/tutorial_for_nervous_beginners.html)
- [HuggingFace Audio Course](https://huggingface.co/learn/audio-course)
- [Arabic NLP Resources](https://github.com/ARBML/masader)

---

## 🌐 Collections & Indexes

### HuggingFace Collections

- [Arabic Speech Datasets](https://huggingface.co/collections/MohamedRashad/arabic-speech-datasets)
- [TTS Datasets](https://huggingface.co/datasets?task_categories=task_categories:text-to-speech)

### Awesome Lists

- [Awesome TTS](https://github.com/erogol/awesome-tts)
- [Awesome Arabic NLP](https://github.com/ARBML/awesome-arabic-nlp)

---

## ⚖️ Considérations Légales

### Licences Courantes

- **CC-0**: Domaine public, usage libre
- **CC-BY 4.0**: Attribution requise
- **Academic Use**: Recherche uniquement, pas commercial

### Éthique du Voice Cloning

⚠️ **IMPORTANT**: 
- Obtenez toujours le **consentement explicite** avant de cloner une voix
- Ne pas utiliser pour **impersonation** ou **fraude**
- Respectez les lois locales sur les **deepfakes**
- Ajoutez des **watermarks** si possible

### Ressources Légales

- [EU AI Act](https://artificialintelligenceact.eu/)
- [Deepfake Laws by Country](https://www.dlapiper.com/en/insights/publications/2023/11/deepfakes-laws-and-regulations)

---

## 🔗 Liens Rapides

### Téléchargement Direct

- [Common Voice FR (latest)](https://commonvoice.mozilla.org/fr/datasets)
- [Common Voice AR (latest)](https://commonvoice.mozilla.org/ar/datasets)
- [MLS French](https://dl.fbaipublicfiles.com/mls/mls_french.tar.gz)

### Communautés

- [Coqui Discord](https://discord.gg/coqui)
- [HuggingFace Forums](https://discuss.huggingface.co/)
- [r/MachineLearning](https://www.reddit.com/r/MachineLearning/)

---

**Dernière mise à jour**: Janvier 2026
