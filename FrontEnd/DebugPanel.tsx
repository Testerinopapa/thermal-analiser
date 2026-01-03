import { Terminal, Copy, Check } from "lucide-react";
import { useState } from "react";

interface DebugPanelProps {
  response: object | null;
  error: string | null;
  isLoading: boolean;
}

export const DebugPanel = ({ response, error, isLoading }: DebugPanelProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (response) {
      await navigator.clipboard.writeText(JSON.stringify(response, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="terminal-panel h-full flex flex-col">
      <div className="flex items-center justify-between p-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary" />
          <span className="font-display text-sm uppercase tracking-wider">
            Debug Output
          </span>
        </div>
        {response && (
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-secondary rounded transition-colors"
            title="Copy JSON"
          >
            {copied ? (
              <Check className="w-4 h-4 text-success" />
            ) : (
              <Copy className="w-4 h-4 text-muted-foreground" />
            )}
          </button>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="flex items-center gap-2 text-primary">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
            <span className="text-sm font-mono">Awaiting response...</span>
          </div>
        ) : error ? (
          <div className="code-block">
            <pre className="text-destructive whitespace-pre-wrap">
              {`// ERROR\n${error}`}
            </pre>
          </div>
        ) : response ? (
          <div className="code-block">
            <pre className="text-foreground whitespace-pre-wrap">
              <SyntaxHighlightedJSON data={response} />
            </pre>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Terminal className="w-12 h-12 text-muted-foreground/30 mb-3" />
            <p className="text-sm text-muted-foreground">
              No data yet. Upload an image to start analysis.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-1 font-mono">
              POST /analyze
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Simple syntax highlighting for JSON
const SyntaxHighlightedJSON = ({ data }: { data: object }) => {
  const jsonString = JSON.stringify(data, null, 2);

  const highlighted = jsonString
    .replace(/"([^"]+)":/g, '<span class="text-primary">"$1"</span>:')
    .replace(/: "([^"]+)"/g, ': <span class="text-success">"$1"</span>')
    .replace(/: (\d+\.?\d*)/g, ': <span class="text-warning">$1</span>')
    .replace(/: (true|false)/g, ': <span class="text-accent">$1</span>')
    .replace(/: (null)/g, ': <span class="text-muted-foreground">$1</span>');

  return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
};
