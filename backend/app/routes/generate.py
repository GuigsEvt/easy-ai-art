from fastapi import APIRouter, HTTPException
from app.core.generation import GenerationRequest, GenerationResponse, ImageToImageRequest
from app.core.pipeline import ImagePipeline
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the image generation pipeline
pipeline = ImagePipeline()

@router.post("/generate", response_model=GenerationResponse)
async def generate_image(request: GenerationRequest):
    """
    Generate an AI image based on the provided prompt and parameters.
    """
    try:
        start_time = time.time()
        
        # Log all generation parameters
        print("=" * 60)
        print("🎨 NEW GENERATION REQUEST (NON-STREAMING)")
        print("=" * 60)
        print(f"📝 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        print(f"❌ Negative Prompt: {request.negative_prompt or 'None'}")
        print(f"📐 Dimensions: {request.width}x{request.height}")
        print(f"🔢 Inference Steps: {request.num_inference_steps}")
        print(f"� Guidance Scale: {request.guidance_scale}")
        print(f"�🌱 Seed: {request.seed or 'Random'}")
        print(f"🤖 Model: {request.model_name}")
        print(f"⚙️ Sampler: {request.sampler}")
        print("=" * 60)
        
        # Generate the image using the pipeline
        image_filename = await pipeline.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            model_name=request.model_name,
            sampler=request.sampler
        )
        
        generation_time = time.time() - start_time
        
        return GenerationResponse(
            success=True,
            image_url=f"/images/{image_filename}",
            message="Image generated successfully",
            filename=image_filename,
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@router.post("/generate-img2img", response_model=GenerationResponse)
async def generate_img2img(request: ImageToImageRequest):
    """
    Generate an AI image from an input image and prompt (image-to-image).
    """
    try:
        start_time = time.time()
        
        # Log all generation parameters
        print("=" * 60)
        print("🎨 NEW IMG2IMG GENERATION REQUEST")
        print("=" * 60)
        print(f"📝 Prompt: {request.prompt[:100]}{'...' if len(request.prompt) > 100 else ''}")
        print(f"❌ Negative Prompt: {request.negative_prompt or 'None'}")
        print(f"💪 Strength: {request.strength}")
        print(f"🔢 Inference Steps: {request.num_inference_steps}")
        print(f"🧭 Guidance Scale: {request.guidance_scale}")
        print(f"🌱 Seed: {request.seed or 'Random'}")
        print(f"🤖 Model: {request.model_name}")
        print(f"⚙️ Sampler: {request.sampler}")
        print("=" * 60)
        
        # Generate the image using the pipeline
        image_filename = await pipeline.generate_img2img(
            prompt=request.prompt,
            image_data=request.image_data,
            negative_prompt=request.negative_prompt,
            strength=request.strength,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            model_name=request.model_name,
            sampler=request.sampler
        )
        
        generation_time = time.time() - start_time
        
        return GenerationResponse(
            success=True,
            image_url=f"/images/{image_filename}",
            message="Image generated successfully via img2img",
            filename=image_filename,
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"Error generating img2img: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")