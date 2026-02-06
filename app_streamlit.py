#!/usr/bin/env python3
"""
🎙️ StarConnect Voice Cloning Studio
Premium Streamlit UI with Multi-Agent Backend
"""

import streamlit as st
import os
import sys
import json
import time
import wave
import struct
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="StarConnect Voice Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOM CSS - Premium Design
# ═══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Dark theme with blue accents */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #a0a0c0;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards */
    .config-card {
        background: rgba(30, 30, 60, 0.8);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .config-card h3 {
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    /* Parameter labels */
    .param-label {
        color: #667eea;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }
    
    .param-desc {
        color: #808090;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Status indicators */
    .status-online {
        color: #4ade80;
        font-weight: 600;
    }
    
    .status-offline {
        color: #f87171;
        font-weight: 600;
    }
    
    /* Generate button */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    
    /* Sliders */
    .stSlider > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Text areas */
    .stTextArea > div > div > textarea {
        background: rgba(30, 30, 60, 0.6);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 8px;
        color: #e0e0f0;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(30, 30, 60, 0.6);
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    /* Segment cards */
    .segment-card {
        background: rgba(40, 40, 80, 0.6);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .segment-card:hover {
        border-color: #667eea;
        transform: translateX(5px);
    }
    
    .segment-card.selected {
        border-color: #764ba2;
        background: rgba(102, 126, 234, 0.2);
    }
    
    /* Audio player */
    audio {
        width: 100%;
        border-radius: 8px;
    }
    
    /* Metrics */
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-label {
        color: #808090;
        font-size: 0.9rem;
    }
    
    /* Processing animation */
    .processing {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #667eea;
    }
    
    .processing .dot {
        width: 8px;
        height: 8px;
        background: #667eea;
        border-radius: 50%;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# INITIALIZE STATE
# ═══════════════════════════════════════════════════════════════════

if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'selected_segment' not in st.session_state:
    st.session_state.selected_segment = None
if 'generated_audio' not in st.session_state:
    st.session_state.generated_audio = None
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []

# ═══════════════════════════════════════════════════════════════════
# DATASET LOADER
# ═══════════════════════════════════════════════════════════════════

DATASET_PATH = Path("/Users/yacinebenhamou/VoiceCloning/StarConnect")

@st.cache_data
def load_dataset():
    """Load StarConnect dataset."""
    segments = []
    
    for audio_file in sorted(DATASET_PATH.glob("segment_*.wav")):
        json_file = audio_file.parent / f"{audio_file.stem}_transcription.json"
        
        segment = {
            "id": audio_file.stem,
            "audio_path": str(audio_file),
            "transcription": "",
            "duration": 0
        }
        
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    segment["transcription"] = data.get("text", "")
                    segment["duration"] = data.get("duration", 0)
            except:
                pass
        
        # Get duration from audio if not in json
        if segment["duration"] == 0:
            try:
                with wave.open(str(audio_file), 'r') as wav:
                    segment["duration"] = wav.getnframes() / wav.getframerate()
            except:
                pass
        
        segments.append(segment)
    
    return segments

# ═══════════════════════════════════════════════════════════════════
# VOXCPM INTERFACE
# ═══════════════════════════════════════════════════════════════════

import requests

def check_voxcpm_status():
    """Check if VoxCPM is running."""
    try:
        response = requests.get("http://localhost:7860", timeout=2)
        return response.status_code == 200
    except:
        return False

def check_ollama_status():
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def query_ollama(prompt: str, model: str = "qwen3:8b") -> str:
    """Query Ollama LLM."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        return response.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════

st.markdown('<h1 class="main-header">🎙️ StarConnect Voice Studio</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Premium Voice Cloning powered by VoxCPM + Multi-Agent AI</p>', unsafe_allow_html=True)

# Status bar
col1, col2, col3, col4 = st.columns(4)

with col1:
    voxcpm_status = check_voxcpm_status()
    status_class = "status-online" if voxcpm_status else "status-offline"
    status_text = "● Online" if voxcpm_status else "○ Offline"
    st.markdown(f'<div class="metric-label">VoxCPM</div><div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)

with col2:
    ollama_status = check_ollama_status()
    status_class = "status-online" if ollama_status else "status-offline"
    status_text = "● Online" if ollama_status else "○ Offline"
    st.markdown(f'<div class="metric-label">Ollama LLM</div><div class="{status_class}">{status_text}</div>', unsafe_allow_html=True)

with col3:
    segments = load_dataset()
    st.markdown(f'<div class="metric-label">Dataset</div><div class="metric-value">{len(segments)}</div>', unsafe_allow_html=True)

with col4:
    total_duration = sum(s.get("duration", 0) for s in segments) / 60
    st.markdown(f'<div class="metric-label">Total Duration</div><div class="metric-value">{total_duration:.1f}m</div>', unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════

left_col, right_col = st.columns([1, 1.5])

# ═══════════════════════════════════════════════════════════════════
# LEFT COLUMN - Reference Selection
# ═══════════════════════════════════════════════════════════════════

with left_col:
    st.markdown("### 🎧 Reference Voice")
    
    # Segment selector
    segment_options = {s["id"]: f"{s['id']} ({s['duration']:.1f}s)" for s in segments[:50]}
    
    selected_id = st.selectbox(
        "Select Reference Segment",
        options=list(segment_options.keys()),
        format_func=lambda x: segment_options[x],
        key="segment_selector"
    )
    
    # Find selected segment
    selected_segment = next((s for s in segments if s["id"] == selected_id), None)
    
    if selected_segment:
        st.session_state.selected_segment = selected_segment
        
        # Audio player
        st.audio(selected_segment["audio_path"])
        
        # Transcription
        st.markdown("**Transcription:**")
        prompt_text = st.text_area(
            "Edit if needed",
            value=selected_segment.get("transcription", ""),
            height=100,
            key="prompt_text",
            label_visibility="collapsed"
        )
        
        # Duration info
        st.caption(f"Duration: {selected_segment['duration']:.2f}s")
    
    st.markdown("---")
    
    # ═══════════════════════════════════════════════════════════════
    # VoxCPM Configuration
    # ═══════════════════════════════════════════════════════════════
    
    st.markdown("### ⚙️ VoxCPM Configuration")
    
    # Preset selector
    preset = st.selectbox(
        "Quality Preset",
        options=["⚡ Fast", "⚖️ Balanced", "✨ High Quality", "💎 Extreme"],
        index=1
    )
    
    # Apply preset
    if "Fast" in preset:
        default_cfg, default_steps = 1.8, 6
    elif "High" in preset:
        default_cfg, default_steps = 2.3, 20
    elif "Extreme" in preset:
        default_cfg, default_steps = 2.5, 30
    else:
        default_cfg, default_steps = 2.0, 10
    
    # CFG Value
    st.markdown('<div class="param-label">CFG Value (Guidance Scale)</div>', unsafe_allow_html=True)
    st.markdown('<div class="param-desc">Higher = more like reference, Lower = more creative</div>', unsafe_allow_html=True)
    cfg_value = st.slider(
        "CFG",
        min_value=1.0,
        max_value=3.0,
        value=default_cfg,
        step=0.1,
        label_visibility="collapsed"
    )
    
    # Inference Timesteps
    st.markdown('<div class="param-label">Inference Timesteps</div>', unsafe_allow_html=True)
    st.markdown('<div class="param-desc">Higher = better quality but slower</div>', unsafe_allow_html=True)
    timesteps = st.slider(
        "Timesteps",
        min_value=4,
        max_value=30,
        value=default_steps,
        label_visibility="collapsed"
    )
    
    # Checkboxes
    col_a, col_b = st.columns(2)
    with col_a:
        enable_denoiser = st.checkbox("🔇 Denoise Audio", value=False)
    with col_b:
        enable_normalize = st.checkbox("📝 Normalize Text", value=True)

# ═══════════════════════════════════════════════════════════════════
# RIGHT COLUMN - Generation
# ═══════════════════════════════════════════════════════════════════

with right_col:
    st.markdown("### ✍️ Target Text")
    
    target_text = st.text_area(
        "Enter the text you want to synthesize",
        placeholder="Bonjour, je suis votre assistant vocal intelligent. Comment puis-je vous aider aujourd'hui?",
        height=150,
        key="target_text"
    )
    
    # Smart suggestions
    if ollama_status:
        with st.expander("🤖 AI Text Assistant"):
            suggestion_type = st.selectbox(
                "Get AI suggestions",
                ["Improve clarity", "Add emotion", "Make professional", "Translate to English"]
            )
            
            if st.button("Generate Suggestion"):
                with st.spinner("AI thinking..."):
                    prompt = f"Transform this text to '{suggestion_type}': {target_text}"
                    suggestion = query_ollama(prompt)
                    st.info(suggestion)
    
    st.markdown("---")
    
    # Generate button
    generate_clicked = st.button("🎤 Generate Speech", use_container_width=True, type="primary")
    
    # Generation logic
    if generate_clicked:
        if not target_text:
            st.error("Please enter target text!")
        elif not selected_segment:
            st.error("Please select a reference segment!")
        elif not voxcpm_status:
            st.error("VoxCPM is not running! Start it first.")
        else:
            with st.spinner("🎙️ Generating voice clone..."):
                # Build config
                config = {
                    "prompt_audio": selected_segment["audio_path"],
                    "prompt_text": prompt_text if 'prompt_text' in dir() else selected_segment.get("transcription", ""),
                    "target_text": target_text,
                    "cfg_value": cfg_value,
                    "inference_timesteps": timesteps,
                    "enable_denoiser": enable_denoiser,
                    "enable_text_normalization": enable_normalize
                }
                
                # Generate via CLI (CPU mode)
                import subprocess
                output_path = f"/tmp/starconnect_output_{int(time.time())}.wav"
                
                # Absolute path to voxcpm executable
                voxcpm_bin = "/Users/yacinebenhamou/.pyenv/versions/3.10.14/bin/voxcpm"
                
                cmd = [
                    voxcpm_bin,
                    "--text", target_text,
                    "--prompt-audio", selected_segment["audio_path"],
                    "--output", output_path,
                    "--cfg-value", str(cfg_value),
                    "--inference-timesteps", str(timesteps)
                ]
                
                # Handle prompt text (REQUIRED by CLI)
                p_text = prompt_text if 'prompt_text' in dir() and prompt_text else selected_segment.get("transcription", "")
                if not p_text:
                    # Fallback if no transcription exists
                    p_text = "ignored" 
                cmd.extend(["--prompt-text", p_text])
                
                if not enable_denoiser:
                    cmd.append("--no-denoiser")
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTORCH_ENABLE_MPS_FALLBACK": "1"}
                    )

                    
                    if Path(output_path).exists():
                        st.session_state.generated_audio = output_path
                        st.session_state.generation_history.append({
                            "timestamp": time.time(),
                            "config": config,
                            "output": output_path
                        })
                        st.success("✅ Generation complete!")
                    else:
                        st.error(f"Generation failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    st.error("Generation timed out (>5 minutes)")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Output section
    st.markdown("### 🔊 Output")
    
    if st.session_state.generated_audio and Path(st.session_state.generated_audio).exists():
        st.audio(st.session_state.generated_audio)
        
        # Download button
        with open(st.session_state.generated_audio, 'rb') as f:
            st.download_button(
                "📥 Download Audio",
                data=f.read(),
                file_name="starconnect_clone.wav",
                mime="audio/wav"
            )
        
        # Quality metrics
        try:
            with wave.open(st.session_state.generated_audio, 'r') as wav:
                duration = wav.getnframes() / wav.getframerate()
                st.caption(f"Duration: {duration:.2f}s | Sample Rate: {wav.getframerate()}Hz")
        except:
            pass
    else:
        st.info("Generated audio will appear here")

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR - Advanced Controls
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🎛️ Advanced Controls")
    
    st.markdown("### 📊 Dataset Stats")
    stats = {
        "Total Segments": len(segments),
        "With Transcription": sum(1 for s in segments if s.get("transcription")),
        "Avg Duration": f"{sum(s['duration'] for s in segments) / len(segments):.1f}s" if segments else "0s"
    }
    
    for label, value in stats.items():
        st.metric(label, value)
    
    st.markdown("---")
    
    st.markdown("### 🔧 System")
    
    if st.button("🔄 Refresh Status"):
        st.rerun()
    
    if st.button("🚀 Start VoxCPM"):
        os.system("cd /Users/yacinebenhamou/VoiceCloning/VoxCPM && PYTORCH_ENABLE_MPS_FALLBACK=1 CUDA_VISIBLE_DEVICES='' python app.py --device cpu &")
        st.info("Starting VoxCPM... Please wait 60s")
    
    st.markdown("---")
    
    st.markdown("### 📜 Generation History")
    
    for i, item in enumerate(reversed(st.session_state.generation_history[-5:])):
        with st.expander(f"Gen {len(st.session_state.generation_history) - i}"):
            st.json(item["config"])
            if Path(item["output"]).exists():
                st.audio(item["output"])

# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #606080; font-size: 0.9rem;">
    <p>🎙️ StarConnect Voice Studio | Powered by VoxCPM 1.5 + Ollama LLM</p>
    <p>Multi-Agent Voice Cloning System | Built for Perfect Control</p>
</div>
""", unsafe_allow_html=True)
