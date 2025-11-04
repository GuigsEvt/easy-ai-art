import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

interface ParameterControlsProps {
  seed: string;
  steps: number;
  sampler: string;
  onSeedChange: (value: string) => void;
  onStepsChange: (value: number) => void;
  onSamplerChange: (value: string) => void;
}

const ParameterControls = ({
  seed,
  steps,
  sampler,
  onSeedChange,
  onStepsChange,
  onSamplerChange,
}: ParameterControlsProps) => {
  const samplers = [
    "euler",
    "euler_ancestral",
    "heun",
    "dpm_2",
    "dpm_2_ancestral",
    "lms",
    "dpm_fast",
    "dpm_adaptive",
    "dpmpp_2s_ancestral",
    "dpmpp_sde",
    "dpmpp_2m",
  ];

  return (
    <div className="space-y-6">
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
        <div className="flex justify-between items-center">
          <Label htmlFor="steps">Steps</Label>
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
      </div>

      <div className="space-y-2">
        <Label htmlFor="sampler">Sampler</Label>
        <Select value={sampler} onValueChange={onSamplerChange}>
          <SelectTrigger id="sampler" className="bg-secondary/50 border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {samplers.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};

export default ParameterControls;
