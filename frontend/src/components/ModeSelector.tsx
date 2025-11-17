import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type Mode = "text-to-image" | "text-to-video" | "image-to-image";

interface ModeSelectorProps {
  selectedMode: Mode;
  onModeChange: (mode: Mode) => void;
}

const ModeSelector = ({ selectedMode, onModeChange }: ModeSelectorProps) => {
  const modes = [
    { id: "text-to-image" as Mode, label: "Text to Image", available: true },
    { id: "text-to-video" as Mode, label: "Text to Video", available: false },
    { id: "image-to-image" as Mode, label: "Image to Image", available: true },
  ];

  return (
    <div className="flex flex-wrap gap-3">
      {modes.map((mode) => (
        <Button
          key={mode.id}
          variant={selectedMode === mode.id ? "default" : "outline"}
          onClick={() => mode.available && onModeChange(mode.id)}
          disabled={!mode.available}
          className="relative group"
        >
          {mode.label}
          {!mode.available && (
            <Badge 
              variant="secondary" 
              className="ml-2 text-xs bg-muted text-muted-foreground"
            >
              Soon
            </Badge>
          )}
        </Button>
      ))}
    </div>
  );
};

export default ModeSelector;
