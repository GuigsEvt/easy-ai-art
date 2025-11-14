/**
 * API client for AI image generation backend
 */

export interface GenerationRequest {
  prompt: string;
  negative_prompt?: string;
  width?: number;
  height?: number;
  num_inference_steps?: number;
  guidance_scale?: number;
  model_name?: string;
  sampler?: string;
}

export interface GenerationResponse {
  success: boolean;
  image_url?: string;
  message: string;
  filename?: string;
  generation_time?: number;
}

export interface ModelInfo {
  name: string;
  path: string;
  type: string;
  pipeline_class?: string;
  description?: string;
  config?: Record<string, unknown>;
}

export interface ModelsResponse {
  success: boolean;
  models: ModelInfo[];
  message: string;
}

class ImageGenerationAPI {
  private baseURL: string;

  constructor(baseURL?: string) {
    // Use environment variable for API base URL, with fallback
    const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8082';
    this.baseURL = baseURL || `${apiBaseUrl}/api`;
  }

  /**
   * Make an authenticated API request
   */
  private async makeRequest(url: string, options: RequestInit = {}): Promise<Response> {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;
    
    return fetch(fullUrl, {
      ...options,
      credentials: 'include', // Include cookies for authentication
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
  }

  /**
   * Generate an AI image based on prompt and parameters
   */
  async generateImage(request: GenerationRequest): Promise<GenerationResponse> {
    try {
      const response = await this.makeRequest('/generate', {
        method: 'POST',
        body: JSON.stringify({
          prompt: request.prompt,
          negative_prompt: request.negative_prompt || null,
          width: request.width || 512,
          height: request.height || 512,
          num_inference_steps: request.num_inference_steps || 6,
          guidance_scale: request.guidance_scale || 1.0,
          model_name: request.model_name || 'sdxl-turbo',
          sampler: request.sampler || 'lcm',
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: GenerationResponse = await response.json();
      
      if (!data.success) {
        throw new Error(data.message || 'Generation failed');
      }

      return data;
    } catch (error) {
      console.error('Image generation error:', error);
      throw error;
    }
  }

  /**
   * Get list of available models
   */
  async getAvailableModels(): Promise<ModelInfo[]> {
    try {
      const response = await this.makeRequest('/models');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ModelsResponse = await response.json();
      console.log('Available models:', data);
      
      if (!data.models) {
        throw new Error(data.message || 'Failed to fetch models');
      }
      
      return data.models;
    } catch (error) {
      console.error('Failed to fetch models:', error);
      throw error;
    }
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<{ status: string }> {
    try {
      const response = await fetch('/health');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const imageAPI = new ImageGenerationAPI();

// Export class for custom instances
export default ImageGenerationAPI;