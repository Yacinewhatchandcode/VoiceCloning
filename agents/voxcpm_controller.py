#!/usr/bin/env python3
"""
🤖 VoxCPM Controller Agent
Multi-agent backend for controlling VoxCPM with intelligence.
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voxcpm_config import VoxCPMConfig, validate_config, PARAMETER_DOCS


class AgentRole(Enum):
    """Agent roles in the multi-agent system."""
    CONTROLLER = "controller"       # Main orchestration
    OPTIMIZER = "optimizer"         # Parameter optimization
    QUALITY = "quality"             # Quality assessment
    DATASET = "dataset"             # Dataset management
    GENERATOR = "generator"         # Audio generation


@dataclass
class AgentMessage:
    """Message passed between agents."""
    sender: AgentRole
    receiver: AgentRole
    action: str
    payload: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class OllamaInterface:
    """Interface to Ollama LLM for intelligent decisions."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "qwen3:8b"  # Best reasoning model available
    
    def query(self, prompt: str, system: str = None) -> str:
        """Query Ollama LLM."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            }
            if system:
                payload["system"] = system
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            return response.json().get("response", "")
        except Exception as e:
            return f"LLM Error: {e}"


class VoxCPMInterface:
    """Direct interface to VoxCPM model/API."""
    
    def __init__(self, gradio_url: str = "http://localhost:7860"):
        self.gradio_url = gradio_url
        self.api_url = f"{gradio_url}/api/predict"
    
    def is_running(self) -> bool:
        """Check if VoxCPM web UI is running."""
        try:
            response = requests.get(self.gradio_url, timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_via_cli(
        self,
        config: VoxCPMConfig
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate audio using VoxCPM CLI.
        Returns: (success, message, output_path)
        """
        output_path = config.output_path or f"/tmp/voxcpm_output_{int(time.time())}.wav"
        
        cmd = [
            "voxcpm",
            "--text", config.target_text,
            "--prompt-audio", config.prompt_audio_path,
            "--output", output_path,
            "--cfg-value", str(config.cfg_value),
            "--inference-timesteps", str(config.inference_timesteps)
        ]
        
        if config.prompt_text:
            cmd.extend(["--prompt-text", config.prompt_text])
        
        if not config.enable_denoiser:
            cmd.append("--no-denoiser")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "CUDA_VISIBLE_DEVICES": ""}
            )
            
            if Path(output_path).exists():
                return True, "Generation successful", output_path
            else:
                return False, result.stderr or "Unknown error", None
                
        except subprocess.TimeoutExpired:
            return False, "Generation timed out", None
        except Exception as e:
            return False, str(e), None


class ParameterOptimizerAgent:
    """Agent that optimizes VoxCPM parameters based on requirements."""
    
    def __init__(self, llm: OllamaInterface):
        self.llm = llm
        self.role = AgentRole.OPTIMIZER
    
    def optimize(
        self,
        config: VoxCPMConfig,
        requirements: Dict[str, Any]
    ) -> VoxCPMConfig:
        """
        Optimize configuration based on requirements.
        
        Requirements can include:
        - priority: "speed" | "quality" | "balanced"
        - voice_similarity: "high" | "medium" | "low"
        - naturalness: "high" | "medium" | "low"
        """
        priority = requirements.get("priority", "balanced")
        voice_sim = requirements.get("voice_similarity", "high")
        
        # Base optimization
        if priority == "speed":
            config.inference_timesteps = 6
            config.enable_denoiser = False
        elif priority == "quality":
            config.inference_timesteps = 20
            config.enable_denoiser = True
        else:
            config.inference_timesteps = 10
        
        # Voice similarity
        if voice_sim == "high":
            config.cfg_value = 2.4
        elif voice_sim == "low":
            config.cfg_value = 1.5
        else:
            config.cfg_value = 2.0
        
        # LLM refinement
        prompt = f"""Given these voice cloning requirements:
{json.dumps(requirements)}

Current config:
- CFG Value: {config.cfg_value}
- Timesteps: {config.inference_timesteps}
- Denoiser: {config.enable_denoiser}

Suggest any adjustments (respond with JSON):
{{"cfg_value": X, "inference_timesteps": Y, "reasoning": "..."}}"""

        response = self.llm.query(prompt)
        
        try:
            # Parse LLM suggestions
            import re
            match = re.search(r'\{[^}]+\}', response)
            if match:
                suggestions = json.loads(match.group())
                if "cfg_value" in suggestions:
                    config.cfg_value = float(suggestions["cfg_value"])
                if "inference_timesteps" in suggestions:
                    config.inference_timesteps = int(suggestions["inference_timesteps"])
        except:
            pass  # Use base optimization
        
        return config
    
    def explain_parameters(self, config: VoxCPMConfig) -> str:
        """Get LLM explanation of current parameters."""
        prompt = f"""Explain these VoxCPM voice cloning settings in simple terms:

- CFG Value: {config.cfg_value} (range 1-3)
- Inference Timesteps: {config.inference_timesteps} (range 4-30)
- Denoiser: {config.enable_denoiser}
- Text Normalization: {config.enable_text_normalization}

Explain what each does and if this is a good configuration."""

        return self.llm.query(prompt)


class DatasetManagerAgent:
    """Agent that manages the StarConnect dataset."""
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.role = AgentRole.DATASET
        self.segments = self._load_segments()
    
    def _load_segments(self) -> List[Dict]:
        """Load all dataset segments."""
        segments = []
        
        for audio_file in sorted(self.dataset_path.glob("segment_*.wav")):
            json_file = audio_file.with_suffix("").with_suffix("_transcription.json")
            
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
            
            segments.append(segment)
        
        return segments
    
    def get_segment(self, segment_id: str) -> Optional[Dict]:
        """Get segment by ID."""
        for seg in self.segments:
            if seg["id"] == segment_id:
                return seg
        return None
    
    def get_best_reference(self, target_duration: float = 5.0) -> Optional[Dict]:
        """Get best reference segment close to target duration."""
        valid = [s for s in self.segments if 3 <= s.get("duration", 0) <= 10]
        if not valid:
            return self.segments[0] if self.segments else None
        
        # Sort by closeness to target duration
        valid.sort(key=lambda x: abs(x["duration"] - target_duration))
        return valid[0]
    
    def search_by_text(self, query: str) -> List[Dict]:
        """Search segments by transcription text."""
        query_lower = query.lower()
        return [s for s in self.segments if query_lower in s.get("transcription", "").lower()]
    
    def get_stats(self) -> Dict:
        """Get dataset statistics."""
        total_duration = sum(s.get("duration", 0) for s in self.segments)
        return {
            "total_segments": len(self.segments),
            "total_duration_seconds": total_duration,
            "total_duration_minutes": total_duration / 60,
            "with_transcription": sum(1 for s in self.segments if s.get("transcription")),
            "average_duration": total_duration / len(self.segments) if self.segments else 0
        }


class QualityAssessmentAgent:
    """Agent that assesses voice cloning quality."""
    
    def __init__(self, llm: OllamaInterface):
        self.llm = llm
        self.role = AgentRole.QUALITY
    
    def assess_audio_file(self, audio_path: str) -> Dict:
        """Assess audio file quality using signal analysis."""
        import wave
        import struct
        import math
        
        try:
            with wave.open(audio_path, 'r') as wav:
                n_frames = wav.getnframes()
                rate = wav.getframerate()
                frames = wav.readframes(n_frames)
                
                samples = list(struct.unpack(f"<{n_frames}h", frames))
                samples = [s / 32768.0 for s in samples]
                
                # RMS
                rms = math.sqrt(sum(s*s for s in samples) / len(samples))
                
                # Peak
                peak = max(abs(s) for s in samples)
                
                # Clipping
                clipping = sum(1 for s in samples if abs(s) > 0.99) / len(samples)
                
                return {
                    "duration_seconds": n_frames / rate,
                    "sample_rate": rate,
                    "rms_level": rms,
                    "peak_level": peak,
                    "clipping_ratio": clipping,
                    "quality_score": self._calculate_score(rms, peak, clipping)
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_score(self, rms: float, peak: float, clipping: float) -> float:
        """Calculate quality score 0-100."""
        score = 50
        
        # RMS should be moderate (not too quiet or loud)
        if 0.05 < rms < 0.3:
            score += 20
        elif 0.02 < rms < 0.5:
            score += 10
        
        # No clipping
        if clipping < 0.001:
            score += 20
        elif clipping < 0.01:
            score += 10
        
        # Good dynamic range
        if peak > 0.5 and rms / peak < 0.5:
            score += 10
        
        return min(100, max(0, score))


class VoxCPMControllerAgent:
    """
    Master controller agent that orchestrates the multi-agent system.
    """
    
    def __init__(
        self,
        dataset_path: str = "/Users/yacinebenhamou/VoiceCloning/StarConnect",
        ollama_url: str = "http://localhost:11434",
        voxcpm_url: str = "http://localhost:7860"
    ):
        # Initialize components
        self.llm = OllamaInterface(ollama_url)
        self.voxcpm = VoxCPMInterface(voxcpm_url)
        
        # Initialize agents
        self.optimizer = ParameterOptimizerAgent(self.llm)
        self.dataset = DatasetManagerAgent(dataset_path)
        self.quality = QualityAssessmentAgent(self.llm)
        
        # State
        self.current_config = VoxCPMConfig.balanced_preset()
        self.history = []
        
        print(f"🤖 VoxCPM Controller initialized")
        print(f"   Dataset: {len(self.dataset.segments)} segments")
        print(f"   VoxCPM running: {self.voxcpm.is_running()}")
    
    def process_request(self, request: Dict) -> Dict:
        """
        Process a voice cloning request.
        
        Request format:
        {
            "text": "Text to synthesize",
            "reference_segment": "segment_001" | null (auto-select),
            "priority": "speed" | "quality" | "balanced",
            "voice_similarity": "high" | "medium" | "low"
        }
        """
        # Get reference audio
        if request.get("reference_segment"):
            segment = self.dataset.get_segment(request["reference_segment"])
        else:
            segment = self.dataset.get_best_reference()
        
        if not segment:
            return {"success": False, "error": "No reference segment found"}
        
        # Configure
        config = VoxCPMConfig.balanced_preset()
        config.prompt_audio_path = segment["audio_path"]
        config.prompt_text = segment.get("transcription", "")
        config.target_text = request.get("text", "")
        
        # Optimize
        requirements = {
            "priority": request.get("priority", "balanced"),
            "voice_similarity": request.get("voice_similarity", "high")
        }
        config = self.optimizer.optimize(config, requirements)
        
        # Validate
        warnings = validate_config(config)
        
        # Generate
        success, message, output_path = self.voxcpm.generate_via_cli(config)
        
        result = {
            "success": success,
            "message": message,
            "output_path": output_path,
            "config_used": config.to_dict(),
            "warnings": warnings,
            "reference_segment": segment["id"]
        }
        
        # Assess quality if successful
        if success and output_path:
            result["quality"] = self.quality.assess_audio_file(output_path)
        
        # Save to history
        self.history.append({
            "timestamp": time.time(),
            "request": request,
            "result": result
        })
        
        return result
    
    def explain_config(self) -> str:
        """Get explanation of current configuration."""
        return self.optimizer.explain_parameters(self.current_config)
    
    def get_status(self) -> Dict:
        """Get system status."""
        return {
            "voxcpm_running": self.voxcpm.is_running(),
            "dataset_stats": self.dataset.get_stats(),
            "current_config": self.current_config.to_dict(),
            "history_count": len(self.history)
        }
    
    def smart_clone(
        self,
        text: str,
        style: str = "natural"
    ) -> Dict:
        """
        Intelligent voice cloning with automatic optimization.
        Uses LLM to determine best parameters.
        """
        # Ask LLM what settings to use
        prompt = f"""For voice cloning this text: "{text}"
        
With style: {style}

Suggest optimal VoxCPM settings as JSON:
{{
    "cfg_value": 1.0-3.0,
    "inference_timesteps": 4-30,
    "enable_denoiser": true/false,
    "reasoning": "..."
}}"""

        response = self.llm.query(prompt)
        
        # Parse and apply
        config = VoxCPMConfig.balanced_preset()
        config.target_text = text
        
        try:
            import re
            match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if match:
                settings = json.loads(match.group())
                if "cfg_value" in settings:
                    config.cfg_value = float(settings["cfg_value"])
                if "inference_timesteps" in settings:
                    config.inference_timesteps = int(settings["inference_timesteps"])
                if "enable_denoiser" in settings:
                    config.enable_denoiser = bool(settings["enable_denoiser"])
        except:
            pass
        
        # Get best reference
        segment = self.dataset.get_best_reference()
        config.prompt_audio_path = segment["audio_path"]
        config.prompt_text = segment.get("transcription", "")
        
        # Generate
        success, message, output_path = self.voxcpm.generate_via_cli(config)
        
        return {
            "success": success,
            "output_path": output_path,
            "message": message,
            "llm_reasoning": response,
            "config": config.to_dict()
        }


if __name__ == "__main__":
    # Demo
    controller = VoxCPMControllerAgent()
    print("\n" + "="*50)
    print("SYSTEM STATUS:")
    print(json.dumps(controller.get_status(), indent=2))
