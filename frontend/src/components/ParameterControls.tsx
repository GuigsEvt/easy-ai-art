import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

interface ParameterControlsProps {
  seed: string;
  steps: number;
  guidanceScale: number;
  width: number;
  height: number;
  sampler: string;
  onSeedChange: (value: string) => void;
  onStepsChange: (value: number) => void;
  onGuidanceScaleChange: (value: number) => void;
  onWidthChange: (value: number) => void;
  onHeightChange: (value: number) => void;
  onSamplerChange: (value: string) => void;
}

const ParameterControls = ({
  seed,
  steps,
  guidanceScale,
  width,
  height,
  sampler,
  onSeedChange,
  onStepsChange,
  onGuidanceScaleChange,
  onWidthChange,
  onHeightChange,
  onSamplerChange,
}: ParameterControlsProps) => {
  // Updated samplers list to match SDXL-Turbo capabilities
  const samplers = [
    "lcm",
    "euler_a",
    "ddim",
    "dpmpp_2m",
  ];

  const imageSizes = [
    { label: "512×512", width: 512, height: 512 },
    { label: "768×512", width: 768, height: 512 },
    { label: "512×768", width: 512, height: 768 },
    { label: "1024×512", width: 1024, height: 512 },
    { label: "512×1024", width: 512, height: 1024 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="seed">Seed</Label>
          <Input
            id="seed"
            type="text"
            placeholder="Random (leave empty)"
            value={seed}
            onChange={(e) => onSeedChange(e.target.value)}
            className="bg-secondary/50 border-border"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="sampler">Sampler</Label>
          <Select value={sampler} onValueChange={onSamplerChange}>
            <SelectTrigger className="bg-secondary/50 border-border">
              <SelectValue placeholder="Select sampler" />
            </SelectTrigger>
            <SelectContent>
              {samplers.map((s) => (
                <SelectItem key={s} value={s}>
                  {s.toUpperCase()}
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
          max={24}
          step={1}
          value={[steps]}
          onValueChange={(value) => onStepsChange(value[0])}
          className="py-4"
        />
        <div className="text-xs text-muted-foreground">
          Recommended: 4-8 for SDXL-Turbo
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <Label htmlFor="guidance">Guidance Scale</Label>
          <span className="text-sm text-muted-foreground">{guidanceScale}</span>
        </div>
        <Slider
          id="guidance"
          min={0.5}
          max={2.0}
          step={0.1}
          value={[guidanceScale]}
          onValueChange={(value) => onGuidanceScaleChange(value[0])}
          className="py-4"
        />
        <div className="text-xs text-muted-foreground">
          Recommended: 1.0-1.5 for SDXL-Turbo
        </div>
      </div>

    </div>
  );
};

export default ParameterControls;
