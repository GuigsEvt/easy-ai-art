import { Download, Loader2, Clock, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ImageDisplayProps {
  imageUrl: string | null;
  isGenerating: boolean;
  generationTime?: number | null;
}

const ImageDisplay = ({ imageUrl, isGenerating, generationTime }: ImageDisplayProps) => {
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
            <div className="w-16 h-16 mx-auto bg-secondary/50 rounded-full flex items-center justify-center">
              <Sparkles className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground">Your generated image will appear here</p>
          </div>
        )}
      </div>
      
      {generationTime && (
        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>Generated in {generationTime.toFixed(1)}s</span>
        </div>
      )}
    </Card>
  );
};

export default ImageDisplay;
