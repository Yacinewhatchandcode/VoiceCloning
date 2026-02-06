#!/usr/bin/env python3
"""
🧠 Multi-Model Ensemble Agent
Cutting-edge 2026 agent that coordinates multiple TTS models for best results.
Uses LLM-driven model selection and output fusion.
"""

import json
import os
import subprocess
import tempfile
import wave
import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


@dataclass
class ModelCandidate:
    """A TTS model candidate for ensemble."""
    name: str
    output_path: Optional[str] = None
    score: float = 0.0
    latency_ms: float = 0.0
    success: bool = False
    error: Optional[str] = None


@dataclass
class EnsembleResult:
    """Result from ensemble synthesis."""
    best_output: str
    best_model: str
    best_score: float
    all_candidates: List[ModelCandidate]
    fusion_method: str
    llm_reasoning: str


class MultiModelEnsembleAgent:
    """
    Coordinates multiple TTS models for optimal voice cloning.
    Uses LLM to select best model and optionally fuse outputs.
    """
    
    # Model registry with capabilities
    MODEL_REGISTRY = {
        "voxcpm": {
            "name": "VoxCPM 1.5",
            "languages": ["en", "zh", "fr"],
            "quality_tier": "premium",
            "speed": "slow",
            "strengths": ["expressiveness", "emotion", "naturalness"],
            "gpu_required": False
        },
        "f5tts": {
            "name": "F5-TTS",
            "languages": ["en", "zh", "fr", "de", "es", "ja", "ko"],
            "quality_tier": "high",
            "speed": "medium",
            "strengths": ["multilingual", "speed", "consistency"],
            "gpu_required": True
        },
        "xtts": {
            "name": "Coqui XTTS v2",
            "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu"],
            "quality_tier": "high",
            "speed": "medium",
            "strengths": ["multilingual", "cross-lingual", "accent-preservation"],
            "gpu_required": True
        },
        "openvoice": {
            "name": "OpenVoice",
            "languages": ["en", "zh"],
            "quality_tier": "good",
            "speed": "fast",
            "strengths": ["speed", "lightweight", "real-time"],
            "gpu_required": False
        }
    }
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        output_dir: str = None,
        max_parallel: int = 2
    ):
        self.ollama_url = ollama_url
        self.output_dir = Path(output_dir) if output_dir else Path.home() / "VoiceCloning" / "ensemble_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_parallel = max_parallel
        
        # Detect available models
        self.available_models = self._detect_models()
        
        print(f"🧠 Multi-Model Ensemble Agent initialized")
        print(f"   Available models: {list(self.available_models.keys())}")
    
    def _detect_models(self) -> Dict[str, bool]:
        """Detect which models are available."""
        available = {}
        
        for model_id in self.MODEL_REGISTRY.keys():
            try:
                if model_id == "voxcpm":
                    result = subprocess.run(
                        ["python", "-c", "import voxcpm; print('ok')"],
                        capture_output=True, text=True, timeout=10
                    )
                    available[model_id] = "ok" in result.stdout
                elif model_id == "f5tts":
                    result = subprocess.run(
                        ["python", "-c", "from f5_tts.api import F5TTS; print('ok')"],
                        capture_output=True, text=True, timeout=10
                    )
                    available[model_id] = "ok" in result.stdout
                elif model_id == "xtts":
                    result = subprocess.run(
                        ["python", "-c", "from TTS.api import TTS; print('ok')"],
                        capture_output=True, text=True, timeout=10
                    )
                    available[model_id] = "ok" in result.stdout
                else:
                    available[model_id] = False
            except:
                available[model_id] = False
        
        return {k: v for k, v in available.items() if v}
    
    def _select_models_with_llm(
        self,
        text: str,
        language: str,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """Use LLM to select best models for the task."""
        model_info = json.dumps({
            k: {
                "name": v["name"],
                "languages": v["languages"],
                "quality": v["quality_tier"],
                "speed": v["speed"],
                "strengths": v["strengths"]
            }
            for k, v in self.MODEL_REGISTRY.items()
            if k in self.available_models
        }, indent=2)
        
        prompt = f"""Select the best TTS models for this task:

TEXT TO SYNTHESIZE: "{text[:100]}..."
LANGUAGE: {language}
REQUIREMENTS: {json.dumps(requirements)}

AVAILABLE MODELS:
{model_info}

Consider:
1. Language support
2. Quality requirements
3. Speed needs
4. Specific strengths needed

Return a JSON array of model IDs to use, ranked by preference.
Example: ["voxcpm", "f5tts"]"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            
            result = response.json().get("response", "")
            
            # Parse model list from response
            import re
            match = re.search(r'\[([^\]]+)\]', result)
            if match:
                models = [m.strip().strip('"\'') for m in match.group(1).split(',')]
                return [m for m in models if m in self.available_models]
            
        except Exception as e:
            print(f"⚠️ LLM selection failed: {e}")
        
        # Fallback: return all available
        return list(self.available_models.keys())
    
    def _run_model_voxcpm(
        self,
        text: str,
        reference_audio: str,
        reference_text: str,
        output_path: str
    ) -> ModelCandidate:
        """Run VoxCPM model."""
        import time
        start = time.time()
        
        try:
            cmd = [
                "voxcpm",
                "--text", text,
                "--prompt-audio", reference_audio,
                "--output", output_path
            ]
            
            if reference_text:
                cmd.extend(["--prompt-text", reference_text])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and Path(output_path).exists():
                return ModelCandidate(
                    name="voxcpm",
                    output_path=output_path,
                    success=True,
                    latency_ms=(time.time() - start) * 1000
                )
            else:
                return ModelCandidate(
                    name="voxcpm",
                    success=False,
                    error=result.stderr or "Unknown error",
                    latency_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ModelCandidate(
                name="voxcpm",
                success=False,
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            )
    
    def _run_model_f5tts(
        self,
        text: str,
        reference_audio: str,
        reference_text: str,
        output_path: str
    ) -> ModelCandidate:
        """Run F5-TTS model."""
        import time
        start = time.time()
        
        try:
            script = f'''
import soundfile as sf
from f5_tts.api import F5TTS

model = F5TTS()
wav, sr = model.infer(
    ref_audio="{reference_audio}",
    ref_text="""{reference_text or ''}""",
    gen_text="""{text}"""
)
sf.write("{output_path}", wav, sr)
print("SUCCESS")
'''
            result = subprocess.run(
                ["python", "-c", script],
                capture_output=True, text=True, timeout=300
            )
            
            if "SUCCESS" in result.stdout and Path(output_path).exists():
                return ModelCandidate(
                    name="f5tts",
                    output_path=output_path,
                    success=True,
                    latency_ms=(time.time() - start) * 1000
                )
            else:
                return ModelCandidate(
                    name="f5tts",
                    success=False,
                    error=result.stderr or "F5-TTS failed",
                    latency_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ModelCandidate(
                name="f5tts",
                success=False,
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            )
    
    def _score_candidate(self, candidate: ModelCandidate) -> float:
        """Score a candidate output."""
        if not candidate.success or not candidate.output_path:
            return 0.0
        
        try:
            # Import quality agent
            from agents.quality_agent import AudioQualityAgent
            qa = AudioQualityAgent(self.ollama_url)
            metrics = qa.assess_audio(candidate.output_path)
            return metrics.overall_score
        except:
            # Fallback: simple file-based scoring
            if Path(candidate.output_path).exists():
                size = Path(candidate.output_path).stat().st_size
                if size > 1000:  # At least 1KB
                    return 50.0  # Basic pass
            return 0.0
    
    def _select_best_with_llm(
        self,
        candidates: List[ModelCandidate]
    ) -> Tuple[ModelCandidate, str]:
        """Use LLM to select best candidate."""
        successful = [c for c in candidates if c.success]
        
        if not successful:
            return candidates[0] if candidates else None, "No successful candidates"
        
        if len(successful) == 1:
            return successful[0], "Only one successful candidate"
        
        # Build comparison prompt
        comparison = "\n".join([
            f"- {c.name}: Score={c.score:.1f}, Latency={c.latency_ms:.0f}ms"
            for c in successful
        ])
        
        prompt = f"""Select the best TTS output based on these results:

{comparison}

Consider:
1. Quality score (higher is better)
2. Model reputation for naturalness
3. Latency (for real-time use cases)

Return the model name of the best choice and explain why."""

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
            
            reasoning = response.json().get("response", "")
            
            # Find mentioned model
            for c in successful:
                if c.name.lower() in reasoning.lower():
                    return c, reasoning
            
            # Default to highest score
            best = max(successful, key=lambda x: x.score)
            return best, reasoning
            
        except:
            # Fallback to highest score
            best = max(successful, key=lambda x: x.score)
            return best, "Selected by highest score (LLM unavailable)"
    
    def synthesize_ensemble(
        self,
        text: str,
        reference_audio: str,
        reference_text: str = None,
        language: str = "fr",
        requirements: Dict[str, Any] = None
    ) -> EnsembleResult:
        """
        Synthesize using ensemble of models and select best.
        
        Args:
            text: Text to synthesize
            reference_audio: Path to reference voice audio
            reference_text: Transcription of reference audio
            language: Target language
            requirements: Additional requirements (quality, speed, etc.)
        
        Returns:
            EnsembleResult with best output and analysis
        """
        requirements = requirements or {"quality": "high"}
        
        # Select models
        models_to_use = self._select_models_with_llm(text, language, requirements)
        print(f"🎯 Selected models: {models_to_use}")
        
        # Generate candidates
        candidates = []
        
        for model_id in models_to_use:
            output_path = str(self.output_dir / f"candidate_{model_id}_{hash(text)}.wav")
            
            print(f"🔄 Running {model_id}...")
            
            if model_id == "voxcpm":
                candidate = self._run_model_voxcpm(
                    text, reference_audio, reference_text, output_path
                )
            elif model_id == "f5tts":
                candidate = self._run_model_f5tts(
                    text, reference_audio, reference_text, output_path
                )
            else:
                candidate = ModelCandidate(
                    name=model_id,
                    success=False,
                    error=f"Model {model_id} not implemented"
                )
            
            # Score candidate
            if candidate.success:
                candidate.score = self._score_candidate(candidate)
                print(f"   ✅ {model_id}: Score={candidate.score:.1f}, Latency={candidate.latency_ms:.0f}ms")
            else:
                print(f"   ❌ {model_id}: {candidate.error}")
            
            candidates.append(candidate)
        
        # Select best
        best, reasoning = self._select_best_with_llm(candidates)
        
        if best and best.success:
            return EnsembleResult(
                best_output=best.output_path,
                best_model=best.name,
                best_score=best.score,
                all_candidates=candidates,
                fusion_method="selection",
                llm_reasoning=reasoning
            )
        else:
            return EnsembleResult(
                best_output=None,
                best_model="none",
                best_score=0.0,
                all_candidates=candidates,
                fusion_method="failed",
                llm_reasoning="All models failed"
            )


class AdaptiveModelAgent:
    """
    Agent that learns from user feedback to improve model selection.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        history_path: str = None
    ):
        self.ollama_url = ollama_url
        self.history_path = Path(history_path) if history_path else Path.home() / "VoiceCloning" / "model_history.json"
        self.history = self._load_history()
        self.ensemble = MultiModelEnsembleAgent(ollama_url)
    
    def _load_history(self) -> List[Dict]:
        """Load selection history."""
        if self.history_path.exists():
            with open(self.history_path, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self):
        """Save selection history."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, 'w') as f:
            json.dump(self.history[-100:], f, indent=2)  # Keep last 100
    
    def record_feedback(
        self,
        model: str,
        language: str,
        text_length: int,
        user_rating: int  # 1-5
    ):
        """Record user feedback for future learning."""
        self.history.append({
            "model": model,
            "language": language,
            "text_length": text_length,
            "rating": user_rating
        })
        self._save_history()
    
    def get_recommended_model(
        self,
        language: str,
        text_length: int
    ) -> str:
        """Get recommended model based on history."""
        # Filter relevant history
        relevant = [h for h in self.history 
                   if h["language"] == language]
        
        if not relevant:
            return "voxcpm"  # Default
        
        # Calculate average rating per model
        ratings = {}
        for h in relevant:
            model = h["model"]
            if model not in ratings:
                ratings[model] = []
            ratings[model].append(h["rating"])
        
        # Get best rated
        avg_ratings = {m: sum(r)/len(r) for m, r in ratings.items()}
        best = max(avg_ratings.items(), key=lambda x: x[1])
        
        return best[0]


def main():
    """Demo of ensemble agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Model Ensemble Agent")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--reference", required=True, help="Reference audio")
    parser.add_argument("--ref-text", help="Reference transcription")
    parser.add_argument("--language", default="fr", help="Language")
    
    args = parser.parse_args()
    
    agent = MultiModelEnsembleAgent()
    
    result = agent.synthesize_ensemble(
        text=args.text,
        reference_audio=args.reference,
        reference_text=args.ref_text,
        language=args.language
    )
    
    print(f"\n{'='*50}")
    print(f"🧠 ENSEMBLE SYNTHESIS RESULT")
    print(f"{'='*50}")
    print(f"Best Model: {result.best_model}")
    print(f"Best Score: {result.best_score:.1f}/100")
    print(f"Output: {result.best_output}")
    print(f"\n📊 All Candidates:")
    for c in result.all_candidates:
        status = "✅" if c.success else "❌"
        print(f"   {status} {c.name}: Score={c.score:.1f}, Latency={c.latency_ms:.0f}ms")
    print(f"\n🤖 LLM Reasoning:\n{result.llm_reasoning}")


if __name__ == "__main__":
    main()
