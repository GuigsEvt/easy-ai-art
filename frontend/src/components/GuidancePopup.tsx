import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { HelpCircle, Info } from "lucide-react";

interface ModelDefaults {
  guidance_scale: number;
  steps: number;
  width: number;
  height: number;
  sampler: string;
  explanation: string;
}

const modelDefaults: Record<string, ModelDefaults> = {
  "sdxl-turbo": {
    guidance_scale: 1.0,
    steps: 6,
    width: 512,
    height: 512,
    sampler: "lcm",
    explanation: "SDXL-Turbo is optimized for fast generation with minimal steps. Uses low guidance scale (1.0) and LCM sampler for best results."
  },
  "sdxl-base-1.0": {
    guidance_scale: 7.5,
    steps: 25,
    width: 1024,
    height: 1024,
    sampler: "euler",
    explanation: "SDXL Base provides high-quality images with more detail. Requires higher guidance scale (7.5) and more steps for optimal results."
  },
  "qwen-image": {
    guidance_scale: 5.0,
    steps: 20,
    width: 768,
    height: 768,
    sampler: "dpmpp_2m",
    explanation: "Qwen-Image is a versatile model that balances quality and speed. Works well with moderate guidance scale and steps."
  }
};

interface GuidancePopupProps {
  onApplyDefaults?: (model: string, defaults: ModelDefaults) => void;
}

const GuidancePopup = ({ onApplyDefaults }: GuidancePopupProps) => {
  const [open, setOpen] = useState(false);

  const handleApplyDefaults = (modelName: string) => {
    const defaults = modelDefaults[modelName];
    if (defaults && onApplyDefaults) {
      onApplyDefaults(modelName, defaults);
      setOpen(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="gap-2 bg-secondary/50 hover:bg-secondary/70 border-border"
        >
          <HelpCircle className="h-4 w-4" />
          Model Guidance
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-primary" />
            Model Default Values & Guidance
          </DialogTitle>
          <DialogDescription>
            Recommended parameter values for optimal results with each model. Click "Apply" to use these defaults.
          </DialogDescription>
        </DialogHeader>
        
        {/* Scrollable models section - shows ~1.5 models */}
        <div className="flex-1 min-h-0 mt-6">
          <ScrollArea className="h-[300px]">
            <div className="grid gap-6 pr-4">
              {Object.entries(modelDefaults).map(([modelName, defaults]) => (
                <Card key={modelName} className="border-border">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg capitalize">
                          {modelName.replace('-', ' ')}
                        </CardTitle>
                        <CardDescription className="mt-2">
                          {defaults.explanation}
                        </CardDescription>
                      </div>
                      <Button
                        onClick={() => handleApplyDefaults(modelName)}
                        size="sm"
                        className="bg-primary hover:bg-primary/90"
                      >
                        Apply Defaults
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Guidance Scale</div>
                        <div className="text-lg font-semibold">{defaults.guidance_scale}</div>
                        <div className="text-xs text-muted-foreground">
                          {defaults.guidance_scale <= 2.0 ? "Low (Fast)" : defaults.guidance_scale <= 5.0 ? "Medium" : "High (Quality)"}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Steps</div>
                        <div className="text-lg font-semibold">{defaults.steps}</div>
                        <div className="text-xs text-muted-foreground">
                          {defaults.steps <= 10 ? "Fast" : defaults.steps <= 20 ? "Balanced" : "Quality"}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Resolution</div>
                        <div className="text-lg font-semibold">{defaults.width}×{defaults.height}</div>
                        <div className="text-xs text-muted-foreground">
                          {defaults.width >= 1024 ? "High-res" : defaults.width >= 768 ? "Medium-res" : "Standard"}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Sampler</div>
                        <div className="text-lg font-semibold uppercase">{defaults.sampler}</div>
                        <div className="text-xs text-muted-foreground">
                          {defaults.sampler === "lcm" ? "Fast" : defaults.sampler === "euler" ? "Balanced" : "Quality"}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-muted-foreground">Best For</div>
                        <div className="text-sm">
                          {modelName === "sdxl-turbo" ? "Speed & Iteration" : 
                           modelName === "qwen-image" ? "Versatile Use" : "Final Quality"}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>
        
        {/* Fixed parameter explanations at the bottom */}
        <div className="mt-4 p-4 bg-muted/50 rounded-lg border border-border">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
            <div className="space-y-2 text-sm">
              <div className="font-medium">Parameter Explanations:</div>
              <ul className="space-y-1 text-muted-foreground">
                <li><strong>Guidance Scale:</strong> Controls how closely the model follows your prompt. Lower values give more creative freedom.</li>
                <li><strong>Steps:</strong> Number of denoising steps. More steps = higher quality but slower generation.</li>
                <li><strong>Resolution:</strong> Output image dimensions. Higher resolution requires more memory and time.</li>
                <li><strong>Sampler:</strong> The algorithm used for generation. Different samplers have different quality/speed trade-offs.</li>
              </ul>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default GuidancePopup;