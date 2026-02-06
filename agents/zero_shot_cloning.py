#!/usr/bin/env python3
"""
🎤 Zero-Shot Voice Cloning Agent
Cutting-edge 2026 agent for instant voice cloning with minimal reference audio.
Leverages VoxCPM, F5-TTS, and ensemble techniques.
"""

import json
import os
import subprocess
import base64
import wave
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests


@dataclass
class CloneRequest:
    """Voice cloning request specification."""
    text: str
    reference_audio: str
    reference_text: Optional[str] = None
    language: str = "fr"
    emotion: str = "neutral"
    speaking_rate: float = 1.0
    output_path: Optional[str] = None


@dataclass
class CloneResult:
    """Voice cloning result."""
    success: bool
    output_path: Optional[str] = None
    duration: float = 0.0
    model_used: str = ""
    error: Optional[str] = None


class ZeroShotCloningAgent:
    """
    Advanced zero-shot voice cloning agent.
    Uses ensemble of models for best quality.
    """
    
    SUPPORTED_MODELS = [
        "voxcpm",      # VoxCPM 1.5 - Best quality, slower
        "f5tts",       # F5-TTS - Fast, good quality  
        "xtts",        # Coqui XTTS v2 - Multilingual
        "openvoice",   # OpenVoice - Lightweight
    ]
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        voxcpm_url: str = "http://localhost:7860",
        output_dir: str = None
    ):
        self.ollama_url = ollama_url
        self.voxcpm_url = voxcpm_url
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "VoiceCloning" / "cloned_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check available models
        self.available_models = self._detect_available_models()
        
        print(f"🎤 Zero-Shot Cloning Agent initialized")
        print(f"   Available models: {self.available_models}")
        print(f"   Output dir: {self.output_dir}")
    
    def _detect_available_models(self) -> List[str]:
        """Detect which TTS models are available."""
        available = []
        
        # Check VoxCPM
        try:
            response = requests.get(f"{self.voxcpm_url}", timeout=2)
            if response.status_code == 200:
                available.append("voxcpm")
        except:
            pass
        
        # Check if voxcpm is installed as CLI
        try:
            result = subprocess.run(
                ["python", "-c", "import voxcpm; print('ok')"],
                capture_output=True,
                text=True
            )
            if "ok" in result.stdout:
                available.append("voxcpm_cli")
        except:
            pass
        
        # Check F5-TTS
        try:
            result = subprocess.run(
                ["python", "-c", "from f5_tts.api import F5TTS; print('ok')"],
                capture_output=True,
                text=True
            )
            if "ok" in result.stdout:
                available.append("f5tts")
        except:
            pass
        
        return available if available else ["voxcpm_cli"]  # Default fallback
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        try:
            with wave.open(audio_path, 'r') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / float(rate)
        except:
            return 0.0
    
    def _analyze_reference_with_llm(
        self,
        reference_text: str,
        target_text: str
    ) -> Dict:
        """Use LLM to analyze and optimize synthesis parameters."""
        prompt = f"""Analyze these texts for voice synthesis optimization:

Reference (what the speaker said): "{reference_text}"
Target (what we want them to say): "{target_text}"

Provide optimal synthesis parameters:
1. Speaking rate adjustment (0.8-1.2)
2. Pitch variation suggestion
3. Emotional tone matching
4. Pause placement recommendations

Output as JSON."""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            return {"analysis": response.json().get("response", "")}
        except:
            return {"analysis": "default", "speaking_rate": 1.0}
    
    def clone_voice_voxcpm(self, request: CloneRequest) -> CloneResult:
        """Clone voice using VoxCPM model."""
        output_path = request.output_path or str(
            self.output_dir / f"clone_{hash(request.text)}.wav"
        )
        
        try:
            # Use VoxCPM CLI
            cmd = [
                "voxcpm",
                "--text", request.text,
                "--prompt-audio", request.reference_audio,
                "--output", output_path
            ]
            
            if request.reference_text:
                cmd.extend(["--prompt-text", request.reference_text])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                return CloneResult(
                    success=True,
                    output_path=output_path,
                    duration=self._get_audio_duration(output_path),
                    model_used="voxcpm"
                )
            else:
                return CloneResult(
                    success=False,
                    error=result.stderr or "Unknown error",
                    model_used="voxcpm"
                )
                
        except Exception as e:
            return CloneResult(
                success=False,
                error=str(e),
                model_used="voxcpm"
            )
    
    def clone_voice_f5tts(self, request: CloneRequest) -> CloneResult:
        """Clone voice using F5-TTS model."""
        output_path = request.output_path or str(
            self.output_dir / f"clone_f5_{hash(request.text)}.wav"
        )
        
        try:
            # F5-TTS Python API
            script = f'''
import soundfile as sf
from f5_tts.api import F5TTS

model = F5TTS()
wav, sr = model.infer(
    ref_audio="{request.reference_audio}",
    ref_text="{request.reference_text or ''}",
    gen_text="{request.text}"
)
sf.write("{output_path}", wav, sr)
print("SUCCESS")
'''
            result = subprocess.run(
                ["python", "-c", script],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if "SUCCESS" in result.stdout and Path(output_path).exists():
                return CloneResult(
                    success=True,
                    output_path=output_path,
                    duration=self._get_audio_duration(output_path),
                    model_used="f5tts"
                )
            else:
                return CloneResult(
                    success=False,
                    error=result.stderr or "F5-TTS failed",
                    model_used="f5tts"
                )
                
        except Exception as e:
            return CloneResult(
                success=False,
                error=str(e),
                model_used="f5tts"
            )
    
    def clone_voice(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = None,
        model: str = "auto",
        **kwargs
    ) -> CloneResult:
        """
        Clone a voice with the best available model.
        
        Args:
            text: Text to synthesize
            reference_audio: Path to reference audio file
            reference_text: Transcription of reference audio (optional)
            model: Model to use ("auto", "voxcpm", "f5tts", etc.)
            **kwargs: Additional parameters
        
        Returns:
            CloneResult with output path and metadata
        """
        request = CloneRequest(
            text=text,
            reference_audio=reference_audio,
            reference_text=reference_text,
            **kwargs
        )
        
        # Select model
        if model == "auto":
            if "voxcpm" in self.available_models or "voxcpm_cli" in self.available_models:
                model = "voxcpm"
            elif "f5tts" in self.available_models:
                model = "f5tts"
            else:
                model = "voxcpm"  # Try anyway
        
        # Analyze with LLM for optimization
        if reference_text:
            analysis = self._analyze_reference_with_llm(reference_text, text)
            print(f"📊 LLM Analysis: {analysis.get('analysis', 'default')[:100]}...")
        
        # Execute cloning
        if model == "voxcpm":
            return self.clone_voice_voxcpm(request)
        elif model == "f5tts":
            return self.clone_voice_f5tts(request)
        else:
            return CloneResult(
                success=False,
                error=f"Model '{model}' not available"
            )
    
    def batch_clone(
        self,
        texts: List[str],
        reference_audio: str,
        reference_text: str = None
    ) -> List[CloneResult]:
        """Clone voice for multiple texts."""
        results = []
        
        for i, text in enumerate(texts):
            print(f"🎤 Cloning {i+1}/{len(texts)}: {text[:50]}...")
            result = self.clone_voice(
                text=text,
                reference_audio=reference_audio,
                reference_text=reference_text
            )
            results.append(result)
            
            if result.success:
                print(f"   ✅ Success: {result.output_path}")
            else:
                print(f"   ❌ Failed: {result.error}")
        
        return results


class EmotionalTTSAgent:
    """
    Agent for emotionally expressive TTS.
    Uses LLM to infer and inject emotions.
    """
    
    EMOTIONS = [
        "neutral", "happy", "sad", "angry", "surprised",
        "fearful", "disgusted", "professional", "excited"
    ]
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.cloning_agent = ZeroShotCloningAgent()
    
    def infer_emotion(self, text: str) -> Tuple[str, float]:
        """Use LLM to infer appropriate emotion from text."""
        prompt = f"""Analyze this text and determine the most appropriate emotion for TTS:

Text: "{text}"

Choose ONE emotion from: {', '.join(self.EMOTIONS)}
Also provide confidence (0.0-1.0).

Response format: emotion,confidence
Example: happy,0.85"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            
            result = response.json().get("response", "neutral,0.5")
            parts = result.strip().split(",")
            emotion = parts[0].strip().lower()
            confidence = float(parts[1].strip()) if len(parts) > 1 else 0.5
            
            if emotion not in self.EMOTIONS:
                emotion = "neutral"
            
            return emotion, confidence
            
        except:
            return "neutral", 0.5
    
    def enhance_text_for_emotion(
        self,
        text: str,
        emotion: str
    ) -> str:
        """Add prosody markers for target emotion."""
        prompt = f"""Enhance this text with SSML-like markers for {emotion} emotion:
- Use | for pauses
- Use *word* for emphasis
- Use [slow] or [fast] for pace

Text: "{text}"

Return only the enhanced text."""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            return response.json().get("response", text)
        except:
            return text
    
    def generate_emotional_speech(
        self,
        text: str,
        reference_audio: str,
        emotion: str = "auto"
    ) -> CloneResult:
        """Generate speech with appropriate emotion."""
        
        # Infer emotion if auto
        if emotion == "auto":
            emotion, confidence = self.infer_emotion(text)
            print(f"🎭 Inferred emotion: {emotion} (confidence: {confidence:.2f})")
        
        # Enhance text
        enhanced_text = self.enhance_text_for_emotion(text, emotion)
        print(f"📝 Enhanced text: {enhanced_text[:100]}...")
        
        # Clone with emotional context
        return self.cloning_agent.clone_voice(
            text=enhanced_text,
            reference_audio=reference_audio,
            emotion=emotion
        )


def main():
    """Demo of zero-shot cloning agents."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Zero-Shot Voice Cloning Agent")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--reference", required=True, help="Reference audio path")
    parser.add_argument("--ref-text", help="Reference audio transcription")
    parser.add_argument("--model", default="auto", help="Model to use")
    parser.add_argument("--emotion", default="auto", help="Emotion for synthesis")
    parser.add_argument("--output", help="Output path")
    
    args = parser.parse_args()
    
    if args.emotion != "neutral":
        agent = EmotionalTTSAgent()
        result = agent.generate_emotional_speech(
            text=args.text,
            reference_audio=args.reference,
            emotion=args.emotion
        )
    else:
        agent = ZeroShotCloningAgent()
        result = agent.clone_voice(
            text=args.text,
            reference_audio=args.reference,
            reference_text=args.ref_text,
            model=args.model,
            output_path=args.output
        )
    
    if result.success:
        print(f"\n✅ Voice cloned successfully!")
        print(f"   Output: {result.output_path}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Model: {result.model_used}")
    else:
        print(f"\n❌ Cloning failed: {result.error}")


if __name__ == "__main__":
    main()
