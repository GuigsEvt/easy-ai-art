import os
import logging
from typing import Optional, List, Callable
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
        # Get the backend directory path (where this file is located)
        backend_dir = Path(__file__).parent.parent.parent
        self.models_dir = backend_dir / "models"
        self.outputs_dir = backend_dir / "outputs"
        self.available_models = [
            "sdxl-turbo",      # Local model we have available
            "sdxl-base-1.0",   # SDXL Base model
            "qwen-image"       # Qwen Image model
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
    
    def _is_qwen_model(self, model_name: str) -> bool:
        """Check if the model is a Qwen model based on model name"""
        return model_name.lower() in ["qwen-image", "qwen"]
    
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
        model_name: str = "sdxl-turbo",
        sampler: str = "lcm",
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Generate an image based on the given parameters.
        
        Args:
            progress_callback: Optional callback function called with (current_step, total_steps, stage)
        
        Returns:
            str: Filename of the generated image
        """
        try:
            start_time = time.time()
            print(f"Starting image generation with model: {model_name}")
            print(f"Prompt: {prompt}")
            
            # Use dynamic guidance scale from frontend
            print(f"Parameters: {width}x{height}, steps={num_inference_steps}, guidance={guidance_scale}, sampler={sampler}")
            
            # Clamp dimensions to multiples of 8
            w = multiple_of_8(width)
            h = multiple_of_8(height)
            
            # Adjust parameters for SDXL-Turbo
            steps = max(1, min(num_inference_steps, 24))
            guidance = max(0.5, min(guidance_scale, 2.0))
            
            # Progress callback for loading model
            if progress_callback:
                progress_callback(0, steps, "Loading model")
            
            model_path = f"models/{model_name}"
            
            # Check if model exists
            model_index_path = os.path.join(model_path, "model_index.json")
            if not os.path.exists(model_index_path):
                raise FileNotFoundError(f"model_index.json not found at: {os.path.abspath(model_index_path)}")
            
            pipe = self._load_pipeline(model_path, sampler)
            
            # Progress callback for preparing
            if progress_callback:
                progress_callback(0, steps, "Preparing generation")
            
            # Set up generator for reproducibility
            device, _ = self._get_device_info()
            generator = None
            if seed is not None:
                if device == "cuda":
                    generator = torch.Generator(device="cuda").manual_seed(seed)
                else:
                    generator = torch.Generator(device="cpu").manual_seed(seed)
            
            # Create a custom callback wrapper for diffusers progress
            current_step = [0]  # Use list to allow modification in nested function
            
            def diffusion_callback(step, timestep, latents):
                current_step[0] = step + 1
                if progress_callback:
                    progress_callback(current_step[0], steps, f"Generating (step {current_step[0]}/{steps})")
            
            # Run generation in executor to avoid blocking
            def _generate():
                # Prepare generation arguments based on model type
                generation_args = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt or None,
                    "num_inference_steps": steps,
                    "width": w,
                    "height": h,
                    "generator": generator,
                    "callback": diffusion_callback,
                    "callback_steps": 1,  # Call callback after each step
                }
                
                # Use different guidance parameter for Qwen models
                if self._is_qwen_model(model_name):
                    generation_args["true_cfg_scale"] = 4.0
                    print(f"Using Qwen model with true_cfg_scale=4.0")
                else:
                    generation_args["guidance_scale"] = guidance
                    print(f"Using standard model with guidance_scale={guidance}")
                
                return pipe(**generation_args)
            
            # Execute generation asynchronously
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _generate)
            
            # Progress callback for post-processing
            if progress_callback:
                progress_callback(steps, steps, "Post-processing")
            
            # Save the generated image
            img = result.images[0]
            output_path = save_image(img, model_name=model_name, sampler=sampler)
            
            # Final completion callback
            if progress_callback:
                progress_callback(steps, steps, "Completed")
            
            generation_time = time.time() - start_time
            logger.info(f"Image generated successfully in {generation_time:.2f}s: {output_path.name}")
            return output_path.name
            
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            raise
    
    async def generate_with_sync_callback(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 6,
        guidance_scale: float = 1.0,
        seed: Optional[int] = None,
        model_name: str = "sdxl-turbo",
        sampler: str = "lcm",
        diffusion_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Generate an image with sync-compatible callbacks for threading.
        
        Args:
            diffusion_callback: Callback for diffusion steps (step, timestep, latents)
            progress_callback: Progress callback function called with (current_step, total_steps, stage)
        
        Returns:
            str: Filename of the generated image
        """
        try:
            start_time = time.time()
            print(f"Starting threaded image generation with model: {model_name}")
            print(f"Prompt: {prompt}")

            # Use dynamic values from frontend instead of hardcoded values
            print(f"Parameters: {width}x{height}, steps={num_inference_steps}, guidance={guidance_scale}, sampler={sampler}")
            
            # Clamp dimensions to multiples of 8
            w = multiple_of_8(width)
            h = multiple_of_8(height)
            
            # Adjust parameters for SDXL-Turbo
            steps = num_inference_steps
            guidance = guidance_scale
            
            # Progress callback for loading model
            if progress_callback:
                progress_callback(0, steps, "Loading model")
            
            # Load the pipeline
            model_path = f"models/{model_name}"
            
            # Check if model exists
            model_index_path = os.path.join(model_path, "model_index.json")
            if not os.path.exists(model_index_path):
                raise FileNotFoundError(f"model_index.json not found at: {os.path.abspath(model_index_path)}")
            
            pipe = self._load_pipeline(model_path, sampler)
            
            # Progress callback for preparing
            if progress_callback:
                progress_callback(0, steps, "Preparing generation")
            
            # Set up generator for reproducibility
            device, _ = self._get_device_info()
            generator = None
            if seed is not None:
                if device == "cuda":
                    generator = torch.Generator(device="cuda").manual_seed(seed)
                else:
                    generator = torch.Generator(device="cpu").manual_seed(seed)
            
            # Run generation synchronously in this thread
            # Prepare generation arguments based on model type
            generation_args = {
                "prompt": prompt,
                "negative_prompt": negative_prompt or None,
                "num_inference_steps": steps,
                "width": w,
                "height": h,
                "generator": generator,
                "callback": diffusion_callback if diffusion_callback else None,
                "callback_steps": 1 if diffusion_callback else None,
            }
            
            # Use different guidance parameter for Qwen models
            if self._is_qwen_model(model_name):
                generation_args["true_cfg_scale"] = 4.0
                print(f"Using Qwen model with true_cfg_scale=4.0")
            else:
                generation_args["guidance_scale"] = guidance
                print(f"Using standard model with guidance_scale={guidance}")
                
            result = pipe(**generation_args)
            
            # Progress callback for post-processing
            if progress_callback:
                progress_callback(steps, steps, "Post-processing")
            
            # Save the generated image
            img = result.images[0]
            output_path = save_image(img, model_name=model_name, sampler=sampler)
            
            # Final completion callback
            if progress_callback:
                progress_callback(steps, steps, "Completed")
            
            generation_time = time.time() - start_time
            print(f"Threaded image generated successfully in {generation_time:.2f}s: {output_path.name}")
            return output_path.name
            
        except Exception as e:
            print(f"Error in threaded image generation: {str(e)}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Return list of available models"""
        return self.available_models
    
    def set_seed(self, seed: Optional[int] = None) -> int:
        """Set random seed for reproducibility"""
        if seed is None:
            seed = int(datetime.now().timestamp())
        return seed