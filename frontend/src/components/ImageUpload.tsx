import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Upload, X, Image as ImageIcon } from "lucide-react";
import { toast } from "sonner";

interface ImageUploadProps {
  onImageSelect: (imageData: string) => void;
  currentImage?: string;
  disabled?: boolean;
}

const ImageUpload = ({ onImageSelect, currentImage, disabled = false }: ImageUploadProps) => {
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>(currentImage || "");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    if (!file.type.startsWith('image/')) {
      toast.error("Please select a valid image file");
      return;
    }

    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error("Image size must be less than 10MB");
      return;
    }

    const reader = new FileReader();
    
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setPreviewUrl(result);
      
      // Extract base64 data (remove data URL prefix)
      const base64Data = result.split(',')[1];
      onImageSelect(base64Data);
    };
    
    reader.onerror = () => {
      toast.error("Failed to read image file");
    };

    reader.readAsDataURL(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setDragOver(true);
    }
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const clearImage = () => {
    setPreviewUrl("");
    onImageSelect("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const openFileDialog = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="space-y-4">
      <Card 
        className={`
          relative border-2 border-dashed transition-all duration-200 cursor-pointer
          ${dragOver ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary/50 hover:bg-muted/25'}
        `}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={openFileDialog}
      >
        {previewUrl ? (
          <div className="relative group">
            <img
              src={previewUrl}
              alt="Input image"
              className="w-full h-64 object-contain rounded-md"
            />
            {!disabled && (
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearImage();
                  }}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
            {!disabled && (
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-md flex items-center justify-center">
                <div className="text-white text-sm font-medium">Click to change image</div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className={`
              p-4 rounded-full mb-4 
              ${dragOver ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}
            `}>
              {dragOver ? <Upload className="h-8 w-8" /> : <ImageIcon className="h-8 w-8" />}
            </div>
            <h3 className="text-lg font-semibold mb-2">
              {dragOver ? 'Drop image here' : 'Upload input image'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {dragOver 
                ? 'Release to upload' 
                : 'Drag and drop an image or click to browse'
              }
            </p>
            <p className="text-sm text-muted-foreground">
              Supports JPG, PNG, WebP • Max 10MB
            </p>
          </div>
        )}
      </Card>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="hidden"
        disabled={disabled}
      />

      {previewUrl && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={openFileDialog}
            disabled={disabled}
          >
            <Upload className="h-4 w-4 mr-2" />
            Change Image
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearImage}
            disabled={disabled}
          >
            <X className="h-4 w-4 mr-2" />
            Remove
          </Button>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;