#!/usr/bin/env python3
"""
Standalone Model Download Script for TGI
Downloads Gemma models from Hugging Face Hub with proper error handling
Usage: python download_model.py [--model-id MODEL_ID] [--output-dir OUTPUT_DIR]
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
import shutil
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelDownloader:
    """Handles model downloading with proper error handling and progress tracking"""
    
    def __init__(self, model_id: str, output_dir: str, hf_token: Optional[str] = None):
        self.model_id = model_id
        self.output_dir = Path(output_dir)
        self.hf_token = hf_token
        self.model_path = self.output_dir / self.model_id.split('/')[-1]
        
    def check_requirements(self) -> bool:
        """Check if all requirements are met"""
        try:
            import huggingface_hub
            logger.info("huggingface_hub available")
            return True
        except ImportError:
            logger.error("huggingface_hub not found. Installing...")
            os.system(f"{sys.executable} -m pip install huggingface_hub")
            return self.check_requirements()
    
    def check_disk_space(self, required_gb: float = 60) -> bool:
        """Check if there's enough disk space for the model"""
        try:
            free_space = shutil.disk_usage(self.output_dir.parent).free
            free_gb = free_space / (1024**3)
            
            if free_gb < required_gb:
                logger.error(f"Insufficient disk space. Required: {required_gb}GB, Available: {free_gb:.1f}GB")
                return False
            
            logger.info(f"Disk space check passed. Available: {free_gb:.1f}GB")
            return True
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False
    
    def check_existing_model(self) -> bool:
        """Check if model already exists and is complete"""
        if not self.model_path.exists():
            return False
            
        # Check for essential files
        essential_files = ['config.json', 'tokenizer.json']
        has_weights = any(self.model_path.glob('*.safetensors')) or any(self.model_path.glob('*.bin'))
        has_essentials = all((self.model_path / f).exists() for f in essential_files)
        
        if has_weights and has_essentials:
            logger.info(f"Model already exists at {self.model_path}")
            return True
        else:
            logger.warning(f"Incomplete model found at {self.model_path}. Re-downloading...")
            return False
    
    def download_model(self) -> bool:
        """Download the model from Hugging Face Hub"""
        try:
            from huggingface_hub import snapshot_download
            
            logger.info(f"Starting download: {self.model_id}")
            logger.info(f"Target directory: {self.model_path}")
            
            # Create output directory
            self.model_path.mkdir(parents=True, exist_ok=True)
            
            # Download model with progress
            snapshot_download(
                repo_id=self.model_id,
                local_dir=str(self.model_path),
                token=self.hf_token,
                ignore_patterns=[
                    "*.git*", 
                    "README.md", 
                    "*.msgpack", 
                    "*.h5",
                    "tf_model.h5",
                    "flax_model.msgpack"
                ],
                resume_download=True
            )
            
            logger.info("Model download completed successfully")
            self._save_download_info()
            return True
            
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return False
    
    def _save_download_info(self):
        """Save download metadata"""
        info = {
            "model_id": self.model_id,
            "download_path": str(self.model_path),
            "download_time": str(Path().resolve()),
        }
        
        info_file = self.model_path / '.download_info.json'
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)
    
    def run(self) -> bool:
        """Execute the complete download process"""
        logger.info("Starting model download process...")
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        # Check existing model
        if self.check_existing_model():
            return True
        
        # Check disk space
        if not self.check_disk_space():
            return False
        
        # Download model
        return self.download_model()

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description="Download models for Text Generation Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_model.py --model-id google/gemma-2-27b-it
  python download_model.py --model-id microsoft/DialoGPT-large --output-dir ./models
  python download_model.py --model-id gpt2 --hf-token your_token_here
        """
    )
    
    parser.add_argument(
        '--model-id',
        default='google/gemma-3-27b-it',
        help='Hugging Face model ID (default: google/gemma-3-27b-it)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./models',
        help='Output directory for downloaded models (default: ./models)'
    )
    
    parser.add_argument(
        '--hf-token',
        default=None,
        help='Hugging Face token for private models'
    )
    
    args = parser.parse_args()
    
    # Get token from environment if not provided
    hf_token = args.hf_token or os.getenv('HUGGING_FACE_HUB_TOKEN')
    
    # Create downloader and run
    downloader = ModelDownloader(
        model_id=args.model_id,
        output_dir=args.output_dir,
        hf_token=hf_token
    )
    
    if downloader.run():
        logger.info("Model download process completed successfully")
        print(f"\nModel ready at: {downloader.model_path}")
        print(f"Use in Docker: -v {downloader.model_path.absolute()}:/opt/models/{downloader.model_id.split('/')[-1]}")
        sys.exit(0)
    else:
        logger.error("Model download process failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 