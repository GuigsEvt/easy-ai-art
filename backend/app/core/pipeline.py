import os
import logging
from typing import Optional, List
import asyncio
from datetime import datetime
from pathlib import Path
import torch
from PIL import Image
import time

from .text2image import build_pipe, detect_device, multiple_of_8, save_image, SAMPLERS

logger = logging.getLogger(__name__)

class ImagePipeline:
    """
    Image generation pipeline using diffusion models with SDXL-Turbo.
    """
    
    def __init__(self):
        self.models_dir = Path("app/models")
        self.outputs_dir = Path("outputs")
        self.default_model_path = "app/models/sdxl-turbo"
        self.available_models = [
            "sdxl-turbo"  # Local model we have available
        ]
        self._ensure_directories()
        self._device = None
        self._dtype = None
        self._pipe = None
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_device_info(self):
        """Get device and dtype information"""
        if self._device is None or self._dtype is None:
            self._device, self._dtype = detect_device()
        return self._device, self._dtype
    
    def _load_pipeline(self, model_path: str, sampler: str = "lcm"):
        """Load the diffusion pipeline"""
        if self._pipe is None:
            device, dtype = self._get_device_info()
            self._pipe = build_pipe(model_path, sampler, device, dtype)
        return self._pipe
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 6,
        guidance_scale: float = 1.0,
        seed: Optional[int] = None,
        model_name: str = "sdxl-turbo"
    ) -> str:
        """
        Generate an image based on the given parameters.
        
        Returns:
            str: Filename of the generated image
        """
        try:
            start_time = time.time()
            logger.info(f"Starting image generation with model: {model_name}")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Parameters: {width}x{height}, steps={num_inference_steps}, guidance={guidance_scale}")
            
            # Clamp dimensions to multiples of 8
            w = multiple_of_8(width)
            h = multiple_of_8(height)
            
            # Adjust parameters for SDXL-Turbo
            steps = max(1, min(num_inference_steps, 24))
            guidance = max(0.5, min(guidance_scale, 2.0))
            
            # Load the pipeline
            model_path = self.default_model_path if model_name == "sdxl-turbo" else model_name
            pipe = self._load_pipeline(model_path, "lcm")
            
            # Set up generator for reproducibility
            device, _ = self._get_device_info()
            generator = None
            if seed is not None:
                if device == "cuda":
                    generator = torch.Generator(device="cuda").manual_seed(seed)
                else:
                    generator = torch.Generator(device="cpu").manual_seed(seed)
            
            # Run generation in executor to avoid blocking
            def _generate():
                return pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt or None,
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=w,
                    height=h,
                    generator=generator,
                )
            
            # Execute generation asynchronously
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _generate)
            
            # Save the generated image
            img = result.images[0]
            output_path = save_image(img, prefix="sdxl_turbo")
            
            generation_time = time.time() - start_time
            logger.info(f"Image generated successfully in {generation_time:.2f}s: {output_path.name}")
            return output_path.name
            
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Return list of available models"""
        return self.available_models
    
    def set_seed(self, seed: Optional[int] = None) -> int:
        """Set random seed for reproducibility"""
        if seed is None:
            seed = int(datetime.now().timestamp())
        return seed