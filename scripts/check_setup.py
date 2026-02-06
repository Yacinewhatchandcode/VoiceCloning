#!/usr/bin/env python3
"""
Script de vérification de l'installation et de l'environnement.
Vérifie les dépendances, FFmpeg, GPU, etc.
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Vérifie la version de Python."""
    print("🐍 Python Version")
    version = sys.version_info
    print(f"   Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("   ❌ Python 3.9+ requis")
        return False
    else:
        print("   ✅ Version OK")
        return True


def check_package(package_name: str, import_name: str = None) -> bool:
    """Vérifie qu'un package Python est installé."""
    if import_name is None:
        import_name = package_name
    
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "unknown")
        print(f"   ✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"   ❌ {package_name}: non installé")
        return False


def check_python_packages():
    """Vérifie les packages Python critiques."""
    print("\n📦 Python Packages")
    
    packages = [
        ("torch", "torch"),
        ("torchaudio", "torchaudio"),
        ("TTS", "TTS"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("librosa", "librosa"),
        ("soundfile", "soundfile"),
        ("datasets", "datasets"),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)


def check_ffmpeg():
    """Vérifie que FFmpeg est installé."""
    print("\n🎬 FFmpeg")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        version_line = result.stdout.split("\n")[0]
        print(f"   ✅ {version_line}")
        return True
    except FileNotFoundError:
        print("   ❌ FFmpeg non trouvé")
        print("      Installation: brew install ffmpeg (macOS)")
        return False


def check_sox():
    """Vérifie que SoX est installé."""
    print("\n🔊 SoX")
    try:
        result = subprocess.run(
            ["sox", "--version"],
            capture_output=True,
            text=True
        )
        version_line = result.stdout.strip()
        print(f"   ✅ {version_line}")
        return True
    except FileNotFoundError:
        print("   ❌ SoX non trouvé")
        print("      Installation: brew install sox (macOS)")
        return False


def check_gpu():
    """Vérifie la disponibilité du GPU."""
    print("\n🖥️  GPU")
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"   ✅ CUDA disponible")
            print(f"      Version: {torch.version.cuda}")
            print(f"      Devices: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                print(f"      GPU {i}: {name}")
            return True
        elif torch.backends.mps.is_available():
            print(f"   ✅ MPS (Apple Silicon) disponible")
            return True
        else:
            print("   ⚠️  Pas de GPU détecté (CPU uniquement)")
            return False
    except ImportError:
        print("   ❌ PyTorch non installé")
        return False


def check_disk_space():
    """Vérifie l'espace disque disponible."""
    print("\n💾 Espace Disque")
    try:
        import shutil
        
        total, used, free = shutil.disk_usage("/")
        
        free_gb = free // (2**30)
        total_gb = total // (2**30)
        
        print(f"   Total: {total_gb} GB")
        print(f"   Libre: {free_gb} GB")
        
        if free_gb < 50:
            print("   ⚠️  Moins de 50 GB disponibles (recommandé: 50+ GB)")
            return False
        else:
            print("   ✅ Espace suffisant")
            return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_directories():
    """Vérifie la structure des répertoires."""
    print("\n📁 Structure des Répertoires")
    
    base_dir = Path(__file__).parent
    
    required_dirs = [
        "datasets",
        "datasets/raw",
        "datasets/processed",
        "datasets/metadata",
        "models",
        "models/pretrained",
        "models/finetuned",
        "scripts",
        "configs",
        "logs",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ⚠️  {dir_path} (sera créé automatiquement)")
    
    return True


def main():
    """Exécute toutes les vérifications."""
    print("=" * 60)
    print("🔍 Vérification de l'environnement Voice Cloning")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Python Packages", check_python_packages),
        ("FFmpeg", check_ffmpeg),
        ("SoX", check_sox),
        ("GPU", check_gpu),
        ("Disk Space", check_disk_space),
        ("Directories", check_directories),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Erreur lors de la vérification '{name}': {e}")
            results[name] = False
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 Résumé")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    # Statut global
    critical_checks = ["Python Version", "Python Packages"]
    critical_ok = all(results.get(check, False) for check in critical_checks)
    
    print("\n" + "=" * 60)
    if critical_ok:
        print("✅ Environnement prêt pour l'entraînement!")
        if not results.get("GPU", False):
            print("⚠️  Note: Pas de GPU détecté, l'entraînement sera lent")
    else:
        print("❌ Environnement incomplet")
        print("   Installez les dépendances manquantes:")
        print("   pip install -r requirements.txt")
    print("=" * 60)
    
    return 0 if critical_ok else 1


if __name__ == "__main__":
    sys.exit(main())
