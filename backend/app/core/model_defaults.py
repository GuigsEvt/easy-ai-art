"""
Model default configurations for optimal generation parameters.
Each model has its own recommended settings for best results.
"""
from typing import Dict, Any
from pydantic import BaseModel


class ModelDefaults(BaseModel):
    """Default parameters for a specific model"""
    guidance_scale: float
    num_inference_steps: int
    width: int
    height: int
    sampler: str
    explanation: str


# Model-specific default configurations
MODEL_DEFAULTS: Dict[str, ModelDefaults] = {
    "sdxl-turbo": ModelDefaults(
        guidance_scale=1.0,
        num_inference_steps=6,
        width=512,
        height=512,
        sampler="lcm",
        explanation="SDXL-Turbo is optimized for fast generation with minimal steps. Uses low guidance scale (1.0) and LCM sampler for best results."
    ),
    "sdxl-base-1.0": ModelDefaults(
        guidance_scale=7.5,
        num_inference_steps=25,
        width=1024,
        height=1024,
        sampler="euler",
        explanation="SDXL Base provides high-quality images with more detail. Requires higher guidance scale (7.5) and more steps for optimal results."
    ),
    "qwen-image": ModelDefaults(
        guidance_scale=5.0,
        num_inference_steps=20,
        width=768,
        height=768,
        sampler="flowmatch",
        explanation="Qwen-Image is a versatile model that balances quality and speed. Works well with moderate guidance scale and Match Euler sampler."
    ),
    "FLUX": ModelDefaults(
        guidance_scale=2.0,
        num_inference_steps=12,
        width=1024,
        height=1024,
        sampler="flowmatch",
        explanation="FLUX is a high-quality diffusion model optimized for fast generation. Uses low CFG (2.0) and moderate steps (12) for best results."
    )
}


def get_model_defaults(model_name: str) -> ModelDefaults:
    """
    Get default parameters for a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        ModelDefaults object with recommended parameters
        
    Raises:
        KeyError: If model is not found in defaults
    """
    if model_name in MODEL_DEFAULTS:
        return MODEL_DEFAULTS[model_name]
    
    # Check if it's a FLUX model variant
    if "flux" in model_name.lower():
        return MODEL_DEFAULTS["FLUX"]
    
    # Fallback to sdxl-turbo defaults for unknown models
    return MODEL_DEFAULTS["sdxl-turbo"]


def get_all_model_defaults() -> Dict[str, ModelDefaults]:
    """
    Get all available model defaults.
    
    Returns:
        Dictionary mapping model names to their default parameters
    """
    return MODEL_DEFAULTS.copy()


def is_model_supported(model_name: str) -> bool:
    """
    Check if a model has defined defaults.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if model has defaults, False otherwise
    """
    return model_name in MODEL_DEFAULTS