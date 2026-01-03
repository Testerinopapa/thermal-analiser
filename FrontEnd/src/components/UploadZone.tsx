import { useState, useCallback, useRef } from "react";
import { Upload, Image as ImageIcon, X } from "lucide-react";

interface UploadZoneProps {
  onImageUpload: (file: File) => void;
  isUploading: boolean;
  previewUrl: string | null;
  onClear: () => void;
}

export const UploadZone = ({
  onImageUpload,
  isUploading,
  previewUrl,
  onClear,
}: UploadZoneProps) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0].type.startsWith("image/")) {
        onImageUpload(files[0]);
      }
    },
    [onImageUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onImageUpload(files[0]);
      }
    },
    [onImageUpload]
  );

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  if (previewUrl) {
    return (
      <div className="relative">
        <button
          onClick={onClear}
          className="absolute top-2 right-2 z-10 p-2 bg-background/80 hover:bg-destructive rounded-md transition-colors"
          title="Clear image"
        >
          <X className="w-4 h-4" />
        </button>
        <div className="upload-zone p-2 relative overflow-hidden">
          <img
            src={previewUrl}
            alt="Uploaded thermal image"
            className="w-full h-auto rounded-md"
          />
          {isUploading && (
            <div className="absolute inset-0 bg-background/80 flex items-center justify-center">
              <div className="flex flex-col items-center gap-2">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-primary font-mono">
                  ANALYZING...
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`upload-zone p-12 cursor-pointer ${
        isDragOver ? "drag-over" : ""
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-secondary flex items-center justify-center">
            {isDragOver ? (
              <ImageIcon className="w-10 h-10 text-primary animate-pulse" />
            ) : (
              <Upload className="w-10 h-10 text-muted-foreground" />
            )}
          </div>
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-primary/30 animate-spin" style={{ animationDuration: '8s' }} />
        </div>

        <div className="text-center">
          <p className="font-display text-lg uppercase tracking-wider text-foreground">
            {isDragOver ? "Drop Thermal Image" : "Upload Thermal Image"}
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Drag & drop or click to browse
          </p>
          <p className="text-xs text-muted-foreground/60 mt-2 font-mono">
            Supports: JPG, PNG, WEBP
          </p>
        </div>
      </div>
    </div>
  );
};

