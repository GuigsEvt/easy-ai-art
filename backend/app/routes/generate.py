from fastapi import APIRouter, HTTPException
from app.models.generation import GenerationRequest, GenerationResponse
from app.core.pipeline import ImagePipeline
import logging

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
        logger.info(f"Generating image with prompt: {request.prompt}")
        
        # Generate the image using the pipeline
        image_path = await pipeline.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            model_name=request.model_name
        )
        
        return GenerationResponse(
            success=True,
            image_url=f"/images/{image_path}",
            message="Image generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@router.get("/models")
async def list_available_models():
    """
    List all available AI models for image generation.
    """
    try:
        models = pipeline.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")