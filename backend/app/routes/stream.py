from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.generation import GenerationRequest
from app.core.pipeline import ImagePipeline
import logging
import json
import asyncio
import queue
import threading
import concurrent.futures
import time
from typing import AsyncGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the image generation pipeline
pipeline = ImagePipeline()

async def generate_with_progress(request: GenerationRequest) -> AsyncGenerator[str, None]:
    """
    Generate an image with progress updates streamed as Server-Sent Events
    """
    try:
        start_time = time.time()
        logger.info(f"Starting streaming generation with prompt: {request.prompt}")
        
        # Use a thread-safe queue for communication between threads
        progress_queue_sync = queue.Queue()
        generation_complete = threading.Event()
        generation_error = threading.Event()
        
        # Send initial progress
        yield f"data: {json.dumps({'type': 'progress', 'progress': 0, 'stage': 'Initializing', 'step': 0, 'total_steps': request.num_inference_steps or 6})}\n\n"
        
        # Create progress callback that puts updates in thread-safe queue
        def progress_callback(step: int, total_steps: int, stage: str):
            progress_data = {
                'step': step,
                'total_steps': total_steps,
                'stage': stage,
                'progress': 0
            }
            
            # Calculate progress percentage
            if stage == "Loading model":
                progress_data['progress'] = 5
            elif stage == "Preparing generation":
                progress_data['progress'] = 10
            elif stage.startswith("Generating"):
                # 10% to 90% based on generation steps
                progress_data['progress'] = 10 + (step / total_steps * 80)
            elif stage == "Post-processing":
                progress_data['progress'] = 95
            elif stage == "Completed":
                progress_data['progress'] = 100
            
            # Put the progress update in the thread-safe queue
            progress_queue_sync.put({'type': 'progress', **progress_data})
        
        # Create a custom diffusion callback that works in executor thread
        def diffusion_callback(step, timestep, latents):
            current_step = step + 1
            total_steps = request.num_inference_steps or 6
            progress_callback(current_step, total_steps, f"Generating (step {current_step}/{total_steps})")
        
        # Start generation in background thread
        def run_generation():
            try:
                # Import asyncio in the thread to create a new event loop
                import asyncio
                
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Call the sync version of the generation
                    result = loop.run_until_complete(pipeline.generate_with_sync_callback(
                        prompt=request.prompt,
                        negative_prompt=request.negative_prompt,
                        width=request.width,
                        height=request.height,
                        num_inference_steps=request.num_inference_steps,
                        seed=request.seed,
                        model_name=request.model_name,
                        diffusion_callback=diffusion_callback,
                        progress_callback=progress_callback
                    ))
                    
                    generation_time = time.time() - start_time
                    
                    # Send completion with result
                    completion_data = {
                        'type': 'complete',
                        'progress': 100,
                        'stage': 'Completed',
                        'step': request.num_inference_steps or 6,
                        'total_steps': request.num_inference_steps or 6,
                        'image_url': f'/images/{result}',
                        'filename': result,
                        'generation_time': generation_time
                    }
                    
                    progress_queue_sync.put(completion_data)
                    logger.info(f"Streaming generation completed in {generation_time:.2f}s: {result}")
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Error in streaming generation: {str(e)}")
                progress_queue_sync.put({'type': 'error', 'message': f'Generation failed: {str(e)}'})
                generation_error.set()
            finally:
                generation_complete.set()
        
        # Start the generation in a separate thread
        generation_thread = threading.Thread(target=run_generation)
        generation_thread.start()
        
        # Yield progress updates as they come
        while not generation_complete.is_set():
            try:
                # Check for progress updates with timeout
                progress_data = progress_queue_sync.get(timeout=0.1)
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # If this is a completion or error, we're done
                if progress_data.get('type') in ['complete', 'error']:
                    break
                    
            except queue.Empty:
                # No progress update available, continue
                continue
        
        # Wait for generation thread to complete
        generation_thread.join()
        
        # Drain any remaining items from the queue
        while not progress_queue_sync.empty():
            try:
                progress_data = progress_queue_sync.get_nowait()
                yield f"data: {json.dumps(progress_data)}\n\n"
            except queue.Empty:
                break
        
    except Exception as e:
        logger.error(f"Error in streaming generation: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'Generation failed: {str(e)}'})}\n\n"

@router.post("/generate-stream")
async def generate_image_stream(request: GenerationRequest):
    """
    Generate an AI image with real-time progress updates via Server-Sent Events
    """
    try:
        return StreamingResponse(
            generate_with_progress(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    except Exception as e:
        logger.error(f"Error starting streaming generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")