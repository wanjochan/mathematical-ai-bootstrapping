"""Setup script for OmniParser installation and model download"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    packages = [
        "ultralytics",
        "transformers",
        "torch",
        "torchvision",
        "huggingface-hub",
        "gradio"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("Dependencies installed successfully!")

def download_omniparser_models():
    """Download OmniParser models from Hugging Face"""
    print("\nDownloading OmniParser models...")
    
    # Create weights directory
    weights_dir = Path("weights")
    weights_dir.mkdir(exist_ok=True)
    
    # Download using huggingface-cli
    print("Downloading detection model...")
    subprocess.run([
        "huggingface-cli", "download", 
        "microsoft/OmniParser-v2.0",
        "icon_detect/train_args.yaml",
        "icon_detect/model.pt", 
        "icon_detect/model.yaml",
        "--local-dir", "weights"
    ])
    
    print("Downloading caption model...")
    subprocess.run([
        "huggingface-cli", "download",
        "microsoft/OmniParser-v2.0", 
        "icon_caption/config.json",
        "icon_caption/generation_config.json",
        "icon_caption/model.safetensors",
        "--local-dir", "weights"
    ])
    
    # Rename caption folder
    caption_src = weights_dir / "icon_caption"
    caption_dst = weights_dir / "icon_caption_florence"
    if caption_src.exists() and not caption_dst.exists():
        caption_src.rename(caption_dst)
    
    print("Models downloaded successfully!")

def test_installation():
    """Test if OmniParser is properly installed"""
    print("\nTesting installation...")
    
    try:
        import ultralytics
        import transformers
        import torch
        print("✓ All dependencies imported successfully")
        
        # Check if models exist
        if Path("weights/icon_detect/model.pt").exists():
            print("✓ Detection model found")
        else:
            print("✗ Detection model not found")
            
        if Path("weights/icon_caption_florence/config.json").exists():
            print("✓ Caption model found")
        else:
            print("✗ Caption model not found")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("OmniParser Setup Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ is required")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Download models
    try:
        download_omniparser_models()
    except Exception as e:
        print(f"Error downloading models: {e}")
        print("You may need to manually download from:")
        print("https://huggingface.co/microsoft/OmniParser-v2.0")
    
    # Test installation
    if test_installation():
        print("\n✓ OmniParser setup completed successfully!")
        print("You can now use vision_model_omniparser.py")
    else:
        print("\n✗ Setup incomplete, please check errors above")

if __name__ == "__main__":
    main()