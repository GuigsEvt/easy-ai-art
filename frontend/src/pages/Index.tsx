import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";
import ModeSelector from "@/components/ModeSelector";
import ParameterControls from "@/components/ParameterControls";
import ImageDisplay from "@/components/ImageDisplay";

type Mode = "text-to-image" | "text-to-video" | "image-to-image";

const Index = () => {
  // State management
  const [selectedMode, setSelectedMode] = useState<Mode>("text-to-image");
  const [prompt, setPrompt] = useState("");
  const [seed, setSeed] = useState("");
  const [steps, setSteps] = useState(20);
  const [sampler, setSampler] = useState("euler");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }

    setIsGenerating(true);
    setGeneratedImage(null);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          seed: seed ? parseInt(seed) : undefined,
          num_inference_steps: steps,
          sampler,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.image_url) {
        setGeneratedImage(data.image_url);
        toast.success("Image generated successfully!");
      } else {
        throw new Error(data.message || "No image URL returned");
      }
    } catch (error) {
      console.error("Generation error:", error);
      toast.error("Failed to generate image. Please try again.");
    } finally {
      setIsGenerating(false);
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

                <ParameterControls
                  seed={seed}
                  steps={steps}
                  sampler={sampler}
                  onSeedChange={setSeed}
                  onStepsChange={setSteps}
                  onSamplerChange={setSampler}
                />

                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating || !prompt.trim()}
                  className="w-full bg-gradient-primary hover:shadow-glow transition-all duration-300"
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
              </div>
            </Card>
          </div>

          {/* Right Panel - Image Display */}
          <div>
            <ImageDisplay imageUrl={generatedImage} isGenerating={isGenerating} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
