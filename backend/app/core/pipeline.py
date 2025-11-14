import os
import logging
from typing import Optional, List, Callable
import asyncio
from datetime import datetime
from pathlib import Path
import torch
import time

from .text2image import build_pipe, detect_device, multiple_of_8, save_image, SAMPLERS

logger = logging.getLogger(__name__)

class ImagePipeline:
    """
    Image generation pipeline using diffusion models with SDXL-Turbo and Qwen-Image.
    """

    def __init__(self):
        backend_dir = Path(__file__).parent.parent.parent
        self.models_dir = backend_dir / "models"
        self.outputs_dir = backend_dir / "outputs"
        self.available_models = [
            "sdxl-turbo",
            "sdxl-base-1.0",
            "qwen-image"
        ]
        self._ensure_directories()
        self._device = None
        self._dtype = None
        self._pipe = None

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

    def _load_pipeline(self, model_path: str, sampler: str = "lcm"):
        if self._pipe is None:
            device, dtype = self._get_device_info()
            self._pipe = build_pipe(model_path, sampler, device, dtype)
        return self._pipe

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
                latents = callback_kwargs.get("latents")
                timestep = callback_kwargs.get("timestep")

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
        print(f"[Async] Generating with {model_name} – prompt: {prompt!r}")

        # ----- parameter clamping -----
        w = multiple_of_8(width)
        h = multiple_of_8(height)
        steps = max(1, min(num_inference_steps, 24))          # SDXL-Turbo limit
        guidance = max(0.5, min(guidance_scale, 2.0))

        if progress_callback:
            progress_callback(0, steps, "Loading model")

        model_path = f"models/{model_name}"
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
        out_path = save_image(img, model_name=model_name, sampler=sampler)

        if progress_callback:
            progress_callback(steps, steps, "Completed")

        logger.info(f"Async generation finished in {time.time() - start_time:.2f}s → {out_path.name}")
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
        print(f"[Threaded] Generating with {model_name} – prompt: {prompt!r}")

        w = multiple_of_8(width)
        h = multiple_of_8(height)
        steps = num_inference_steps                     # no clamping for Qwen
        guidance = guidance_scale

        if progress_callback:
            progress_callback(0, steps, "Loading model")

        model_path = f"models/{model_name}"
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
        out_path = save_image(img, model_name=model_name, sampler=sampler)

        if progress_callback:
            progress_callback(steps, steps, "Completed")

        logger.info(f"Threaded generation finished in {time.time() - start_time:.2f}s → {out_path.name}")
        return out_path.name

    # --------------------------------------------------------------------- #
    # Misc
    # --------------------------------------------------------------------- #
    def get_available_models(self) -> List[str]:
        return self.available_models

    def set_seed(self, seed: Optional[int] = None) -> int:
        if seed is None:
            seed = int(datetime.now().timestamp())
        return seed