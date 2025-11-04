from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ModelName(str, Enum):
    """Available AI models for image generation"""
    STABLE_DIFFUSION_15 = "runwayml/stable-diffusion-v1-5"
    STABLE_DIFFUSION_21 = "stabilityai/stable-diffusion-2-1"
    STABLE_DIFFUSION_XL = "stabilityai/stable-diffusion-xl-base-1.0"

class GenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., description="Text prompt for image generation", min_length=1, max_length=1000)
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to avoid certain elements")
    width: int = Field(512, description="Image width in pixels", ge=64, le=2048)
    height: int = Field(512, description="Image height in pixels", ge=64, le=2048)
    num_inference_steps: int = Field(20, description="Number of denoising steps", ge=1, le=100)
    guidance_scale: float = Field(7.5, description="Guidance scale for prompt adherence", ge=1.0, le=20.0)
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    model_name: ModelName = Field(ModelName.STABLE_DIFFUSION_15, description="AI model to use for generation")

class GenerationResponse(BaseModel):
    """Response model for image generation"""
    success: bool = Field(..., description="Whether the generation was successful")
    image_url: Optional[str] = Field(None, description="URL path to the generated image")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if generation failed")