#!/usr/bin/env python3
"""
🔬 Audio Quality Assessment Agent
Cutting-edge 2026 agent for evaluating voice cloning quality.
Uses LLM reasoning + audio signal processing.
"""

import json
import os
import subprocess
import wave
import struct
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import requests


@dataclass
class QualityMetrics:
    """Audio quality assessment metrics."""
    # Technical metrics
    snr_db: float = 0.0                 # Signal-to-noise ratio
    silence_ratio: float = 0.0         # Ratio of silence
    clipping_ratio: float = 0.0        # Ratio of clipped samples
    dynamic_range_db: float = 0.0       # Dynamic range
    
    # Perceptual metrics (estimated)
    intelligibility_score: float = 0.0  # 0-1 speech clarity
    naturalness_score: float = 0.0      # 0-1 how natural it sounds
    similarity_score: float = 0.0       # 0-1 similarity to reference
    
    # Overall
    overall_score: float = 0.0          # 0-100 overall quality
    grade: str = ""                     # A-F grade
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """Result of comparing original vs cloned voice."""
    reference_metrics: QualityMetrics
    cloned_metrics: QualityMetrics
    similarity_score: float
    verdict: str
    detailed_analysis: str


class AudioQualityAgent:
    """
    Agent for assessing audio quality using signal processing + LLM reasoning.
    """
    
    GRADE_THRESHOLDS = {
        "A+": 95, "A": 90, "A-": 85,
        "B+": 80, "B": 75, "B-": 70,
        "C+": 65, "C": 60, "C-": 55,
        "D": 50, "F": 0
    }
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        print("🔬 Audio Quality Agent initialized")
    
    def _read_wav_samples(self, audio_path: str) -> Tuple[List[float], int]:
        """Read samples from WAV file."""
        try:
            with wave.open(audio_path, 'r') as wav:
                n_channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                n_frames = wav.getnframes()
                
                frames = wav.readframes(n_frames)
                
                # Convert to float samples
                if sample_width == 2:  # 16-bit
                    fmt = f"<{n_frames * n_channels}h"
                    samples = list(struct.unpack(fmt, frames))
                    samples = [s / 32768.0 for s in samples]
                elif sample_width == 4:  # 32-bit
                    fmt = f"<{n_frames * n_channels}i"
                    samples = list(struct.unpack(fmt, frames))
                    samples = [s / 2147483648.0 for s in samples]
                else:
                    samples = [0.0] * n_frames
                
                # Convert to mono if stereo
                if n_channels == 2:
                    samples = [(samples[i] + samples[i+1]) / 2 
                               for i in range(0, len(samples), 2)]
                
                return samples, framerate
        except Exception as e:
            print(f"⚠️ Error reading {audio_path}: {e}")
            return [], 0
    
    def _calculate_rms(self, samples: List[float]) -> float:
        """Calculate RMS of samples."""
        if not samples:
            return 0.0
        sum_sq = sum(s * s for s in samples)
        return math.sqrt(sum_sq / len(samples))
    
    def _calculate_snr(self, samples: List[float]) -> float:
        """Estimate SNR in dB."""
        if not samples:
            return 0.0
        
        # Simple noise floor estimation (from quietest 10%)
        sorted_samples = sorted([abs(s) for s in samples])
        noise_floor = self._calculate_rms(sorted_samples[:len(sorted_samples)//10])
        signal_level = self._calculate_rms(samples)
        
        if noise_floor < 1e-10:
            return 60.0  # Very clean
        
        snr = 20 * math.log10(signal_level / noise_floor)
        return max(0, min(60, snr))
    
    def _calculate_silence_ratio(
        self,
        samples: List[float],
        threshold: float = 0.01
    ) -> float:
        """Calculate ratio of silent samples."""
        if not samples:
            return 0.0
        silent = sum(1 for s in samples if abs(s) < threshold)
        return silent / len(samples)
    
    def _calculate_clipping_ratio(
        self,
        samples: List[float],
        threshold: float = 0.99
    ) -> float:
        """Calculate ratio of clipped samples."""
        if not samples:
            return 0.0
        clipped = sum(1 for s in samples if abs(s) > threshold)
        return clipped / len(samples)
    
    def _calculate_dynamic_range(self, samples: List[float]) -> float:
        """Calculate dynamic range in dB."""
        if not samples:
            return 0.0
        
        peak = max(abs(s) for s in samples)
        sorted_samples = sorted([abs(s) for s in samples])
        floor = sorted_samples[len(sorted_samples)//10]  # 10th percentile
        
        if floor < 1e-10:
            floor = 1e-10
        
        dr = 20 * math.log10(peak / floor)
        return max(0, min(60, dr))
    
    def assess_audio(self, audio_path: str) -> QualityMetrics:
        """
        Assess quality of an audio file.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            QualityMetrics with detailed assessment
        """
        samples, sample_rate = self._read_wav_samples(audio_path)
        
        if not samples:
            return QualityMetrics(
                overall_score=0,
                grade="F",
                recommendations=["Could not read audio file"]
            )
        
        # Calculate technical metrics
        snr = self._calculate_snr(samples)
        silence_ratio = self._calculate_silence_ratio(samples)
        clipping_ratio = self._calculate_clipping_ratio(samples)
        dynamic_range = self._calculate_dynamic_range(samples)
        
        # Calculate scores
        snr_score = min(1.0, snr / 40)  # 40dB is excellent
        silence_score = 1.0 - min(1.0, silence_ratio / 0.5)  # Up to 50% silence ok
        clipping_score = 1.0 - min(1.0, clipping_ratio * 100)  # Any clipping is bad
        dr_score = min(1.0, dynamic_range / 30)  # 30dB is good
        
        # Estimate perceptual metrics (simplified)
        intelligibility = (snr_score * 0.5 + (1 - clipping_score) * 0.3 + dr_score * 0.2)
        naturalness = (snr_score * 0.3 + dr_score * 0.4 + (1 - silence_ratio) * 0.3)
        
        # Overall score
        overall = (
            snr_score * 25 +
            silence_score * 15 +
            clipping_score * 20 +
            dr_score * 15 +
            intelligibility * 15 +
            naturalness * 10
        )
        
        # Determine grade
        grade = "F"
        for g, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
            if overall >= threshold:
                grade = g
                break
        
        # Generate recommendations
        recommendations = []
        if snr < 20:
            recommendations.append("Consider noise reduction - SNR is low")
        if clipping_ratio > 0.001:
            recommendations.append("Audio has clipping - reduce input gain")
        if silence_ratio > 0.3:
            recommendations.append("High silence ratio - consider trimming")
        if dynamic_range < 15:
            recommendations.append("Low dynamic range - may sound compressed")
        
        return QualityMetrics(
            snr_db=snr,
            silence_ratio=silence_ratio,
            clipping_ratio=clipping_ratio,
            dynamic_range_db=dynamic_range,
            intelligibility_score=intelligibility,
            naturalness_score=naturalness,
            similarity_score=0.0,  # Need reference for this
            overall_score=overall,
            grade=grade,
            recommendations=recommendations
        )
    
    def compare_voices(
        self,
        reference_audio: str,
        cloned_audio: str
    ) -> ComparisonResult:
        """
        Compare reference and cloned voice quality.
        
        Args:
            reference_audio: Path to original reference audio
            cloned_audio: Path to cloned output audio
        
        Returns:
            ComparisonResult with detailed comparison
        """
        ref_metrics = self.assess_audio(reference_audio)
        cloned_metrics = self.assess_audio(cloned_audio)
        
        # Calculate similarity (simplified - would use embeddings in production)
        snr_sim = 1.0 - abs(ref_metrics.snr_db - cloned_metrics.snr_db) / 40
        dr_sim = 1.0 - abs(ref_metrics.dynamic_range_db - cloned_metrics.dynamic_range_db) / 30
        
        similarity = (snr_sim + dr_sim) / 2
        similarity = max(0, min(1, similarity))
        
        # Use LLM for detailed analysis
        analysis = self._generate_llm_analysis(ref_metrics, cloned_metrics, similarity)
        
        # Generate verdict
        if cloned_metrics.overall_score >= 80 and similarity >= 0.7:
            verdict = "EXCELLENT - High quality clone with good similarity"
        elif cloned_metrics.overall_score >= 60 and similarity >= 0.5:
            verdict = "GOOD - Acceptable quality, minor improvements possible"
        elif cloned_metrics.overall_score >= 40:
            verdict = "FAIR - Quality issues detected, review recommendations"
        else:
            verdict = "POOR - Significant quality issues, requires regeneration"
        
        return ComparisonResult(
            reference_metrics=ref_metrics,
            cloned_metrics=cloned_metrics,
            similarity_score=similarity,
            verdict=verdict,
            detailed_analysis=analysis
        )
    
    def _generate_llm_analysis(
        self,
        ref_metrics: QualityMetrics,
        cloned_metrics: QualityMetrics,
        similarity: float
    ) -> str:
        """Use LLM to generate detailed analysis."""
        prompt = f"""Analyze this voice cloning quality comparison:

REFERENCE AUDIO:
- SNR: {ref_metrics.snr_db:.1f} dB
- Dynamic Range: {ref_metrics.dynamic_range_db:.1f} dB
- Overall Score: {ref_metrics.overall_score:.1f}/100
- Grade: {ref_metrics.grade}

CLONED AUDIO:
- SNR: {cloned_metrics.snr_db:.1f} dB
- Dynamic Range: {cloned_metrics.dynamic_range_db:.1f} dB
- Overall Score: {cloned_metrics.overall_score:.1f}/100
- Grade: {cloned_metrics.grade}
- Clipping: {cloned_metrics.clipping_ratio*100:.2f}%

SIMILARITY SCORE: {similarity*100:.1f}%

Provide:
1. Brief quality assessment (2-3 sentences)
2. Main strengths
3. Areas for improvement
4. Recommended actions"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "qwen3:8b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            return response.json().get("response", "Analysis unavailable")
        except:
            return "LLM analysis unavailable - using metrics only"
    
    def batch_assess(self, audio_dir: str) -> Dict[str, QualityMetrics]:
        """Assess all audio files in a directory."""
        results = {}
        audio_dir = Path(audio_dir)
        
        for audio_file in audio_dir.glob("*.wav"):
            print(f"🔬 Assessing: {audio_file.name}")
            metrics = self.assess_audio(str(audio_file))
            results[audio_file.name] = metrics
            print(f"   Score: {metrics.overall_score:.1f}/100 ({metrics.grade})")
        
        return results
    
    def generate_report(
        self,
        metrics: Dict[str, QualityMetrics],
        output_path: str = None
    ) -> str:
        """Generate a comprehensive quality report."""
        report = {
            "summary": {
                "total_files": len(metrics),
                "average_score": sum(m.overall_score for m in metrics.values()) / len(metrics) if metrics else 0,
                "grade_distribution": {}
            },
            "files": {}
        }
        
        # Grade distribution
        for name, m in metrics.items():
            grade = m.grade
            report["summary"]["grade_distribution"][grade] = \
                report["summary"]["grade_distribution"].get(grade, 0) + 1
            
            report["files"][name] = {
                "score": m.overall_score,
                "grade": m.grade,
                "snr_db": m.snr_db,
                "recommendations": m.recommendations
            }
        
        report_json = json.dumps(report, indent=2, ensure_ascii=False)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_json)
            print(f"📊 Report saved: {output_path}")
        
        return report_json


class VoiceSimilarityAgent:
    """
    Agent for measuring voice similarity using embeddings.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.quality_agent = AudioQualityAgent(ollama_url)
    
    def extract_voice_signature(self, audio_path: str) -> Dict:
        """Extract a voice signature (simplified embedding)."""
        samples, sr = self.quality_agent._read_wav_samples(audio_path)
        
        if not samples:
            return {"error": "Could not read audio"}
        
        # Simplified spectral features
        rms = self.quality_agent._calculate_rms(samples)
        snr = self.quality_agent._calculate_snr(samples)
        dr = self.quality_agent._calculate_dynamic_range(samples)
        
        # Zero crossing rate (rough pitch estimate)
        zcr = sum(1 for i in range(1, len(samples)) 
                  if samples[i-1] * samples[i] < 0) / len(samples)
        
        return {
            "rms_energy": rms,
            "snr_db": snr,
            "dynamic_range_db": dr,
            "zero_crossing_rate": zcr,
            "sample_rate": sr,
            "duration": len(samples) / sr if sr else 0
        }
    
    def calculate_similarity(
        self,
        reference_audio: str,
        test_audio: str
    ) -> float:
        """Calculate similarity between two voices."""
        ref_sig = self.extract_voice_signature(reference_audio)
        test_sig = self.extract_voice_signature(test_audio)
        
        if "error" in ref_sig or "error" in test_sig:
            return 0.0
        
        # Simple cosine-like similarity on features
        features = ["rms_energy", "snr_db", "dynamic_range_db", "zero_crossing_rate"]
        
        diff_sum = 0
        for f in features:
            ref_val = ref_sig.get(f, 0)
            test_val = test_sig.get(f, 0)
            max_val = max(abs(ref_val), abs(test_val), 1e-10)
            diff_sum += abs(ref_val - test_val) / max_val
        
        similarity = 1.0 - (diff_sum / len(features))
        return max(0, min(1, similarity))


def main():
    """Demo of audio quality agents."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Audio Quality Assessment Agent")
    parser.add_argument("--audio", help="Audio file to assess")
    parser.add_argument("--reference", help="Reference audio for comparison")
    parser.add_argument("--batch", help="Directory for batch assessment")
    parser.add_argument("--report", help="Output report path")
    
    args = parser.parse_args()
    
    agent = AudioQualityAgent()
    
    if args.batch:
        metrics = agent.batch_assess(args.batch)
        if args.report:
            agent.generate_report(metrics, args.report)
    elif args.audio and args.reference:
        result = agent.compare_voices(args.reference, args.audio)
        print(f"\n{'='*50}")
        print(f"📊 VOICE COMPARISON REPORT")
        print(f"{'='*50}")
        print(f"Reference: {args.reference}")
        print(f"Cloned: {args.audio}")
        print(f"\nReference Score: {result.reference_metrics.overall_score:.1f}/100 ({result.reference_metrics.grade})")
        print(f"Cloned Score: {result.cloned_metrics.overall_score:.1f}/100 ({result.cloned_metrics.grade})")
        print(f"Similarity: {result.similarity_score*100:.1f}%")
        print(f"\n🎯 VERDICT: {result.verdict}")
        print(f"\n📝 ANALYSIS:\n{result.detailed_analysis}")
    elif args.audio:
        metrics = agent.assess_audio(args.audio)
        print(f"\n{'='*50}")
        print(f"📊 AUDIO QUALITY REPORT")
        print(f"{'='*50}")
        print(f"File: {args.audio}")
        print(f"Overall Score: {metrics.overall_score:.1f}/100")
        print(f"Grade: {metrics.grade}")
        print(f"\nTechnical Metrics:")
        print(f"  SNR: {metrics.snr_db:.1f} dB")
        print(f"  Dynamic Range: {metrics.dynamic_range_db:.1f} dB")
        print(f"  Silence Ratio: {metrics.silence_ratio*100:.1f}%")
        print(f"  Clipping: {metrics.clipping_ratio*100:.3f}%")
        print(f"\nRecommendations:")
        for rec in metrics.recommendations:
            print(f"  • {rec}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
