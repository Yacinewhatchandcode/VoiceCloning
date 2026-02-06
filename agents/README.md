# 🎙️ StarConnect Voice Cloning Agent System

## 🚀 Cutting-Edge 2026 Multi-Agent Architecture

This system leverages **local Ollama LLMs** and **state-of-the-art TTS models** for voice cloning.

---

## 📦 Available Agents

| Agent | File | Purpose |
|-------|------|---------|
| 🎯 **Orchestrator** | `orchestrator.py` | Master agent for pipeline coordination |
| 🎤 **Zero-Shot Cloning** | `zero_shot_cloning.py` | Instant voice cloning with VoxCPM/F5-TTS |
| 🔬 **Quality Agent** | `quality_agent.py` | Audio quality assessment & comparison |
| 🧠 **Ensemble Agent** | `ensemble_agent.py` | Multi-model synthesis & selection |
| ☁️ **Colab Agent** | `colab_agent.py` | Google Colab GPU orchestration |
| 🖥️ **GCP Agent** | `gcp_agent.py` | Google Cloud Platform deployment |
| 🚀 **RunPod Agent** | `runpod_agent.py` | RunPod GPU pod management |
| 🎮 **NVIDIA API Agent** | `nvidia_api_agent.py` | NVIDIA API integration |

---

## 🦙 Ollama Models Used

| Model | Size | Best For |
|-------|------|----------|
| `qwen3:8b` | 5.2 GB | **Reasoning & Planning** |
| `deepseek-r1:7b` | 4.7 GB | **Code & Technical** |
| `qwen2.5:3b` | 1.9 GB | **Fast, Simple Tasks** |
| `phi3:14b` | 7.9 GB | **Best Quality** |
| `llama3.2:3b` | 2.0 GB | **Balanced** |

---

## 🎯 Quick Start

### 1. Analyze Your Dataset
```bash
python starconnect.py analyze --dataset ./StarConnect
```

### 2. Create Voice Profile
```bash
python starconnect.py profile --dataset ./StarConnect --name MyVoice
```

### 3. Clone a Voice
```bash
python starconnect.py clone \
  --text "Bonjour, je suis votre assistant vocal." \
  --reference ./StarConnect/segment_001.wav \
  --ref-text "Bonjour, c'est Mani, producteur et manager."
```

### 4. Use Ensemble (Best Quality)
```bash
python starconnect.py ensemble \
  --text "Bonjour, je suis votre assistant vocal." \
  --reference ./StarConnect/segment_001.wav \
  --language fr
```

### 5. Assess Audio Quality
```bash
python starconnect.py assess --audio ./output.wav
```

### 6. Compare Original vs Cloned
```bash
python starconnect.py assess \
  --audio ./cloned.wav \
  --compare ./original.wav
```

---

## 🔧 CLI Commands

```
starconnect.py <command> [options]

Commands:
  analyze   - Analyze voice dataset with LLM
  select    - Select best reference samples
  profile   - Create voice profile
  clone     - Clone voice (single text)
  ensemble  - Use multi-model ensemble
  assess    - Assess audio quality
  batch     - Batch process multiple texts
  models    - List available TTS models
  ollama    - Check Ollama status
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER REQUEST                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              🎯 ORCHESTRATOR AGENT                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Ollama LLM (qwen3:8b)                          │   │
│  │  - Task planning                                 │   │
│  │  - Model selection                               │   │
│  │  - Quality reasoning                             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 🎤 Zero-Shot  │ │ 🧠 Ensemble   │ │ 🔬 Quality    │
│    Cloning    │ │    Agent      │ │    Agent      │
│               │ │               │ │               │
│ - VoxCPM      │ │ - VoxCPM      │ │ - SNR Analysis│
│ - F5-TTS      │ │ - F5-TTS      │ │ - Similarity  │
│ - Emotional   │ │ - XTTS        │ │ - LLM Report  │
└───────────────┘ └───────────────┘ └───────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   OUTPUT AUDIO                           │
│  - Cloned voice .wav                                     │
│  - Quality report                                        │
│  - LLM analysis                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 StarConnect Dataset

- **Total Segments**: 703 audio files
- **Total Duration**: ~64 minutes
- **Language**: French
- **Speaker**: Single speaker
- **Format**: WAV + JSON transcriptions

---

## 🎭 Emotional TTS

Generate speech with automatic emotion detection:

```bash
python starconnect.py clone \
  --text "Je suis tellement content de te voir!" \
  --reference ./StarConnect/segment_001.wav \
  --emotion auto
```

Supported emotions:
- `neutral`, `happy`, `sad`, `angry`, `surprised`
- `fearful`, `disgusted`, `professional`, `excited`

---

## 🔄 Training on Colab

1. Upload dataset to Google Drive
2. Open `notebooks/F5_TTS_Colab_Training.ipynb`
3. Run the polling cell
4. Trigger from local:

```bash
python agents/colab_agent.py trigger \
  --dataset /content/drive/MyDrive/f5_tts_datasets/starconnect_f5tts \
  --epochs 200
```

---

## 📈 Quality Metrics

The quality agent calculates:
- **SNR** (Signal-to-Noise Ratio)
- **Dynamic Range**
- **Clipping Detection**
- **Silence Ratio**
- **Intelligibility Score**
- **Naturalness Score**
- **Similarity Score** (vs reference)

---

## 🔗 Related Files

- `STARCONNECT_TRAINING_GUIDE.md` - Colab training guide
- `F5_TTS_INTEGRATION.md` - F5-TTS documentation
- `GPU_ORCHESTRATION_GUIDE.md` - Cloud GPU options
- `NVIDIA_FREE_OPTIONS.md` - Free NVIDIA resources

---

## ✅ Status

- [x] Orchestrator agent with LLM reasoning
- [x] Zero-shot cloning agent
- [x] Emotional TTS agent
- [x] Audio quality assessment
- [x] Multi-model ensemble
- [x] Unified CLI
- [x] Colab orchestration
- [x] 12 Ollama models available
- [x] 703 StarConnect segments processed

---

**Built with cutting-edge 2026 AI techniques** 🚀
