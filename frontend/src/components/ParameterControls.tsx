import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

interface ParameterControlsProps {
  guidanceScale: number;
  steps: number;
  width: number;
  height: number;
  sampler: string;
  strength?: number; // Optional for img2img
  mode?: "text-to-image" | "image-to-image"; // To show/hide relevant controls
  onGuidanceScaleChange: (value: number) => void;
  onStepsChange: (value: number) => void;
  onWidthChange: (value: number) => void;
  onHeightChange: (value: number) => void;
  onSamplerChange: (value: string) => void;
  onStrengthChange?: (value: number) => void; // Optional for img2img
}

const ParameterControls = ({
  guidanceScale,
  steps,
  width,
  height,
  sampler,
  strength = 0.75,
  mode = "text-to-image",
  onGuidanceScaleChange,
  onStepsChange,
  onWidthChange,
  onHeightChange,
  onSamplerChange,
  onStrengthChange,
}: ParameterControlsProps) => {
  // Updated samplers list to match SDXL-Turbo capabilities
  const samplers = [
    { value: "lcm", label: "LCM" },
    { value: "euler", label: "Euler" },
    { value: "euler_a", label: "Euler Ancestral" },
    { value: "ddim", label: "DDIM" },
    { value: "dpmpp_2m", label: "DPM++ 2M" },
    { value: "dpmpp_2m_karras", label: "DPM++ 2M Karras" },
    { value: "flowmatch", label: "Match Euler" },
  ];

  const imageSizes = [
    { label: "512×512", width: 512, height: 512 },
    { label: "768×512", width: 768, height: 512 },
    { label: "512×768", width: 512, height: 768 },
    { label: "768×768", width: 768, height: 768 },
    { label: "1024×512", width: 1024, height: 512 },
    { label: "512×1024", width: 512, height: 1024 },
    { label: "1024×1024", width: 1024, height: 1024 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="guidance_scale">Guidance Scale</Label>
          <div className="flex items-center space-x-4">
            <Slider
              id="guidance_scale"
              min={0.5}
              max={20}
              step={0.1}
              value={[guidanceScale]}
              onValueChange={(value) => onGuidanceScaleChange(value[0])}
              className="flex-1"
            />
            <Input
              type="number"
              value={guidanceScale}
              onChange={(e) => onGuidanceScaleChange(parseFloat(e.target.value) || 0.5)}
              min={0.5}
              max={20}
              step={0.1}
              className="w-20 bg-secondary/50 border-border"
            />
          </div>
          <div className="text-xs text-muted-foreground">
            How closely to follow the prompt (0.5-20)
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="sampler">Sampler</Label>
          <Select value={sampler} onValueChange={onSamplerChange}>
            <SelectTrigger className="bg-secondary/50 border-border">
              <SelectValue placeholder="Select sampler" />
            </SelectTrigger>
            <SelectContent>
              {samplers.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="size">Image Size</Label>
        <Select 
          value={`${width}x${height}`} 
          onValueChange={(value) => {
            const size = imageSizes.find(s => `${s.width}x${s.height}` === value);
            if (size) {
              onWidthChange(size.width);
              onHeightChange(size.height);
            }
          }}
        >
          <SelectTrigger className="bg-secondary/50 border-border">
            <SelectValue placeholder="Select size" />
          </SelectTrigger>
          <SelectContent>
            {imageSizes.map((size) => (
              <SelectItem key={`${size.width}x${size.height}`} value={`${size.width}x${size.height}`}>
                {size.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <Label htmlFor="steps">Inference Steps</Label>
          <span className="text-sm text-muted-foreground">{steps}</span>
        </div>
        <Slider
          id="steps"
          min={1}
          max={50}
          step={1}
          value={[steps]}
          onValueChange={(value) => onStepsChange(value[0])}
          className="py-4"
        />
        <div className="text-xs text-muted-foreground">
          Recommended: 4-8 for SDXL-Turbo, 20-50 for SDXL-Base
        </div>
      </div>

      {/* Strength parameter for image-to-image */}
      {mode === "image-to-image" && onStrengthChange && (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="strength">Strength</Label>
            <span className="text-sm text-muted-foreground">{strength.toFixed(2)}</span>
          </div>
          <Slider
            id="strength"
            min={0.1}
            max={1.0}
            step={0.05}
            value={[strength]}
            onValueChange={(value) => onStrengthChange(value[0])}
            className="py-4"
          />
          <div className="text-xs text-muted-foreground">
            How much to transform the input image (0.1 = subtle, 1.0 = heavy transformation)
          </div>
        </div>
      )}

    </div>
  );
};

export default ParameterControls;
