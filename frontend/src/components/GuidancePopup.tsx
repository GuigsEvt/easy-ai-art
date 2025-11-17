import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { HelpCircle, Info, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { imageAPI, ModelDefaults } from "@/lib/api";

interface GuidancePopupModelDefaults extends ModelDefaults {
  steps: number;
}

interface GuidancePopupProps {
  onApplyDefaults?: (model: string, defaults: GuidancePopupModelDefaults) => void;
}

const GuidancePopup = ({ onApplyDefaults }: GuidancePopupProps) => {
  const [open, setOpen] = useState(false);
  const [modelDefaults, setModelDefaults] = useState<Record<string, GuidancePopupModelDefaults>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && Object.keys(modelDefaults).length === 0) {
      loadModelDefaults();
    }
  }, [open, modelDefaults]);

  const loadModelDefaults = async () => {
    try {
      setLoading(true);
      setError(null);
      const defaults = await imageAPI.getAllModelDefaults();
      
      const convertedDefaults: Record<string, GuidancePopupModelDefaults> = {};
      for (const [modelName, modelDefault] of Object.entries(defaults)) {
        convertedDefaults[modelName] = {
          ...modelDefault,
          steps: modelDefault.num_inference_steps
        };
      }
      
      setModelDefaults(convertedDefaults);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load model defaults';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
            Recommended parameter values for optimal results with each model.
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 min-h-0 mt-6">
          {loading ? (
            <div className="flex items-center justify-center h-[300px]">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm text-muted-foreground">Loading model defaults...</span>
              </div>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-[300px] gap-3">
              <div className="text-sm text-destructive">{error}</div>
              <Button variant="outline" size="sm" onClick={loadModelDefaults}>
                Retry
              </Button>
            </div>
          ) : Object.keys(modelDefaults).length === 0 ? (
            <div className="flex items-center justify-center h-[300px]">
              <div className="text-sm text-muted-foreground">No model defaults found</div>
            </div>
          ) : (
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
                          <div className="text-sm font-medium text-muted-foreground">Guidance</div>
                          <div className="text-lg font-semibold">{defaults.guidance_scale}</div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="text-sm font-medium text-muted-foreground">Steps</div>
                          <div className="text-lg font-semibold">{defaults.steps}</div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="text-sm font-medium text-muted-foreground">Resolution</div>
                          <div className="text-lg font-semibold">{defaults.width}×{defaults.height}</div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="text-sm font-medium text-muted-foreground">Sampler</div>
                          <div className="text-lg font-semibold">
                            {defaults.sampler === "flowmatch" ? "Match Euler" : 
                             defaults.sampler === "euler_a" ? "Euler Ancestral" :
                             defaults.sampler === "dpmpp_2m" ? "DPM++ 2M" :
                             defaults.sampler === "dpmpp_2m_karras" ? "DPM++ 2M Karras" :
                             defaults.sampler.toUpperCase()}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {defaults.sampler === "lcm" ? "Fast" : 
                             defaults.sampler === "flowmatch" ? "Qwen-Optimized" :
                             defaults.sampler === "euler" ? "Balanced" : "Quality"}
                          </div>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="text-sm font-medium text-muted-foreground">Type</div>
                          <div className="text-sm">
                            {modelName === "sdxl-turbo" ? "Fast" : 
                             modelName === "qwen-image" ? "Versatile" : "Quality"}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default GuidancePopup;
