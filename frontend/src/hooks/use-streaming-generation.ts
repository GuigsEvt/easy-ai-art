import { useState, useCallback, useRef } from 'react';
import { GenerationRequest, GenerationResponse } from '@/lib/api';

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
          seed: request.seed || null,
          model_name: request.model_name || 'sdxl-turbo',
        };

        // Start the generation by making a POST request to the streaming endpoint
        const response = await fetch('/api/generate-stream', {
          method: 'POST',
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

  return {
    ...state,
    generateImageStream,
    cancelGeneration,
    resetState,
  };
};

export default useStreamingGeneration;