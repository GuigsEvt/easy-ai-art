#!/usr/bin/env python3
import argparse
import os
import platform
import time
import json
from pathlib import Path
from typing import Literal

import torch
from PIL import Image
from diffusers import (
    AutoPipelineForText2Image,
    EulerAncestralDiscreteScheduler,
    DDIMScheduler,
    DPMSolverMultistepScheduler,
    LCMScheduler,
    EulerDiscreteScheduler,
    FlowMatchEulerDiscreteScheduler
)

# Try to import QwenImagePipeline - it might not be available in all diffusers versions
try:
    from diffusers import QwenImagePipeline
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False
    print("Warning: QwenImagePipeline not available in this diffusers version")

# ---------- Config ----------
# Get the backend directory path
backend_dir = Path(__file__).parent.parent.parent
OUTPUT_DIR = backend_dir / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default model path (relative to backend directory)
DEFAULT_MODEL_PATH = "./backend/models/sdxl-turbo"

SAMPLERS = {
    "euler_a": EulerAncestralDiscreteScheduler,
    "euler": EulerDiscreteScheduler,
    "ddim": DDIMScheduler,
    "dpmpp_2m": DPMSolverMultistepScheduler,
    "dpmpp_2m_karras": DPMSolverMultistepScheduler,
    "lcm": LCMScheduler,
}

def detect_device():
    # Priorité: CUDA > MPS > CPU
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if platform.system() == "Darwin" and torch.backends.mps.is_available():        
        return "mps", torch.float32
    return "cpu", torch.float32

def multiple_of_8(x: int) -> int:
    return max(256, (x // 8) * 8)

def build_pipe(model_path: str, sampler: str, device: str, dtype):
    # ensure it's a real local directory with a model_index.json
    mp = Path(model_path)
    idx = mp / "model_index.json"
    if not idx.exists():
        raise FileNotFoundError(f"model_index.json not found at: {idx.resolve()}")

    # Check if this is a Qwen model by examining model_index.json
    is_qwen_model = False
    try:
        with open(idx, 'r') as f:
            model_config = json.load(f)
            if model_config.get("_class_name") == "QwenImagePipeline":
                is_qwen_model = True
                print(f"Detected Qwen model at {mp}")
    except Exception as e:
        print(f"Warning: Could not read model_index.json: {e}")

    # offline / local only
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    # Load the appropriate pipeline based on model type
    if is_qwen_model:
        if not QWEN_AVAILABLE:
            raise ImportError("QwenImagePipeline is required but not available. Please update diffusers: pip install diffusers>=0.34.0")
        
        print("Loading QwenImagePipeline...")
        pipe = QwenImagePipeline.from_pretrained(
            str(mp),            
            torch_dtype=torch.float32,
            use_safetensors=True,
            local_files_only=True,
            trust_remote_code=False,
        )
        pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        # Qwen uses different scheduler handling, skip custom scheduler for now
        print("Note: Custom scheduler selection not supported for Qwen models yet")
        
    else:
        # Standard SDXL/diffusion model
        pipe = AutoPipelineForText2Image.from_pretrained(
            str(mp),
            torch_dtype=dtype,
            use_safetensors=True,
            local_files_only=True,
            trust_remote_code=False,
        )
        
        # Replace the scheduler (sampler) for non-Qwen models
        if sampler in SAMPLERS:
            if sampler == "dpmpp_2m_karras":
                # Use DPM++ 2M with Karras noise schedule
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                    pipe.scheduler.config,
                    use_karras_sigmas=True,
                    algorithm_type="dpmsolver++",
                    solver_order=2
                )
            else:
                pipe.scheduler = SAMPLERS[sampler].from_config(pipe.scheduler.config)

    pipe = pipe.to(device)

    # Petites optimisations mémoire pour MPS/CPU
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    return pipe

def save_image(img: Image.Image, model_name: str = "sdxl", sampler: str = "turbo") -> Path:
    ts = int(time.time() * 1000)
    # Clean up model name for filename (remove any path separators)
    clean_model_name = model_name.replace("/", "_").replace("\\", "_")
    out_path = OUTPUT_DIR / f"{clean_model_name}_{sampler}_{ts}.png"
    img.save(out_path)
    return out_path

def main():
    parser = argparse.ArgumentParser(description="SDXL-Turbo text-to-image")
    parser.add_argument("--prompt", required=True, help="Positive prompt")
    parser.add_argument("--negative", default="", help="Negative prompt")
    parser.add_argument("--steps", type=int, default=6, help="Number of inference steps")
    parser.add_argument(
        "--sampler",
        choices=list(SAMPLERS.keys()),
        default="lcm",
        help="Sampler / scheduler",
    )
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--guidance", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_PATH,
        help='HF repo id ("stabilityai/sdxl-turbo") ou chemin local ("./backend/models/sdxl-turbo")',
    )
    args = parser.parse_args()

    device, dtype = detect_device()
    print(f"[Device] {device} | dtype={dtype}")

    # Clamp / ajuster dims pour %8
    w = multiple_of_8(args.width)
    h = multiple_of_8(args.height)

    pipe = build_pipe(args.model, args.sampler, device, dtype)

    # SDXL-Turbo aime peu d’étapes & faible guidance
    steps = max(1, min(args.steps, 24))  # éviter des steps trop grands
    guidance = max(0.5, min(args.guidance, 2.0))

    # Générateur (seed)
    if device == "cuda":
        generator = torch.Generator(device="cuda").manual_seed(args.seed) if args.seed is not None else None
    else:
        generator = torch.Generator(device="cpu").manual_seed(args.seed) if args.seed is not None else None

    print(f"[Run] sampler={args.sampler} steps={steps} guidance={guidance} size={w}x{h}")
    try:
        out = pipe(
            prompt=args.prompt,
            negative_prompt=args.negative or None,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=w,
            height=h,
            generator=generator,
        )
    except Exception as e:
        raise SystemExit(f"Generation failed: {e}")

    img = out.images[0]
    # Extract model name from path for filename
    model_name_for_file = os.path.basename(args.model) if args.model else "sdxl"
    out_path = save_image(img, model_name=model_name_for_file, sampler=args.sampler)
    print(f"[OK] saved → {out_path}")

if __name__ == "__main__":
    main()