import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Sparkles, X } from "lucide-react";
import ModeSelector from "@/components/ModeSelector";
import ParameterControls from "@/components/ParameterControls";
import ImageDisplay from "@/components/ImageDisplay";
import GenerationProgress from "@/components/GenerationProgress";
import { imageAPI } from "@/lib/api";
import useStreamingGeneration from "@/hooks/use-streaming-generation";

type Mode = "text-to-image" | "text-to-video" | "image-to-image";

const Index = () => {
  // State management
  const [selectedMode, setSelectedMode] = useState<Mode>("text-to-image");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [seed, setSeed] = useState("");
  const [steps, setSteps] = useState(6); // Default for SDXL-Turbo
  const [width, setWidth] = useState(512);
  const [height, setHeight] = useState(512);
  const [sampler, setSampler] = useState("lcm"); // SDXL-Turbo uses LCM
  const [useStreaming, setUseStreaming] = useState(true); // Toggle for streaming vs regular generation
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [generationTime, setGenerationTime] = useState<number | null>(null);

  // Streaming generation hook
  const {
    isGenerating: streamingGenerating,
    progress,
    stage,
    currentStep,
    totalSteps,
    error: streamingError,
    result: streamingResult,
    generateImageStream,
    cancelGeneration,
    resetState
  } = useStreamingGeneration();

  // Legacy state for non-streaming generation
  const [legacyGenerating, setLegacyGenerating] = useState(false);

  const isGenerating = useStreaming ? streamingGenerating : legacyGenerating;

  // Update image when streaming completes
  useEffect(() => {
    if (streamingResult) {
      setGeneratedImage(streamingResult.image_url);
      setGenerationTime(streamingResult.generation_time);
      toast.success(`Image generated successfully! (${streamingResult.generation_time.toFixed(1)}s)`);
    }
  }, [streamingResult]);

  // Handle streaming errors
  useEffect(() => {
    if (streamingError) {
      toast.error(streamingError);
    }
  }, [streamingError]);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    // Reset previous results
    setGeneratedImage(null);
    setGenerationTime(null);
    resetState();

    const requestParams = {
      prompt: prompt.trim(),
      negative_prompt: negativePrompt.trim() || undefined,
      width,
      height,
      num_inference_steps: steps,
      seed: seed ? parseInt(seed) : undefined,
      model_name: "sdxl-turbo",
      sampler: sampler,
    };

    if (useStreaming) {
      // Use streaming generation
      await generateImageStream(requestParams);
    } else {
      // Use legacy generation
      setLegacyGenerating(true);
      
      try {
        const result = await imageAPI.generateImage(requestParams);

        if (result.success && result.image_url) {
          setGeneratedImage(result.image_url);
          setGenerationTime(result.generation_time || null);
          toast.success(`Image generated successfully! ${result.generation_time ? `(${result.generation_time.toFixed(1)}s)` : ''}`);
        } else {
          throw new Error(result.message || "No image URL returned");
        }
      } catch (error) {
        console.error("Generation error:", error);
        const errorMessage = error instanceof Error ? error.message : "Failed to generate image";
        toast.error(errorMessage);
      } finally {
        setLegacyGenerating(false);
      }
    }
  };

  const handleCancel = () => {
    if (useStreaming && streamingGenerating) {
      cancelGeneration();
      toast.info("Generation cancelled");
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3">
            <Sparkles className="h-8 w-8 text-primary" />
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              AI Image Generator
            </h1>
          </div>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Create stunning images from text descriptions. Simple, fast, and powerful.
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex justify-center">
          <ModeSelector selectedMode={selectedMode} onModeChange={setSelectedMode} />
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Panel - Controls */}
          <div className="space-y-6">
            <Card className="p-6 bg-gradient-card border-border shadow-card">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Prompt</label>
                  <Textarea
                    placeholder="Describe the image you want to generate..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="min-h-[120px] bg-secondary/50 border-border resize-none"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Negative Prompt</label>
                  <Textarea
                    placeholder="Describe what you don't want (optional)..."
                    value={negativePrompt}
                    onChange={(e) => setNegativePrompt(e.target.value)}
                    className="min-h-[80px] bg-secondary/50 border-border resize-none"
                  />
                </div>

                <ParameterControls
                  seed={seed}
                  steps={steps}
                  width={width}
                  height={height}
                  sampler={sampler}
                  onSeedChange={setSeed}
                  onStepsChange={setSteps}
                  onWidthChange={setWidth}
                  onHeightChange={setHeight}
                  onSamplerChange={setSampler}
                />

                <div className="flex gap-2">
                  <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !prompt.trim()}
                    className="flex-1 bg-gradient-primary hover:shadow-glow transition-all duration-300"
                    size="lg"
                  >
                    {isGenerating ? (
                      <>Generating...</>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-5 w-5" />
                        Generate Image
                      </>
                    )}
                  </Button>
                  
                  {isGenerating && useStreaming && (
                    <Button
                      onClick={handleCancel}
                      variant="outline"
                      size="lg"
                      className="px-3"
                    >
                      <X className="h-5 w-5" />
                    </Button>
                  )}
                </div>
                
                {/* Streaming Toggle */}
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="streaming"
                      checked={useStreaming}
                      onChange={(e) => setUseStreaming(e.target.checked)}
                      className="rounded"
                      disabled={isGenerating}
                    />
                    <label htmlFor="streaming" className="text-sm font-medium">
                      Real-time progress updates
                    </label>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {useStreaming ? "Streaming enabled" : "Legacy mode"}
                  </span>
                </div>
              </div>
            </Card>
          </div>

          {/* Right Panel - Progress and Image Display */}
          <div className="space-y-6">
            {/* Progress Component */}
            {useStreaming && (
              <GenerationProgress
                isGenerating={streamingGenerating}
                progress={progress}
                stage={stage}
                currentStep={currentStep}
                totalSteps={totalSteps}
                error={streamingError}
              />
            )}
            
            {/* Image Display */}
            <ImageDisplay 
              imageUrl={generatedImage} 
              isGenerating={isGenerating} 
              generationTime={generationTime}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
