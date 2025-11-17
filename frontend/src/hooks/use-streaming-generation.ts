import { useState, useCallback, useRef } from 'react';
import { GenerationRequest, GenerationResponse, ImageToImageRequest } from '@/lib/api';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082';

export interface ProgressUpdate {
  type: 'progress' | 'complete' | 'error';
  progress: number;
  stage: string;
  step: number;
  total_steps: number;
  image_url?: string;
  filename?: string;
  generation_time?: number;
  message?: string;
}

export interface StreamingState {
  isGenerating: boolean;
  progress: number;
  stage: string;
  currentStep: number;
  totalSteps: number;
  error?: string;
  result?: {
    image_url: string;
    filename: string;
    generation_time: number;
  };
}

const useStreamingGeneration = () => {
  const [state, setState] = useState<StreamingState>({
    isGenerating: false,
    progress: 0,
    stage: '',
    currentStep: 0,
    totalSteps: 0,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const generateImageStream = useCallback(
    async (request: GenerationRequest): Promise<void> => {
      // Reset state
      setState({
        isGenerating: true,
        progress: 0,
        stage: 'Initializing',
        currentStep: 0,
        totalSteps: request.num_inference_steps || 6,
        error: undefined,
        result: undefined,
      });

      try {
        // Close any existing EventSource
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        // Create the request body
        const requestBody = {
          prompt: request.prompt,
          negative_prompt: request.negative_prompt || null,
          width: request.width || 512,
          height: request.height || 512,
          num_inference_steps: request.num_inference_steps || 6,
          guidance_scale: request.guidance_scale || 1.0,
          model_name: request.model_name || 'sdxl-turbo',
          sampler: request.sampler || 'lcm',
        };

        // Log all generation parameters to console
        console.log('🎨 FRONTEND: Sending Generation Request');
        console.log('=' .repeat(60));
        console.log('📝 Prompt:', request.prompt?.substring(0, 100) + (request.prompt?.length > 100 ? '...' : ''));
        console.log('❌ Negative Prompt:', request.negative_prompt || 'None');
        console.log('📐 Dimensions:', `${requestBody.width}x${requestBody.height}`);
        console.log('🔢 Inference Steps:', requestBody.num_inference_steps);
        console.log('🎯 Guidance Scale:', requestBody.guidance_scale);
        console.log('🤖 Model:', requestBody.model_name);
        console.log('⚙️ Sampler:', requestBody.sampler);
        console.log('📦 Full Request Body:', requestBody);
        console.log('=' .repeat(60));

        // Start the generation by making a POST request to the streaming endpoint
        const response = await fetch(`${API_BASE_URL}/api/generate-stream`, {
          method: 'POST',
          credentials: 'include', // Include cookies for authentication
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Create EventSource from the response
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Failed to get response stream reader');
        }

        const decoder = new TextDecoder();

        // Read the stream
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            break;
          }

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data: ProgressUpdate = JSON.parse(line.slice(6));
                
                if (data.type === 'progress') {
                  setState(prev => ({
                    ...prev,
                    progress: data.progress,
                    stage: data.stage,
                    currentStep: data.step,
                    totalSteps: data.total_steps,
                  }));
                } else if (data.type === 'complete') {
                  setState(prev => ({
                    ...prev,
                    isGenerating: false,
                    progress: 100,
                    stage: 'Completed',
                    currentStep: data.step,
                    totalSteps: data.total_steps,
                    result: {
                      image_url: data.image_url!,
                      filename: data.filename!,
                      generation_time: data.generation_time!,
                    },
                  }));
                  return; // Generation complete
                } else if (data.type === 'error') {
                  setState(prev => ({
                    ...prev,
                    isGenerating: false,
                    error: data.message,
                  }));
                  return; // Generation failed
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }
      } catch (error) {
        console.error('Streaming generation error:', error);
        setState(prev => ({
          ...prev,
          isGenerating: false,
          error: error instanceof Error ? error.message : 'Failed to generate image',
        }));
      }
    },
    []
  );

  const cancelGeneration = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    setState(prev => ({
      ...prev,
      isGenerating: false,
      error: 'Generation cancelled',
    }));
  }, []);

  const resetState = useCallback(() => {
    setState({
      isGenerating: false,
      progress: 0,
      stage: '',
      currentStep: 0,
      totalSteps: 0,
      error: undefined,
      result: undefined,
    });
  }, []);

  const generateImageToImageStream = useCallback(
    async (request: ImageToImageRequest): Promise<void> => {
      // Reset state
      setState({
        isGenerating: true,
        progress: 0,
        stage: 'Initializing img2img',
        currentStep: 0,
        totalSteps: request.num_inference_steps || 20,
        error: undefined,
        result: undefined,
      });

      try {
        // Close any existing EventSource
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        // Make POST request to start streaming
        const response = await fetch(`${API_BASE_URL}/api/generate-img2img-stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            prompt: request.prompt,
            image_data: request.image_data,
            negative_prompt: request.negative_prompt || null,
            strength: request.strength || 0.75,
            num_inference_steps: request.num_inference_steps || 20,
            guidance_scale: request.guidance_scale || 7.5,
            model_name: request.model_name || 'sdxl-base-1.0',
            sampler: request.sampler || 'euler_a',
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error('No response body available for streaming');
        }

        // Create EventSource from the response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete lines
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.substring(6);
              
              if (data.trim() === '') continue; // Skip empty data
              
              try {
                const parsed: ProgressUpdate = JSON.parse(data);
                
                if (parsed.type === 'progress') {
                  setState(prev => ({
                    ...prev,
                    progress: parsed.progress || 0,
                    stage: parsed.stage || prev.stage,
                    currentStep: parsed.step || 0,
                    totalSteps: parsed.total_steps || prev.totalSteps,
                  }));
                } else if (parsed.type === 'complete') {
                  setState(prev => ({
                    ...prev,
                    isGenerating: false,
                    progress: 100,
                    stage: 'Completed',
                    result: {
                      image_url: parsed.image_url!,
                      filename: parsed.filename!,
                      generation_time: parsed.generation_time!,
                    },
                  }));
                  break;
                } else if (parsed.type === 'error') {
                  setState(prev => ({
                    ...prev,
                    isGenerating: false,
                    error: parsed.message || 'Unknown error occurred',
                  }));
                  break;
                }
              } catch (parseError) {
                console.warn('Failed to parse SSE data:', parseError, 'Raw data:', data);
              }
            }
          }
        }
        
      } catch (error) {
        console.error('Streaming img2img generation error:', error);
        setState(prev => ({
          ...prev,
          isGenerating: false,
          error: error instanceof Error ? error.message : 'Unknown error occurred',
        }));
      }
    },
    []
  );

  return {
    ...state,
    generateImageStream,
    generateImageToImageStream,
    cancelGeneration,
    resetState,
  };
};

export default useStreamingGeneration;