#!/usr/bin/env python3
"""
🚀 StarConnect Voice Cloning CLI
Unified command-line interface for the complete voice cloning agent system.
Leverages Ollama LLMs and cutting-edge 2026 techniques.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_analyze(args):
    """Analyze the StarConnect dataset."""
    from agents.orchestrator import VoiceCloningOrchestrator
    
    orchestrator = VoiceCloningOrchestrator(dataset_path=args.dataset)
    result = orchestrator.analyze_voice_characteristics()
    
    print("\n📊 VOICE ANALYSIS")
    print("=" * 50)
    print(result.get("raw_analysis", "Analysis unavailable"))


def cmd_select(args):
    """Select best reference samples."""
    from agents.orchestrator import VoiceCloningOrchestrator
    
    orchestrator = VoiceCloningOrchestrator(dataset_path=args.dataset)
    samples = orchestrator.select_best_reference_samples(
        target_duration=args.duration
    )
    
    print(f"\n🎯 SELECTED {len(samples)} REFERENCE SAMPLES")
    print("=" * 50)
    
    total_duration = 0
    for i, s in enumerate(samples[:10]):
        print(f"{i+1}. {Path(s['audio_path']).name}")
        print(f"   Duration: {s.get('duration', 0):.2f}s")
        print(f"   Text: {s['transcription'][:60]}...")
        total_duration += s.get('duration', 0)
    
    if len(samples) > 10:
        print(f"   ... and {len(samples) - 10} more")
    
    print(f"\nTotal duration: {total_duration:.1f}s")


def cmd_profile(args):
    """Create a voice profile."""
    from agents.orchestrator import VoiceCloningOrchestrator
    
    orchestrator = VoiceCloningOrchestrator(
        dataset_path=args.dataset,
        output_dir=args.output
    )
    profile = orchestrator.create_voice_profile(name=args.name)
    
    print(f"\n✅ VOICE PROFILE CREATED")
    print("=" * 50)
    print(f"Name: {profile.name}")
    print(f"Reference audios: {len(profile.reference_audios)}")
    print(f"Language: {profile.language}")


def cmd_clone(args):
    """Clone a voice with text."""
    from agents.zero_shot_cloning import ZeroShotCloningAgent, EmotionalTTSAgent
    
    if args.emotion and args.emotion != "neutral":
        agent = EmotionalTTSAgent()
        result = agent.generate_emotional_speech(
            text=args.text,
            reference_audio=args.reference,
            emotion=args.emotion
        )
    else:
        agent = ZeroShotCloningAgent(output_dir=args.output)
        result = agent.clone_voice(
            text=args.text,
            reference_audio=args.reference,
            reference_text=args.ref_text,
            model=args.model
        )
    
    print(f"\n{'='*50}")
    if result.success:
        print(f"✅ VOICE CLONING SUCCESSFUL")
        print(f"   Output: {result.output_path}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Model: {result.model_used}")
    else:
        print(f"❌ VOICE CLONING FAILED")
        print(f"   Error: {result.error}")


def cmd_ensemble(args):
    """Use ensemble of models for best quality."""
    from agents.ensemble_agent import MultiModelEnsembleAgent
    
    agent = MultiModelEnsembleAgent(output_dir=args.output)
    result = agent.synthesize_ensemble(
        text=args.text,
        reference_audio=args.reference,
        reference_text=args.ref_text,
        language=args.language
    )
    
    print(f"\n{'='*50}")
    print(f"🧠 ENSEMBLE RESULT")
    print(f"{'='*50}")
    print(f"Best Model: {result.best_model}")
    print(f"Best Score: {result.best_score:.1f}/100")
    print(f"Output: {result.best_output}")


def cmd_assess(args):
    """Assess audio quality."""
    from agents.quality_agent import AudioQualityAgent
    
    agent = AudioQualityAgent()
    
    if args.compare:
        result = agent.compare_voices(args.compare, args.audio)
        print(f"\n{'='*50}")
        print(f"📊 VOICE COMPARISON")
        print(f"{'='*50}")
        print(f"Reference Score: {result.reference_metrics.overall_score:.1f}/100")
        print(f"Cloned Score: {result.cloned_metrics.overall_score:.1f}/100")
        print(f"Similarity: {result.similarity_score*100:.1f}%")
        print(f"Verdict: {result.verdict}")
    else:
        metrics = agent.assess_audio(args.audio)
        print(f"\n{'='*50}")
        print(f"📊 AUDIO QUALITY")
        print(f"{'='*50}")
        print(f"Score: {metrics.overall_score:.1f}/100 ({metrics.grade})")
        print(f"SNR: {metrics.snr_db:.1f} dB")
        print(f"Dynamic Range: {metrics.dynamic_range_db:.1f} dB")
        if metrics.recommendations:
            print(f"\nRecommendations:")
            for rec in metrics.recommendations:
                print(f"  • {rec}")


def cmd_batch(args):
    """Batch process multiple texts."""
    from agents.zero_shot_cloning import ZeroShotCloningAgent
    
    # Read texts from file
    with open(args.input, 'r', encoding='utf-8') as f:
        texts = [line.strip() for line in f if line.strip()]
    
    agent = ZeroShotCloningAgent(output_dir=args.output)
    results = agent.batch_clone(
        texts=texts,
        reference_audio=args.reference,
        reference_text=args.ref_text
    )
    
    success_count = sum(1 for r in results if r.success)
    print(f"\n{'='*50}")
    print(f"📦 BATCH PROCESSING COMPLETE")
    print(f"{'='*50}")
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")


def cmd_models(args):
    """List available models."""
    from agents.ensemble_agent import MultiModelEnsembleAgent
    
    agent = MultiModelEnsembleAgent()
    
    print(f"\n{'='*50}")
    print(f"🤖 AVAILABLE MODELS")
    print(f"{'='*50}")
    
    for model_id, available in agent.available_models.items():
        info = agent.MODEL_REGISTRY.get(model_id, {})
        status = "✅" if available else "❌"
        print(f"{status} {info.get('name', model_id)}")
        print(f"   Languages: {', '.join(info.get('languages', []))}")
        print(f"   Quality: {info.get('quality_tier', 'unknown')}")
        print(f"   Speed: {info.get('speed', 'unknown')}")
        print(f"   Strengths: {', '.join(info.get('strengths', []))}")
        print()


def cmd_ollama(args):
    """Check Ollama status."""
    import subprocess
    
    print(f"\n{'='*50}")
    print(f"🦙 OLLAMA STATUS")
    print(f"{'='*50}")
    
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    print(result.stdout)


def main():
    parser = argparse.ArgumentParser(
        description="🎙️ StarConnect Voice Cloning CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze dataset
  python starconnect.py analyze --dataset ./StarConnect

  # Clone a voice
  python starconnect.py clone --text "Bonjour!" --reference ./sample.wav

  # Use ensemble for best quality
  python starconnect.py ensemble --text "Bonjour!" --reference ./sample.wav

  # Assess audio quality
  python starconnect.py assess --audio ./output.wav
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Analyze command
    p_analyze = subparsers.add_parser("analyze", help="Analyze voice dataset")
    p_analyze.add_argument("--dataset", default="./StarConnect", help="Dataset path")
    p_analyze.set_defaults(func=cmd_analyze)
    
    # Select command
    p_select = subparsers.add_parser("select", help="Select reference samples")
    p_select.add_argument("--dataset", default="./StarConnect", help="Dataset path")
    p_select.add_argument("--duration", type=float, default=30, help="Target duration")
    p_select.set_defaults(func=cmd_select)
    
    # Profile command
    p_profile = subparsers.add_parser("profile", help="Create voice profile")
    p_profile.add_argument("--dataset", default="./StarConnect", help="Dataset path")
    p_profile.add_argument("--name", default="StarConnect", help="Profile name")
    p_profile.add_argument("--output", help="Output directory")
    p_profile.set_defaults(func=cmd_profile)
    
    # Clone command
    p_clone = subparsers.add_parser("clone", help="Clone voice")
    p_clone.add_argument("--text", required=True, help="Text to synthesize")
    p_clone.add_argument("--reference", required=True, help="Reference audio")
    p_clone.add_argument("--ref-text", help="Reference transcription")
    p_clone.add_argument("--model", default="auto", help="Model to use")
    p_clone.add_argument("--emotion", default="neutral", help="Emotion")
    p_clone.add_argument("--output", help="Output directory")
    p_clone.set_defaults(func=cmd_clone)
    
    # Ensemble command
    p_ensemble = subparsers.add_parser("ensemble", help="Use model ensemble")
    p_ensemble.add_argument("--text", required=True, help="Text to synthesize")
    p_ensemble.add_argument("--reference", required=True, help="Reference audio")
    p_ensemble.add_argument("--ref-text", help="Reference transcription")
    p_ensemble.add_argument("--language", default="fr", help="Language")
    p_ensemble.add_argument("--output", help="Output directory")
    p_ensemble.set_defaults(func=cmd_ensemble)
    
    # Assess command
    p_assess = subparsers.add_parser("assess", help="Assess audio quality")
    p_assess.add_argument("--audio", required=True, help="Audio to assess")
    p_assess.add_argument("--compare", help="Reference for comparison")
    p_assess.set_defaults(func=cmd_assess)
    
    # Batch command
    p_batch = subparsers.add_parser("batch", help="Batch process texts")
    p_batch.add_argument("--input", required=True, help="Input file with texts")
    p_batch.add_argument("--reference", required=True, help="Reference audio")
    p_batch.add_argument("--ref-text", help="Reference transcription")
    p_batch.add_argument("--output", help="Output directory")
    p_batch.set_defaults(func=cmd_batch)
    
    # Models command
    p_models = subparsers.add_parser("models", help="List available models")
    p_models.set_defaults(func=cmd_models)
    
    # Ollama command
    p_ollama = subparsers.add_parser("ollama", help="Check Ollama status")
    p_ollama.set_defaults(func=cmd_ollama)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Run command
    args.func(args)


if __name__ == "__main__":
    main()
