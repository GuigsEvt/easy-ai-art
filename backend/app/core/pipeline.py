import os
import logging
from typing import Optional, List, Callable
import asyncio
from datetime import datetime
from pathlib import Path
import torch
import time
import base64
import io
from PIL import Image

from .text2image import build_pipe, build_img2img_pipe, detect_device, multiple_of_8, save_image, SAMPLERS
from .model_detection import detect_model_type, is_text_to_image_model, is_image_to_image_model, get_recommended_model_for_task

logger = logging.getLogger(__name__)

class ImagePipeline:
    """
    Image generation pipeline using diffusion models with SDXL-Turbo and Qwen-Image.
    """

    def __init__(self):
        backend_dir = Path(__file__).parent.parent.parent
        self.models_dir = backend_dir / "models"
        self.outputs_dir = backend_dir / "outputs"
        self._ensure_directories()
        self._device = None
        self._dtype = None
        self._pipe = None
        self._img2img_pipe = None

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _ensure_directories(self):
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def _get_device_info(self):
        if self._device is None or self._dtype is None:
            self._device, self._dtype = detect_device()
        return self._device, self._dtype

    def _is_qwen_model(self, model_name: str) -> bool:
        return model_name.lower() in {"qwen-image", "qwen"}

    def _get_suitable_model_for_text2image(self, requested_model: str) -> str:
        """
        Get a suitable model for text-to-image generation.
        If the requested model is not suitable, find an alternative.
        """
        model_path = f"models/{requested_model}"
        
        # Check if requested model exists and is suitable for text-to-image
        if os.path.exists(model_path) and is_text_to_image_model(model_path):
            return requested_model
        
        # Try to find a suitable alternative
        suitable_model = get_recommended_model_for_task(str(self.models_dir), "text-to-image")
        
        if suitable_model:
            logger.warning(f"Model '{requested_model}' not suitable for text-to-image, using '{suitable_model}' instead")
            return suitable_model
        else:
            # Fallback to original model (might fail, but let it fail gracefully)
            logger.error(f"No suitable text-to-image model found, attempting with '{requested_model}'")
            return requested_model
    
    def _get_suitable_model_for_img2img(self, requested_model: str) -> str:
        """
        Get a suitable model for image-to-image generation.
        If the requested model is not suitable, find an alternative.
        """
        model_path = f"models/{requested_model}"
        
        # Check if requested model exists and is suitable for image-to-image
        if os.path.exists(model_path) and is_image_to_image_model(model_path):
            return requested_model
        
        # Try to find a suitable alternative
        suitable_model = get_recommended_model_for_task(str(self.models_dir), "image-to-image")
        
        if suitable_model:
            logger.warning(f"Model '{requested_model}' not suitable for image-to-image, using '{suitable_model}' instead")
            return suitable_model
        else:
            # For img2img, we can often use text-to-image models in img2img mode
            # Check if the requested model is at least a text-to-image model
            if os.path.exists(model_path) and is_text_to_image_model(model_path):
                logger.info(f"Using text-to-image model '{requested_model}' for image-to-image generation")
                return requested_model
            
            # Last resort: try to find any text-to-image model
            text2img_model = get_recommended_model_for_task(str(self.models_dir), "text-to-image")
            if text2img_model:
                logger.warning(f"No dedicated img2img model found, using text-to-image model '{text2img_model}' instead")
                return text2img_model
            
            # Fallback to original model (might fail, but let it fail gracefully)
            logger.error(f"No suitable model found for image-to-image, attempting with '{requested_model}'")
            return requested_model

    def _load_pipeline(self, model_path: str, sampler: str = "lcm"):
        if self._pipe is None:
            device, dtype = self._get_device_info()
            self._pipe = build_pipe(model_path, sampler, device, dtype)
        return self._pipe
    
    def _load_img2img_pipeline(self, model_path: str, sampler: str = "euler_a"):
        if self._img2img_pipe is None:
            device, dtype = self._get_device_info()
            self._img2img_pipe = build_img2img_pipe(model_path, sampler, device, dtype)
        return self._img2img_pipe
    
    def _decode_base64_image(self, image_data: str) -> Image.Image:
        """Decode base64 image string to PIL Image"""
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            return image
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")

    # --------------------------------------------------------------------- #
    # Unified callback wrapper (works for both pipelines)
    # --------------------------------------------------------------------- #
    def _make_progress_wrapper(
        self,
        steps: int,
        progress_callback: Optional[Callable[[int, int, str], None]],
        diffusion_callback: Optional[Callable] = None,
    ) -> Callable:
        """Return a callback that works for SDXL (legacy) **and** Qwen (callback_on_step_end)."""
        current_step = [0]                     # mutable for closure

        def wrapper(*args, **kwargs):
            # ---------- Qwen: (pipeline, step, callback_kwargs) ----------
            if len(args) >= 2 and hasattr(args[0], "transformer"):   # rough pipeline check
                pipeline, step_idx = args[0], args[1]
                callback_kwargs = args[2] if len(args) > 2 else kwargs.get("callback_kwargs", {})
                
                # Safely extract values from callback_kwargs - it should be a dict
                latents = None
                timestep = None
                if isinstance(callback_kwargs, dict):
                    latents = callback_kwargs.get("latents")
                    timestep = callback_kwargs.get("timestep")
                else:
                    # If callback_kwargs is not a dict, reset it to empty dict
                    callback_kwargs = {}

            # ---------- SDXL / legacy: (step, timestep, latents) ----------
            elif len(args) >= 1 and isinstance(args[0], int):
                step_idx = args[0]
                timestep = args[1] if len(args) > 1 else None
                latents = args[2] if len(args) > 2 else None
                callback_kwargs = {}

            # ---------- Fallback via kwargs ----------
            elif "step" in kwargs:
                step_idx = kwargs["step"]
                timestep = kwargs.get("timestep")
                latents = kwargs.get("latents")
                callback_kwargs = {}
            else:
                # extreme fallback – just count up
                current_step[0] += 1
                step_idx = current_step[0] - 1
                timestep = latents = None
                callback_kwargs = {}

            # update mutable counter (used for the UI)
            current_step[0] = step_idx + 1
            stage = f"Generating (step {current_step[0]}/{steps})"

            if progress_callback:
                progress_callback(current_step[0], steps, stage)

            if diffusion_callback:
                try:
                    diffusion_callback(step_idx, timestep, latents)
                except Exception:
                    try:
                        diffusion_callback(step_idx, timestep)
                    except Exception:
                        diffusion_callback(step_idx)

            # Qwen **requires** the callback to return the kwargs dict
            return callback_kwargs

        return wrapper

    # --------------------------------------------------------------------- #
    # Async generation (used by FastAPI / websockets)
    # --------------------------------------------------------------------- #
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
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> str:
        start_time = time.time()
        
        # Get suitable model for text-to-image generation
        actual_model = self._get_suitable_model_for_text2image(model_name)
        print(f"[Async] Generating with {actual_model} – prompt: {prompt!r}")

        # ----- parameter clamping -----
        w = multiple_of_8(width)
        h = multiple_of_8(height)
        steps = max(1, min(num_inference_steps, 24))          # SDXL-Turbo limit
        guidance = max(0.5, min(guidance_scale, 2.0))

        if progress_callback:
            progress_callback(0, steps, "Loading model")

        model_path = f"models/{actual_model}"
        if not os.path.exists(os.path.join(model_path, "model_index.json")):
            raise FileNotFoundError(f"model_index.json missing in {model_path}")

        pipe = self._load_pipeline(model_path, sampler)

        if progress_callback:
            progress_callback(0, steps, "Preparing generation")

        # ----- seed -----
        device, _ = self._get_device_info()
        generator = None
        if seed is not None:
            gen_cls = torch.Generator(device="cuda" if device == "cuda" else "cpu")
            generator = gen_cls.manual_seed(seed)

        # ----- generation (runs in thread pool) -----
        def _generate():
            gen_args = {
                "prompt": prompt,
                "negative_prompt": negative_prompt or None,
                "num_inference_steps": steps,
                "width": w,
                "height": h,
                "generator": generator,
            }

            # guidance
            if self._is_qwen_model(model_name):
                gen_args["true_cfg_scale"] = guidance_scale
            else:
                gen_args["guidance_scale"] = guidance

            # progress callback
            if progress_callback:
                wrapper = self._make_progress_wrapper(steps, progress_callback)
                if self._is_qwen_model(model_name):
                    gen_args["callback_on_step_end"] = wrapper
                    # gen_args["callback_on_step_end_tensor_inputs"] = ["latents"]
                else:
                    # legacy signature – wrapper still works
                    gen_args["callback"] = wrapper
                    gen_args["callback_steps"] = 1

            return pipe(**gen_args)

        result = await asyncio.get_event_loop().run_in_executor(None, _generate)

        # ----- post-processing -----
        if progress_callback:
            progress_callback(steps, steps, "Post-processing")

        img = result.images[0]
        out_path = save_image(img, model_name=actual_model, sampler=sampler)

        if progress_callback:
            progress_callback(steps, steps, "Completed")

        logger.info(f"Async generation finished in {time.time() - start_time:.2f}s → {out_path.name}")
        return out_path.name

    # --------------------------------------------------------------------- #
    # Image-to-Image generation
    # --------------------------------------------------------------------- #
    async def generate_img2img(
        self,
        prompt: str,
        image_data: str,
        negative_prompt: Optional[str] = None,
        strength: float = 0.75,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        model_name: str = "sdxl-base-1.0",
        sampler: str = "euler_a",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> str:
        start_time = time.time()
        
        # Get suitable model for image-to-image generation
        actual_model = self._get_suitable_model_for_img2img(model_name)
        print(f"[Async IMG2IMG] Generating with {actual_model} – prompt: {prompt!r}")

        # Decode input image
        if progress_callback:
            progress_callback(0, num_inference_steps, "Decoding input image")
        
        input_image = self._decode_base64_image(image_data)
        
        # Parameter validation
        steps = max(1, min(num_inference_steps, 50))
        strength = max(0.1, min(strength, 1.0))
        guidance = max(0.1, min(guidance_scale, 20.0))

        if progress_callback:
            progress_callback(0, steps, "Loading img2img model")

        model_path = f"models/{actual_model}"
        if not os.path.exists(os.path.join(model_path, "model_index.json")):
            raise FileNotFoundError(f"model_index.json missing in {model_path}")

        pipe = self._load_img2img_pipeline(model_path, sampler)

        if progress_callback:
            progress_callback(0, steps, "Preparing img2img generation")

        # Seed
        device, _ = self._get_device_info()
        generator = None
        if seed is not None:
            gen_cls = torch.Generator(device="cuda" if device == "cuda" else "cpu")
            generator = gen_cls.manual_seed(seed)

        # Generation (runs in thread pool)
        def _generate_img2img():
            gen_args = {
                "prompt": prompt,
                "image": input_image,
                "negative_prompt": negative_prompt or None,
                "num_inference_steps": steps,
                "strength": strength,
                "guidance_scale": guidance,
                "generator": generator,
            }

            # Progress callback
            if progress_callback:
                wrapper = self._make_progress_wrapper(steps, progress_callback)
                gen_args["callback"] = wrapper
                gen_args["callback_steps"] = 1

            return pipe(**gen_args)

        result = await asyncio.get_event_loop().run_in_executor(None, _generate_img2img)

        # Post-processing
        if progress_callback:
            progress_callback(steps, steps, "Post-processing")

        img = result.images[0]
        out_path = save_image(img, model_name=actual_model, sampler=f"{sampler}_img2img")

        if progress_callback:
            progress_callback(steps, steps, "Completed")

        logger.info(f"Async img2img generation finished in {time.time() - start_time:.2f}s → {out_path.name}")
        return out_path.name

    # --------------------------------------------------------------------- #
    # Thread-safe generation (for sync endpoints)
    # --------------------------------------------------------------------- #
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
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> str:
        start_time = time.time()
        
        # Get suitable model for text-to-image generation
        actual_model = self._get_suitable_model_for_text2image(model_name)
        print(f"[Threaded] Generating with {actual_model} – prompt: {prompt!r}")

        w = multiple_of_8(width)
        h = multiple_of_8(height)
        steps = num_inference_steps                     # no clamping for Qwen
        guidance = guidance_scale

        if progress_callback:
            progress_callback(0, steps, "Loading model")

        model_path = f"models/{actual_model}"
        if not os.path.exists(os.path.join(model_path, "model_index.json")):
            raise FileNotFoundError(f"model_index.json missing in {model_path}")

        pipe = self._load_pipeline(model_path, sampler)

        if progress_callback:
            progress_callback(0, steps, "Preparing generation")

        device, _ = self._get_device_info()
        generator = None
        if seed is not None:
            gen_cls = torch.Generator(device="cuda" if device == "cuda" else "cpu")
            generator = gen_cls.manual_seed(seed)

        # ----- build args -----
        gen_args = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or None,
            "num_inference_steps": steps,
            "width": w,
            "height": h,
            "generator": generator,
        }

        if self._is_qwen_model(model_name):
            gen_args["true_cfg_scale"] = guidance_scale
        else:
            gen_args["guidance_scale"] = guidance

        # ----- callbacks -----
        if progress_callback or diffusion_callback:
            wrapper = self._make_progress_wrapper(steps, progress_callback, diffusion_callback)
            if self._is_qwen_model(model_name):
                gen_args["callback_on_step_end"] = wrapper
                # gen_args["callback_on_step_end_tensor_inputs"] = ["latents"]
            else:
                gen_args["callback"] = wrapper
                gen_args["callback_steps"] = 1

        # ----- run (blocking) -----
        result = pipe(**gen_args)

        if progress_callback:
            progress_callback(steps, steps, "Post-processing")

        img = result.images[0]
        out_path = save_image(img, model_name=actual_model, sampler=sampler)

        if progress_callback:
            progress_callback(steps, steps, "Completed")

        logger.info(f"Threaded generation finished in {time.time() - start_time:.2f}s → {out_path.name}")
        return out_path.name

    # --------------------------------------------------------------------- #
    # Misc
    # --------------------------------------------------------------------- #
    def set_seed(self, seed: Optional[int] = None) -> int:
        if seed is None:
            seed = int(datetime.now().timestamp())
        return seed