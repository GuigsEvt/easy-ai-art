from fastapi import APIRouter, HTTPException
from app.models.generation import GenerationRequest, GenerationResponse
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
        logger.info(f"Generating image with prompt: {request.prompt}")
        
        # Generate the image using the pipeline
        image_filename = await pipeline.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
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