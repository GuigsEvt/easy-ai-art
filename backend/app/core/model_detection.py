"""
Model type detection utility for determining the correct pipeline usage.
"""
from pathlib import Path
import json
import logging
from typing import Literal, Optional

logger = logging.getLogger(__name__)

ModelType = Literal[
    "Text-to-Image",
    "Image-to-Image (Img2Img)", 
    "Inpainting",
    "Depth-to-Image",
    "Qwen-Image (Text-to-Image)",
    "FLUX.1 (Text-to-Image)",
    "FLUX.1 (Image-to-Image)",
    "ControlNet (auxiliary)",
    "Text-to-Image (most likely)"
]

def detect_model_type(model_path: str) -> ModelType:
    """
    Detect the model type based on model_index.json and folder name patterns.
    
    Args:
        model_path: Path to the model directory
        
    Returns:
        ModelType: The detected model type/usage
    """
    path = Path(model_path)
    
    # 1. Look for model_index.json (the gold standard)
    index_file = path / "model_index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r') as f:
                data = json.load(f)
            
            cls = data.get("_class_name", "")
            pipeline_type = data.get("_pipeline_type", "")
            
            # Check for specific pipeline classes
            if "Img2Img" in cls or "image_to_image" in pipeline_type.lower():
                return "Image-to-Image (Img2Img)"
            if "Inpaint" in cls:
                return "Inpainting"
            if "Depth" in cls:
                return "Depth-to-Image"
            if "QwenImagePipeline" in cls:
                return "Qwen-Image (Text-to-Image)"
            if "FluxPipeline" in cls:
                return "FLUX.1 (Text-to-Image)"
            if "FluxKontextPipeline" in cls:
                return "FLUX.1 (Image-to-Image)"
            if any(k in cls for k in ["StableDiffusion", "PixArt", "SD3"]):
                return "Text-to-Image"
                
        except Exception as e:
            logger.warning(f"Could not read model_index.json for {model_path}: {e}")
    
    # 2. Fallback: folder name clues
    name = path.name.lower()
    if any(x in name for x in ["inpainting", "inpaint", "-ip-"]):
        return "Inpainting"
    if "img2img" in name or "i2i" in name:
        return "Image-to-Image (Img2Img)"
    if "controlnet" in name:
        return "ControlNet (auxiliary)"
    if "qwen" in name:
        return "Qwen-Image (Text-to-Image)"
    if "flux" in name:
        return "FLUX.1 (Text-to-Image)"
    
    # 3. Default assumption for diffusion models
    return "Text-to-Image (most likely)"


def is_text_to_image_model(model_path: str) -> bool:
    """
    Check if a model is suitable for text-to-image generation.
    
    Args:
        model_path: Path to the model directory
        
    Returns:
        bool: True if the model is suitable for text-to-image
    """
    model_type = detect_model_type(model_path)
    return model_type in [
        "Text-to-Image",
        "Qwen-Image (Text-to-Image)",
        "FLUX.1 (Text-to-Image)",
        "Text-to-Image (most likely)"
    ]


def is_image_to_image_model(model_path: str) -> bool:
    """
    Check if a model is suitable for image-to-image generation.
    
    Args:
        model_path: Path to the model directory
        
    Returns:
        bool: True if the model is suitable for image-to-image
    """
    model_type = detect_model_type(model_path)
    return model_type in [
        "Image-to-Image (Img2Img)",
        "Inpainting",
        "Depth-to-Image",
        "FLUX.1 (Image-to-Image)",  # FLUX Kontext models support img2img
        "Text-to-Image",  # Most text-to-image models can do img2img
        "FLUX.1 (Text-to-Image)",  # FLUX models support img2img
        "Text-to-Image (most likely)"
    ]


def get_recommended_model_for_task(models_dir: str, task: str = "text-to-image") -> Optional[str]:
    """
    Get a recommended model for a specific task from available models.
    
    Args:
        models_dir: Path to the models directory
        task: Task type ("text-to-image" or "image-to-image")
        
    Returns:
        str or None: Name of recommended model, or None if no suitable model found
    """
    models_path = Path(models_dir)
    if not models_path.exists():
        return None
    
    suitable_models = []
    
    for model_dir in models_path.iterdir():
        if model_dir.is_dir() and not model_dir.name.startswith('.'):
            model_path = str(model_dir)
            
            if task == "text-to-image" and is_text_to_image_model(model_path):
                suitable_models.append(model_dir.name)
            elif task == "image-to-image" and is_image_to_image_model(model_path):
                suitable_models.append(model_dir.name)
    
    # Return the first suitable model found
    return suitable_models[0] if suitable_models else None


if __name__ == "__main__":
    # Test the detection function
    import sys
    
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
        result = detect_model_type(model_path)
        print(f"Model at '{model_path}': {result}")
    else:
        # Test with known models
        test_models = [
            "models/sdxl-turbo",
            "models/sdxl-base-1.0", 
            "models/qwen-image",
            "models/stable-diffusion-xl-refiner-1.0"
        ]
        
        for model in test_models:
            try:
                result = detect_model_type(model)
                print(f"{model}: {result}")
            except Exception as e:
                print(f"{model}: Error - {e}")