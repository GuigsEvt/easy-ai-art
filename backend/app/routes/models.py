from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import json
import logging
from ..core.model_defaults import get_model_defaults, get_all_model_defaults, ModelDefaults, is_model_supported
from ..core.model_detection import detect_model_type

router = APIRouter()
logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    """Model information"""
    name: str = Field(..., description="Model name")
    path: str = Field(..., description="Model path")
    type: str = Field(..., description="Model type")
    pipeline_class: Optional[str] = Field(None, description="Pipeline class name")
    description: Optional[str] = Field(None, description="Model description")
    config: Optional[Dict[str, Any]] = Field(None, description="Model configuration")
    defaults: Optional[ModelDefaults] = Field(None, description="Default parameters for optimal generation")

class ModelsResponse(BaseModel):
    """Response model for available models"""
    success: bool = Field(..., description="Whether the request was successful")
    models: List[ModelInfo] = Field(..., description="List of available models")
    message: str = Field(..., description="Status message")

@router.get("/models", response_model=ModelsResponse)
async def get_available_models():
    """
    Get a list of all available models for image generation.
    """
    try:
        models = []
        models_dir = "models"  # Look in models directory relative to backend root
        
        # Check if models directory exists
        if not os.path.exists(models_dir):
            return ModelsResponse(
                success=False,
                models=[],
                message="Models directory not found"
            )
        
        # Scan the models directory
        for item in os.listdir(models_dir):
            if item.startswith('.') or item == '__pycache__':
                continue
                
            model_path = os.path.join(models_dir, item)
            
            # Check if it's a directory (model folder) and has model_index.json
            if os.path.isdir(model_path):
                model_index_path = os.path.join(model_path, "model_index.json")
                if os.path.exists(model_index_path):
                    # Use model detection to get the proper type
                    detected_type = detect_model_type(model_path)
                    
                    model_info = ModelInfo(
                        name=item,
                        path=model_path,
                        type=detected_type
                    )
                    
                    # Add model defaults if available
                    if is_model_supported(item):
                        model_info.defaults = get_model_defaults(item)
                    
                    # Read model_index.json for additional info
                    try:
                        with open(model_index_path, 'r') as f:
                            config = json.load(f)
                            model_info.pipeline_class = config.get("_class_name", "Unknown")
                            model_info.config = config
                    except Exception as e:
                        logger.warning(f"Could not read model config for {item}: {e}")
                    
                    # Try to read README.md for description
                    readme_path = os.path.join(model_path, "README.md")
                    if os.path.exists(readme_path):
                        try:
                            with open(readme_path, 'r') as f:
                                # Read first few lines as description
                                lines = f.readlines()[:5]
                                description = "".join(lines).strip()
                                if len(description) > 200:
                                    description = description[:200] + "..."
                                model_info.description = description
                        except Exception as e:
                            logger.warning(f"Could not read README for {item}: {e}")
                    
                    models.append(model_info)
        
        logger.info(f"Found {len(models)} available models")
        
        return ModelsResponse(
            success=True,
            models=models,
            message=f"Found {len(models)} available models"
        )
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(model_name: str):
    """
    Get detailed information about a specific model.
    """
    try:
        model_path = os.path.join("models", model_name)
        
        if not os.path.exists(model_path) or not os.path.isdir(model_path):
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
        # Use model detection to get the proper type
        detected_type = detect_model_type(model_path)
        
        model_info = ModelInfo(
            name=model_name,
            path=model_path,
            type=detected_type
        )
        
        # Add model defaults if available
        if is_model_supported(model_name):
            model_info.defaults = get_model_defaults(model_name)
        
        # Try to read model_index.json
        model_index_path = os.path.join(model_path, "model_index.json")
        if os.path.exists(model_index_path):
            try:
                with open(model_index_path, 'r') as f:
                    config = json.load(f)
                    model_info.pipeline_class = config.get("_class_name", "Unknown")
                    model_info.config = config
            except Exception as e:
                logger.warning(f"Could not read model config for {model_name}: {e}")
        
        # Try to read README.md
        readme_path = os.path.join(model_path, "README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r') as f:
                    description = f.read().strip()
                    if len(description) > 500:
                        description = description[:500] + "..."
                    model_info.description = description
            except Exception as e:
                logger.warning(f"Could not read README for {model_name}: {e}")
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.get("/models/defaults/all")
async def get_all_model_defaults_endpoint():
    """
    Get default parameters for all supported models.
    """
    try:
        defaults = get_all_model_defaults()
        return {
            "success": True,
            "defaults": defaults,
            "message": f"Retrieved defaults for {len(defaults)} models"
        }
    except Exception as e:
        logger.error(f"Error getting model defaults: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model defaults: {str(e)}")


@router.get("/models/{model_name}/defaults", response_model=ModelDefaults)
async def get_model_defaults_endpoint(model_name: str):
    """
    Get default parameters for a specific model.
    """
    try:
        if not is_model_supported(model_name):
            raise HTTPException(status_code=404, detail=f"No defaults available for model '{model_name}'")
        
        defaults = get_model_defaults(model_name)
        return defaults
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting defaults for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get defaults for {model_name}: {str(e)}")