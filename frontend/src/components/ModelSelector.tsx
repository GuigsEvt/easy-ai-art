import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { imageAPI, ModelInfo, ModelDefaults } from "@/lib/api";

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelName: string) => void;
  onApplyDefaults?: (defaults: ModelDefaults) => void;
  mode?: "text-to-image" | "image-to-image"; // Add mode prop to filter models
}

const ModelSelector = ({ selectedModel, onModelChange, onApplyDefaults, mode = "text-to-image" }: ModelSelectorProps) => {
  const [allModels, setAllModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter models based on the mode - memoized to prevent infinite loops
  const getFilteredModels = useCallback((models: ModelInfo[]) => {
    if (mode === "text-to-image") {
      return models.filter(model => 
        model.type.includes("Text-to-Image") || 
        model.type.includes("Qwen-Image") || 
        model.type.includes("FLUX.1")
      );
    } else if (mode === "image-to-image") {
      return models.filter(model => 
        model.type.includes("Image-to-Image") || 
        model.type.includes("Img2Img") ||
        model.type.includes("Inpainting") ||
        model.type.includes("Depth-to-Image")
      );
    }
    return models;
  }, [mode]);

  // Get the current filtered models
  const filteredModels = getFilteredModels(allModels);

  // Load models function - only depends on loading state, not on props
  const loadModels = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const availableModels = await imageAPI.getAvailableModels();
      setAllModels(availableModels);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle model selection and mode changes separately
  useEffect(() => {
    if (filteredModels.length === 0) return;

    // If no model is selected, select the first one
    if (!selectedModel) {
      const firstModel = filteredModels[0];
      onModelChange(firstModel.name);
      
      // Apply defaults if available and callback is provided
      if (onApplyDefaults && firstModel.defaults) {
        onApplyDefaults(firstModel.defaults);
        toast.success(`Applied defaults for ${firstModel.name.replace('-', ' ')}`);
      }
      return;
    }

    // Check if the currently selected model is still valid for this mode
    const isSelectedModelValid = filteredModels.some(model => model.name === selectedModel);
    if (!isSelectedModelValid) {
      // Switch to the first valid model
      const firstModel = filteredModels[0];
      onModelChange(firstModel.name);
      toast.info(`Switched to ${firstModel.name} (suitable for ${mode})`);
      
      // Apply defaults if available and callback is provided
      if (onApplyDefaults && firstModel.defaults) {
        onApplyDefaults(firstModel.defaults);
      }
    }
  }, [filteredModels, selectedModel, onModelChange, onApplyDefaults, mode]);

  // Only load models once on mount
  useEffect(() => {
    loadModels();
  }, []);

  const handleModelSelect = (modelName: string) => {
    onModelChange(modelName);
    
    // Apply defaults if available and callback is provided
    if (onApplyDefaults) {
      const selectedModelInfo = filteredModels.find(m => m.name === modelName);
      if (selectedModelInfo?.defaults) {
        onApplyDefaults(selectedModelInfo.defaults);
        toast.success(`Applied defaults for ${modelName.replace('-', ' ')}`);
      } else {
        toast.success(`Selected model: ${modelName}`);
      }
    } else {
      toast.success(`Selected model: ${modelName}`);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm text-muted-foreground">Loading available models...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 border-destructive">
        <div className="flex items-center gap-3 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">{error}</span>
          <Button variant="outline" size="sm" onClick={loadModels}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  if (filteredModels.length === 0 && !loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center gap-3 text-muted-foreground">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">
            No models found for {mode === "image-to-image" ? "image-to-image" : "text-to-image"}.
          </span>
          <Button variant="outline" size="sm" onClick={loadModels}>
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">
            Available Models {mode === "image-to-image" ? "(Image-to-Image)" : "(Text-to-Image)"}
          </h3>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{filteredModels.length} model{filteredModels.length !== 1 ? 's' : ''}</Badge>
            <Button variant="outline" size="sm" onClick={loadModels} disabled={loading}>
              {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : "Refresh"}
            </Button>
          </div>
        </div>
        
        {/* Scrollable models container - shows ~1.5 models */}
        <ScrollArea className="h-[240px]">
          <div className="grid gap-3 pr-4">
            {filteredModels.map((model) => (
              <div
                key={model.name}
                className={`
                  p-4 rounded-lg border cursor-pointer transition-all duration-200
                  ${selectedModel === model.name 
                    ? 'border-primary bg-primary/5 shadow-sm' 
                    : 'border-border hover:border-primary/50 hover:bg-secondary/50'
                  }
                `}
                onClick={() => handleModelSelect(model.name)}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {selectedModel === model.name && (
                        <CheckCircle className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    
                    {model.pipeline_class && (
                      <Badge variant="outline" className="text-xs">
                        {model.pipeline_class}
                      </Badge>
                    )}
                    
                    {model.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {model.description}
                      </p>
                    )}
                  </div>
                  
                  <Badge variant={model.type === 'diffusers' ? 'default' : 'secondary'}>
                    {model.type}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        
        <div className="text-xs text-muted-foreground">
          Click on a model to select it for image generation. Use "Refresh" to reload models.
        </div>
      </div>
    </Card>
  );
};

export default ModelSelector;