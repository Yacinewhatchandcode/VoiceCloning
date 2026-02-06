#!/usr/bin/env python3
"""
🎛️ VoxCPM Configuration & Control System
Complete parameter definition with functional understanding.
Extracted from VoxCPM 1.5 interface.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from enum import Enum
import json


class QualityPreset(Enum):
    """Quality presets for quick configuration."""
    FAST = "fast"           # Quick generation, lower quality
    BALANCED = "balanced"   # Default balance
    HIGH_QUALITY = "high"   # Maximum quality, slower
    EXTREME = "extreme"     # Best possible, very slow


@dataclass
class VoxCPMConfig:
    """
    Complete VoxCPM Configuration with functional documentation.
    
    INTERFACE COMPONENTS (from DOM analysis):
    =========================================
    
    1. PROMPT SPEECH (Audio Input)
       - Type: Audio file upload
       - Purpose: Reference voice sample for cloning
       - Optimal: 3-10 seconds of clear speech
       - Format: WAV, MP3, FLAC
       
    2. PROMPT SPEECH ENHANCEMENT
       - Type: Checkbox (boolean)
       - Purpose: Uses ZipEnhancer to denoise reference audio
       - When to use: If reference has background noise
       - Effect: Cleaner voice extraction, may lose some character
       
    3. PROMPT TEXT
       - Type: Text input
       - Purpose: Transcription of the reference audio
       - Critical: Must match what speaker says in reference
       - If empty: Model tries to infer (less accurate)
       
    4. CFG VALUE (Guidance Scale)
       - Type: Slider (1.0 - 3.0)
       - Default: 2.0
       - Purpose: Controls adherence to prompt voice
       - Low (1.0): More creative, may deviate from voice
       - High (3.0): Strict adherence to reference voice
       - Recommendation: 2.0-2.5 for best balance
       
    5. INFERENCE TIMESTEPS
       - Type: Slider (4 - 30)
       - Default: 10
       - Purpose: Number of diffusion steps
       - Low (4-8): Fast generation, lower quality
       - High (20-30): Better quality, 3x slower
       - Sweet spot: 10-15 for good quality/speed
       
    6. TARGET TEXT
       - Type: Text area
       - Purpose: The text you want the cloned voice to say
       - Supports: Multilingual (FR, EN, ZH, etc.)
       
    7. TEXT NORMALIZATION
       - Type: Checkbox (boolean)
       - Purpose: Uses wetext library for text preprocessing
       - Effect: Converts numbers, abbreviations, symbols
       - Example: "123" → "one hundred twenty-three"
    """
    
    # ═══════════════════════════════════════════════════════════════
    # AUDIO INPUT SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    prompt_audio_path: Optional[str] = None
    """Path to reference audio file (3-10 seconds optimal)"""
    
    prompt_text: str = ""
    """Transcription of reference audio. Must match spoken content."""
    
    enable_denoiser: bool = False
    """
    ZipEnhancer denoising on reference audio.
    - True: Cleaner voice, may lose subtle characteristics
    - False: Preserves original voice character, may have noise
    Use when: Reference has background noise or reverb
    """
    
    # ═══════════════════════════════════════════════════════════════
    # GENERATION SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    cfg_value: float = 2.0
    """
    Classifier-Free Guidance Scale (1.0 - 3.0)
    
    Controls how closely the output matches the reference voice:
    - 1.0: Maximum creativity, may not sound like reference
    - 1.5: Creative, allows natural variation
    - 2.0: Balanced (DEFAULT) - sounds like reference with naturalness
    - 2.5: Strong adherence, very similar to reference
    - 3.0: Maximum adherence, may sound robotic
    
    Recommendation: Start at 2.0, increase if voice doesn't match
    """
    
    inference_timesteps: int = 10
    """
    Diffusion model inference steps (4 - 30)
    
    Quality vs Speed trade-off:
    - 4:  Ultra-fast (~2s), lowest quality
    - 8:  Fast (~4s), acceptable quality
    - 10: Balanced (~6s) (DEFAULT)
    - 15: Good quality (~10s)
    - 20: High quality (~15s)
    - 30: Maximum quality (~25s)
    
    GPU: ~1s per 10 steps, CPU: ~5s per 10 steps
    """
    
    # ═══════════════════════════════════════════════════════════════
    # OUTPUT SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    target_text: str = ""
    """Text to synthesize with the cloned voice."""
    
    enable_text_normalization: bool = True
    """
    Text preprocessing with wetext library.
    - Converts numbers: "123" → "one hundred twenty-three"
    - Expands abbreviations: "Dr." → "Doctor"
    - Handles symbols: "$100" → "one hundred dollars"
    
    Disable for: Pre-formatted text or special pronunciations
    """
    
    output_path: Optional[str] = None
    """Path to save generated audio."""
    
    # ═══════════════════════════════════════════════════════════════
    # ADVANCED SETTINGS (Not in UI but available in API)
    # ═══════════════════════════════════════════════════════════════
    
    sample_rate: int = 24000
    """Output audio sample rate in Hz."""
    
    seed: Optional[int] = None
    """Random seed for reproducibility. None = random."""
    
    streaming: bool = False
    """Enable streaming output for real-time generation."""
    
    language: str = "auto"
    """Language hint: 'auto', 'en', 'zh', 'fr', 'de', etc."""
    
    # ═══════════════════════════════════════════════════════════════
    # PRESETS
    # ═══════════════════════════════════════════════════════════════
    
    @classmethod
    def fast_preset(cls) -> "VoxCPMConfig":
        """Fast generation, lower quality."""
        return cls(
            cfg_value=1.8,
            inference_timesteps=6,
            enable_denoiser=False,
            enable_text_normalization=True
        )
    
    @classmethod
    def balanced_preset(cls) -> "VoxCPMConfig":
        """Balanced quality and speed (DEFAULT)."""
        return cls(
            cfg_value=2.0,
            inference_timesteps=10,
            enable_denoiser=False,
            enable_text_normalization=True
        )
    
    @classmethod
    def high_quality_preset(cls) -> "VoxCPMConfig":
        """High quality, slower generation."""
        return cls(
            cfg_value=2.3,
            inference_timesteps=20,
            enable_denoiser=True,
            enable_text_normalization=True
        )
    
    @classmethod
    def extreme_preset(cls) -> "VoxCPMConfig":
        """Maximum quality, slowest generation."""
        return cls(
            cfg_value=2.5,
            inference_timesteps=30,
            enable_denoiser=True,
            enable_text_normalization=True
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "prompt_audio_path": self.prompt_audio_path,
            "prompt_text": self.prompt_text,
            "enable_denoiser": self.enable_denoiser,
            "cfg_value": self.cfg_value,
            "inference_timesteps": self.inference_timesteps,
            "target_text": self.target_text,
            "enable_text_normalization": self.enable_text_normalization,
            "output_path": self.output_path,
            "sample_rate": self.sample_rate,
            "seed": self.seed,
            "streaming": self.streaming,
            "language": self.language
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "VoxCPMConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


# ═══════════════════════════════════════════════════════════════════
# PARAMETER VALIDATION & OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════

def validate_config(config: VoxCPMConfig) -> List[str]:
    """Validate configuration and return warnings."""
    warnings = []
    
    if config.cfg_value < 1.0 or config.cfg_value > 3.0:
        warnings.append(f"CFG value {config.cfg_value} outside optimal range [1.0, 3.0]")
    
    if config.inference_timesteps < 4:
        warnings.append(f"Timesteps {config.inference_timesteps} too low, quality will suffer")
    elif config.inference_timesteps > 30:
        warnings.append(f"Timesteps {config.inference_timesteps} very high, will be slow")
    
    if not config.prompt_text and config.prompt_audio_path:
        warnings.append("No prompt text provided - model will auto-transcribe (less accurate)")
    
    if config.enable_denoiser and not config.prompt_audio_path:
        warnings.append("Denoiser enabled but no audio provided")
    
    return warnings


def optimize_for_speed(config: VoxCPMConfig) -> VoxCPMConfig:
    """Optimize config for fastest generation."""
    config.inference_timesteps = 6
    config.cfg_value = 1.8
    config.enable_denoiser = False
    return config


def optimize_for_quality(config: VoxCPMConfig) -> VoxCPMConfig:
    """Optimize config for best quality."""
    config.inference_timesteps = 25
    config.cfg_value = 2.4
    config.enable_denoiser = True
    return config


# ═══════════════════════════════════════════════════════════════════
# DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════

PARAMETER_DOCS = {
    "cfg_value": {
        "name": "CFG Value (Guidance Scale)",
        "type": "float",
        "range": [1.0, 3.0],
        "default": 2.0,
        "description": "Controls how closely output matches reference voice",
        "tips": [
            "Start at 2.0 for most cases",
            "Increase to 2.5 if voice doesn't match well",
            "Decrease to 1.5 for more natural variation",
            "Values above 2.5 may sound robotic"
        ]
    },
    "inference_timesteps": {
        "name": "Inference Timesteps",
        "type": "int",
        "range": [4, 30],
        "default": 10,
        "description": "Number of diffusion steps for generation",
        "tips": [
            "6-8 for quick previews",
            "10-15 for production quality",
            "20+ for critical/final output",
            "Each step adds ~0.5s on GPU, ~2s on CPU"
        ]
    },
    "enable_denoiser": {
        "name": "Prompt Speech Enhancement",
        "type": "bool",
        "default": False,
        "description": "Apply ZipEnhancer denoising to reference audio",
        "tips": [
            "Enable for noisy reference audio",
            "Disable to preserve voice character",
            "May slightly change voice timbre"
        ]
    },
    "enable_text_normalization": {
        "name": "Text Normalization",
        "type": "bool",
        "default": True,
        "description": "Preprocess text with wetext library",
        "tips": [
            "Handles numbers, abbreviations, symbols",
            "Disable for pre-formatted text",
            "Disable for special pronunciations"
        ]
    }
}


if __name__ == "__main__":
    # Demo
    config = VoxCPMConfig.balanced_preset()
    print("VoxCPM Configuration")
    print("=" * 50)
    print(config.to_json())
    print("\nValidation:", validate_config(config))
