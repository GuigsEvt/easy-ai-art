from pydantic import BaseModel, Field
from typing import Optional


class GenerationRequest(BaseModel):
    """Request model for image generation"""
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt to avoid certain elements")
    width: Optional[int] = Field(512, description="Image width in pixels", ge=64, le=2048)
    height: Optional[int] = Field(512, description="Image height in pixels", ge=64, le=2048)
    num_inference_steps: Optional[int] = Field(6, description="Number of denoising steps", ge=1, le=50)
    guidance_scale: Optional[float] = Field(1.0, description="Guidance scale for generation", ge=0.1, le=20.0)
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    model_name: Optional[str] = Field("sdxl-turbo", description="Model name to use for generation")
    sampler: Optional[str] = Field("euler_a", description="Sampler algorithm to use")


class GenerationResponse(BaseModel):
    """Response model for image generation"""
    success: bool = Field(..., description="Whether the generation was successful")
    image_url: Optional[str] = Field(None, description="URL path to the generated image")
    message: str = Field(..., description="Status message")
    filename: Optional[str] = Field(None, description="Generated image filename")
    generation_time: Optional[float] = Field(None, description="Time taken to generate the image in seconds")