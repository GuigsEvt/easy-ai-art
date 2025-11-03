import { Download, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ImageDisplayProps {
  imageUrl: string | null;
  isGenerating: boolean;
}

const ImageDisplay = ({ imageUrl, isGenerating }: ImageDisplayProps) => {
  const handleDownload = () => {
    if (!imageUrl) return;
    
    const link = document.createElement("a");
    link.href = imageUrl;
    link.download = `generated-image-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card className="p-6 bg-gradient-card border-border shadow-card">
      <div className="aspect-square w-full rounded-lg overflow-hidden bg-secondary/30 flex items-center justify-center">
        {isGenerating ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-muted-foreground">Generating your image...</p>
          </div>
        ) : imageUrl ? (
          <div className="relative w-full h-full group">
            <img
              src={imageUrl}
              alt="Generated"
              className="w-full h-full object-contain"
            />
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <Button
                onClick={handleDownload}
                variant="secondary"
                size="lg"
                className="gap-2"
              >
                <Download className="h-5 w-5" />
                Download
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-2">
            <div className="text-4xl">🎨</div>
            <p className="text-muted-foreground">Your generated image will appear here</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default ImageDisplay;
