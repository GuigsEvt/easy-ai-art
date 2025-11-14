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
                }
                
                # Conditional guidance (use appropriate parameter for each model type)
                if self._is_qwen_model(model_name):
                    generation_args["true_cfg_scale"] = guidance_scale  # Use the original guidance_scale value for Qwen
                    print(f"Using Qwen model with true_cfg_scale={guidance_scale}")
                else:
                    generation_args["guidance_scale"] = guidance
                    print(f"Using standard model with guidance_scale={guidance}")
                
                # Conditional callback setup
                if progress_callback:  # Only add if callback is needed
                    current_step = [0]  # Mutable for closure

                    def progress_wrapper(*args, **kwargs):
                        """Unified wrapper to adapt callback signatures."""
                        # Handle different argument patterns from diffusion libraries
                        print(f"DEBUG: async progress_wrapper called with args: {[type(arg).__name__ for arg in args]}")
                        
                        # Extract step index safely - different models pass different signatures
                        step_idx = 0
                        timestep = None
                        
                        # Check if first argument is an integer (step index)
                        if len(args) > 0 and isinstance(args[0], int):
                            step_idx = args[0]
                            timestep = args[1] if len(args) > 1 else None
                        elif 'step' in kwargs:
                            # Try to get step from kwargs
                            step_idx = kwargs.get('step', 0)
                            timestep = kwargs.get('timestep', None)
                        else:
                            # Fallback: look for any integer in the args
                            for arg in args:
                                if isinstance(arg, int):
                                    step_idx = arg
                                    break
                            if step_idx == 0:
                                # Use internal step counter as fallback
                                current_step[0] += 1
                                step_idx = current_step[0] - 1
                        
                        # Ensure step_idx is valid
                        if not isinstance(step_idx, int):
                            step_idx = current_step[0]
                        
                        current_step[0] = step_idx + 1  # step_idx starts at 0
                        stage_msg = f"Generating (step {current_step[0]}/{steps})"
                        progress_callback(current_step[0], steps, stage_msg)

                    if self._is_qwen_model(model_name):
                        # Qwen: Use callback_on_step_end (newer API)
                        generation_args["callback_on_step_end"] = progress_wrapper
                        generation_args["callback_on_step_end_tensor_inputs"] = ["latents"]  # Optional: passes latents if needed
                    else:
                        # SDXL/etc.: Use legacy callback
                        def legacy_callback(step, timestep, latents):
                            current_step[0] = step + 1
                            progress_callback(current_step[0], steps, f"Generating (step {current_step[0]}/{steps})")

                        generation_args["callback"] = legacy_callback
                        generation_args["callback_steps"] = 1
                
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
            }
            
            # Conditional guidance (use appropriate parameter for each model type)
            if self._is_qwen_model(model_name):
                generation_args["true_cfg_scale"] = guidance_scale  # Use the original guidance_scale value for Qwen
                print(f"Using Qwen model with true_cfg_scale={guidance_scale}")
            else:
                generation_args["guidance_scale"] = guidance
                print(f"Using standard model with guidance_scale={guidance}")
            
            # Conditional callback setup
            if progress_callback or diffusion_callback:  # Only add if callback is needed
                current_step = [0]  # Mutable for closure

                def progress_wrapper(*args, **kwargs):
                    """Unified wrapper to adapt callback signatures."""
                    # Handle different argument patterns from diffusion libraries
                    # For debugging - log what we're actually receiving
                    print(f"DEBUG: progress_wrapper called with args: {[type(arg).__name__ for arg in args]}")
                    
                    # Extract step index safely - different models pass different signatures
                    step_idx = 0
                    timestep = None
                    callback_kwargs = None
                    latents = None
                    
                    # Check if first argument is an integer (step index)
                    if len(args) > 0 and isinstance(args[0], int):
                        step_idx = args[0]
                        timestep = args[1] if len(args) > 1 else None
                        callback_kwargs = args[2] if len(args) > 2 else kwargs.get('callback_kwargs', None)
                        latents = args[3] if len(args) > 3 else kwargs.get('latents', None)
                    elif 'step' in kwargs:
                        # Try to get step from kwargs
                        step_idx = kwargs.get('step', 0)
                        timestep = kwargs.get('timestep', None)
                        callback_kwargs = kwargs.get('callback_kwargs', None)
                        latents = kwargs.get('latents', None)
                    else:
                        # Fallback: assume we're being called in an unexpected way
                        # Look for any integer in the args or use current_step counter
                        for arg in args:
                            if isinstance(arg, int):
                                step_idx = arg
                                break
                        if step_idx == 0:
                            # Use internal step counter as fallback
                            current_step[0] += 1
                            step_idx = current_step[0] - 1
                    
                    # Ensure step_idx is valid
                    if not isinstance(step_idx, int):
                        step_idx = current_step[0]
                    
                    current_step[0] = step_idx + 1  # step_idx starts at 0
                    stage_msg = f"Generating (step {current_step[0]}/{steps})"
                    if progress_callback:
                        progress_callback(current_step[0], steps, stage_msg)
                    if diffusion_callback:
                        # Try to call with the expected signature (step, timestep, latents)
                        try:
                            if latents is not None:
                                diffusion_callback(step_idx, timestep, latents)
                            else:
                                diffusion_callback(step_idx, timestep, callback_kwargs)
                        except TypeError:
                            # Fallback to just step_idx and timestep
                            try:
                                diffusion_callback(step_idx, timestep)
                            except TypeError:
                                # Last fallback - just step_idx
                                diffusion_callback(step_idx)

                if self._is_qwen_model(model_name):
                    # Qwen: Use callback_on_step_end (newer API)
                    generation_args["callback_on_step_end"] = progress_wrapper
                    generation_args["callback_on_step_end_tensor_inputs"] = ["latents"]  # Optional: passes latents if needed
                else:
                    # SDXL/etc.: Use legacy callback
                    def legacy_callback(step, timestep, latents):
                        current_step[0] = step + 1
                        if progress_callback:
                            progress_callback(current_step[0], steps, f"Generating (step {current_step[0]}/{steps})")
                        if diffusion_callback:
                            diffusion_callback(step, timestep, latents)

                    generation_args["callback"] = legacy_callback
                    generation_args["callback_steps"] = 1
                
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