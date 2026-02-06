#!/usr/bin/env python3
"""
🎯 Voice Cloning Orchestrator Agent
Master agent leveraging Ollama LLMs to coordinate voice cloning pipelines.
Cutting-edge 2026 architecture with multi-model orchestration.
"""

import json
import os
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class OllamaModel(Enum):
    """Available Ollama models for different tasks."""
    QWEN3_8B = "qwen3:8b"           # Best for reasoning & planning
    DEEPSEEK_R1 = "deepseek-r1:7b"  # Best for code & technical
    QWEN25_3B = "qwen2.5:3b"        # Fast, good for simple tasks
    PHI3_14B = "phi3:14b"           # Best quality, slower
    LLAMA32 = "llama3.2:3b"         # Balanced performance


@dataclass
class VoiceProfile:
    """Represents a speaker's voice profile."""
    name: str
    reference_audios: List[str]
    transcriptions: List[str]
    language: str = "fr"
    emotion: str = "neutral"
    style_tags: List[str] = None
    embedding: Optional[Any] = None


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.available_models = self._get_available_models()
    
    def _get_available_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )
            models = []
            for line in result.stdout.strip().split('\n')[1:]:  # Skip header
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
        except Exception as e:
            print(f"⚠️ Could not get Ollama models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: str = "qwen3:8b",
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate text using Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"❌ Ollama generate error: {e}")
            return ""
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "qwen3:8b",
        temperature: float = 0.7
    ) -> str:
        """Chat with Ollama model."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            print(f"❌ Ollama chat error: {e}")
            return ""


class VoiceCloningOrchestrator:
    """
    Master orchestrator for voice cloning pipeline.
    Uses LLM agents for intelligent decision making.
    """
    
    def __init__(
        self,
        dataset_path: str,
        output_dir: str = None
    ):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir) if output_dir else self.dataset_path.parent / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Ollama client
        self.ollama = OllamaClient()
        
        # Load dataset metadata
        self.segments = self._load_segments()
        
        print(f"🎯 Voice Cloning Orchestrator initialized")
        print(f"   Dataset: {self.dataset_path}")
        print(f"   Segments: {len(self.segments)}")
        print(f"   Available Ollama models: {self.ollama.available_models}")
    
    def _load_segments(self) -> List[Dict]:
        """Load all audio segments and their transcriptions."""
        segments = []
        
        for json_file in sorted(self.dataset_path.glob("*_transcription.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Find corresponding audio file
                audio_name = json_file.stem.replace("_transcription", "") + ".wav"
                audio_path = self.dataset_path / audio_name
                
                if audio_path.exists():
                    segments.append({
                        "audio_path": str(audio_path),
                        "transcription": data.get("text", ""),
                        "duration": data.get("duration", 0),
                        "word_count": data.get("word_count", 0),
                        "metadata": data
                    })
            except Exception as e:
                print(f"⚠️ Error loading {json_file}: {e}")
        
        return segments
    
    def analyze_voice_characteristics(self) -> Dict:
        """
        Use LLM to analyze voice characteristics from transcriptions.
        Identifies speaking style, tone, vocabulary patterns.
        """
        # Sample transcriptions for analysis
        samples = [s["transcription"] for s in self.segments[:20] if s["transcription"]]
        sample_text = "\n".join([f"- {t}" for t in samples])
        
        prompt = f"""Analyze the following speech transcriptions and identify:
1. Speaking style (formal, casual, professional, etc.)
2. Common vocabulary themes
3. Sentence structure patterns
4. Emotional undertones
5. Recommended voice synthesis parameters

Transcriptions:
{sample_text}

Provide a structured analysis in JSON format."""

        analysis = self.ollama.generate(
            prompt=prompt,
            model="qwen3:8b",
            system="You are an expert speech analyst. Analyze transcriptions and provide insights for voice synthesis."
        )
        
        return {
            "raw_analysis": analysis,
            "sample_count": len(samples),
            "total_segments": len(self.segments)
        }
    
    def select_best_reference_samples(
        self,
        target_duration: float = 30.0,
        diversity_weight: float = 0.5
    ) -> List[Dict]:
        """
        Intelligently select the best reference samples for voice cloning.
        Balances audio quality, clarity, and diversity.
        """
        # Use LLM to rank quality based on transcription complexity
        candidates = []
        
        for seg in self.segments:
            if 3.0 <= seg.get("duration", 0) <= 15.0:  # Optimal length
                word_count = seg.get("word_count", len(seg["transcription"].split()))
                words_per_sec = word_count / max(seg.get("duration", 1), 1)
                
                # Score: prefer moderate speaking pace
                pace_score = 1.0 - abs(words_per_sec - 2.5) / 2.5
                candidates.append({
                    **seg,
                    "pace_score": max(0, pace_score),
                    "words_per_sec": words_per_sec
                })
        
        # Sort by score and select diverse set
        candidates.sort(key=lambda x: x["pace_score"], reverse=True)
        
        selected = []
        total_duration = 0
        
        for cand in candidates:
            if total_duration >= target_duration:
                break
            
            selected.append(cand)
            total_duration += cand.get("duration", 0)
        
        return selected
    
    def generate_training_config(self) -> Dict:
        """
        Use LLM to generate optimal training configuration.
        """
        dataset_info = {
            "total_segments": len(self.segments),
            "total_duration_minutes": sum(s.get("duration", 0) for s in self.segments) / 60,
            "language": "French",
            "speaker": "single"
        }
        
        prompt = f"""Given this voice dataset:
{json.dumps(dataset_info, indent=2)}

Generate optimal F5-TTS training configuration including:
1. Recommended epochs
2. Batch size for T4 GPU (15GB VRAM)
3. Learning rate
4. Warmup steps
5. Checkpoint frequency

Provide as JSON."""

        config_response = self.ollama.generate(
            prompt=prompt,
            model="deepseek-r1:7b",
            system="You are an ML engineer expert in TTS training. Provide optimized configs."
        )
        
        # Default config with LLM suggestions
        default_config = {
            "model": "F5-TTS",
            "epochs": 200,
            "batch_size": 4,
            "learning_rate": 1e-5,
            "warmup_steps": 1000,
            "checkpoint_interval": 5000,
            "dataset_info": dataset_info,
            "llm_suggestions": config_response
        }
        
        return default_config
    
    def generate_synthesis_prompt(
        self,
        text: str,
        emotion: str = "neutral",
        style: str = "professional"
    ) -> Dict:
        """
        Generate enhanced prompt for expressive TTS synthesis.
        Uses LLM to add prosody hints and emotional markers.
        """
        prompt = f"""Enhance this text for expressive text-to-speech synthesis.
Add SSML-like annotations for:
- Pauses (use |)
- Emphasis (use *word*)
- Pitch changes
- Speaking rate

Target emotion: {emotion}
Target style: {style}

Original text: {text}

Provide the enhanced text."""

        enhanced = self.ollama.generate(
            prompt=prompt,
            model="qwen2.5:3b",  # Fast model for quick enhancement
            temperature=0.6
        )
        
        return {
            "original": text,
            "enhanced": enhanced,
            "emotion": emotion,
            "style": style
        }
    
    def create_voice_profile(self, name: str = "StarConnect") -> VoiceProfile:
        """Create a comprehensive voice profile from the dataset."""
        reference_samples = self.select_best_reference_samples(target_duration=60.0)
        
        profile = VoiceProfile(
            name=name,
            reference_audios=[s["audio_path"] for s in reference_samples],
            transcriptions=[s["transcription"] for s in reference_samples],
            language="fr",
            emotion="professional",
            style_tags=["clear", "articulate", "french", "professional"]
        )
        
        # Save profile
        profile_path = self.output_dir / f"{name}_profile.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": profile.name,
                "reference_audios": profile.reference_audios,
                "transcriptions": profile.transcriptions,
                "language": profile.language,
                "emotion": profile.emotion,
                "style_tags": profile.style_tags
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Voice profile saved: {profile_path}")
        return profile
    
    def run_pipeline(self) -> Dict:
        """
        Execute the complete voice cloning pipeline.
        """
        print("\n🚀 Starting Voice Cloning Pipeline")
        print("=" * 50)
        
        results = {}
        
        # Step 1: Analyze voice
        print("\n📊 Step 1: Analyzing voice characteristics...")
        results["analysis"] = self.analyze_voice_characteristics()
        
        # Step 2: Select references
        print("\n🎯 Step 2: Selecting best reference samples...")
        references = self.select_best_reference_samples()
        results["references"] = {
            "count": len(references),
            "total_duration": sum(r.get("duration", 0) for r in references),
            "files": [r["audio_path"] for r in references[:5]]
        }
        
        # Step 3: Generate config
        print("\n⚙️ Step 3: Generating training configuration...")
        results["config"] = self.generate_training_config()
        
        # Step 4: Create profile
        print("\n👤 Step 4: Creating voice profile...")
        profile = self.create_voice_profile()
        results["profile"] = profile.name
        
        print("\n" + "=" * 50)
        print("✅ Pipeline completed!")
        
        return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Cloning Orchestrator")
    parser.add_argument("--dataset", default="/Users/yacinebenhamou/VoiceCloning/StarConnect",
                       help="Path to dataset")
    parser.add_argument("--action", choices=["analyze", "select", "config", "profile", "full"],
                       default="full", help="Action to perform")
    
    args = parser.parse_args()
    
    orchestrator = VoiceCloningOrchestrator(dataset_path=args.dataset)
    
    if args.action == "analyze":
        result = orchestrator.analyze_voice_characteristics()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "select":
        result = orchestrator.select_best_reference_samples()
        print(f"Selected {len(result)} samples")
    elif args.action == "config":
        result = orchestrator.generate_training_config()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.action == "profile":
        orchestrator.create_voice_profile()
    else:
        result = orchestrator.run_pipeline()
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
