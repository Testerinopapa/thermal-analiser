import { useState, useCallback } from "react";
import { Flame, Cpu, Zap } from "lucide-react";
import { StatusIndicator } from "@/components/StatusIndicator";
import { UploadZone } from "@/components/UploadZone";
import { DebugPanel } from "@/components/DebugPanel";
import { ImageOverlay } from "@/components/ImageOverlay";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "https://thermal-analyzer-backend.onrender.com";

interface AnalysisResponse {
  detections?: Array<{
    bbox?: number[];
    bounding_box?: number[];
    coordinates?: number[];
    label?: string;
    class?: string;
    confidence?: number;
    score?: number;
    [key: string]: unknown;
  }>;
  [key: string]: unknown;
}

const App = () => {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [response, setResponse] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageUpload = useCallback(async (file: File) => {
    setImageFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setError(null);
    setResponse(null);
    setIsAnalyzing(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errorText}`);
      }

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const handleClear = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setImageFile(null);
    setPreviewUrl(null);
    setResponse(null);
    setError(null);
  }, [previewUrl]);

  // Extract detections from response (handle various API response formats)
  const getDetections = () => {
    if (!response) return null;
    
    if (Array.isArray(response.detections)) return response.detections;
    if (Array.isArray(response.predictions)) return response.predictions;
    if (Array.isArray(response.results)) return response.results;
    if (Array.isArray(response.boxes)) return response.boxes;
    if (Array.isArray(response)) return response;
    
    return null;
  };

  const detections = getDetections();

  return (
    <div className="min-h-screen bg-background cyber-grid relative scanlines">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm relative z-20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center neon-border">
                <Flame className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="font-display text-xl uppercase tracking-wider">
                  Thermal Analysis
                </h1>
                <p className="text-xs text-muted-foreground font-mono">
                  Connection Test Dashboard v1.0
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
                <Cpu className="w-4 h-4" />
                <span>ENDPOINT: {BACKEND_URL.replace("https://", "")}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 relative z-20">
        {/* Status Bar */}
        <div className="mb-6">
          <StatusIndicator backendUrl={BACKEND_URL} />
        </div>

        {/* Main Grid */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left Column - Upload & Preview */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-primary" />
              <h2 className="font-display text-sm uppercase tracking-wider">
                Image Analysis
              </h2>
            </div>

            {previewUrl && detections && detections.length > 0 ? (
              <div className="terminal-panel p-4">
                <ImageOverlay imageUrl={previewUrl} detections={detections} />
                <button
                  onClick={handleClear}
                  className="mt-4 w-full py-2 bg-secondary hover:bg-secondary/80 rounded-md text-sm font-mono transition-colors"
                >
                  Clear & Upload New Image
                </button>
              </div>
            ) : (
              <UploadZone
                onImageUpload={handleImageUpload}
                isUploading={isAnalyzing}
                previewUrl={previewUrl}
                onClear={handleClear}
              />
            )}

            {/* Quick Stats */}
            {response && (
              <div className="grid grid-cols-3 gap-3">
                <div className="terminal-panel p-3 text-center">
                  <p className="text-2xl font-display text-primary">
                    {detections?.length ?? 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Detections</p>
                </div>
                <div className="terminal-panel p-3 text-center">
                  <p className="text-2xl font-display text-success">
                    {response ? "✓" : "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">Response</p>
                </div>
                <div className="terminal-panel p-3 text-center">
                  <p className="text-2xl font-display text-warning">
                    {imageFile ? (imageFile.size / 1024).toFixed(0) : "—"}
                  </p>
                  <p className="text-xs text-muted-foreground">KB</p>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Debug Panel */}
          <div className="lg:min-h-[500px]">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              <h2 className="font-display text-sm uppercase tracking-wider">
                Raw JSON Response
              </h2>
            </div>
            <DebugPanel
              response={response}
              error={error}
              isLoading={isAnalyzing}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-auto relative z-20">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground font-mono">
            <span>THERMAL-ANALYZER-DASHBOARD</span>
            <span>© 2026 | DEBUG MODE ACTIVE</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;

