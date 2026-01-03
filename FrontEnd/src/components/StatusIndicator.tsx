import { useEffect, useState } from "react";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

interface StatusIndicatorProps {
  backendUrl: string;
}

type Status = "checking" | "online" | "offline";

export const StatusIndicator = ({ backendUrl }: StatusIndicatorProps) => {
  const [status, setStatus] = useState<Status>("checking");
  const [latency, setLatency] = useState<number | null>(null);

  const checkConnection = async () => {
    setStatus("checking");
    const startTime = Date.now();
    
    try {
      const response = await fetch(backendUrl, {
        method: "GET",
        mode: "cors",
      });
      
      const endTime = Date.now();
      setLatency(endTime - startTime);
      
      if (response.ok) {
        setStatus("online");
      } else {
        setStatus("offline");
      }
    } catch {
      setStatus("offline");
      setLatency(null);
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  return (
    <div className="terminal-panel p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              status === "checking"
                ? "bg-warning animate-pulse"
                : status === "online"
                ? "bg-success status-online"
                : "bg-destructive status-offline"
            }`}
          />
          <div>
            <div className="flex items-center gap-2">
              {status === "online" ? (
                <Wifi className="w-4 h-4 text-success" />
              ) : status === "offline" ? (
                <WifiOff className="w-4 h-4 text-destructive" />
              ) : (
                <RefreshCw className="w-4 h-4 text-warning animate-spin" />
              )}
              <span className="font-display text-sm uppercase tracking-wider">
                {status === "checking"
                  ? "Checking Connection..."
                  : status === "online"
                  ? "🟢 System Online"
                  : "🔴 Offline"}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1 font-mono">
              {backendUrl}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {latency !== null && status === "online" && (
            <div className="text-right">
              <p className="text-xs text-muted-foreground">LATENCY</p>
              <p className="text-sm text-primary font-mono">{latency}ms</p>
            </div>
          )}
          <button
            onClick={checkConnection}
            className="p-2 hover:bg-secondary rounded-md transition-colors"
            title="Refresh connection"
          >
            <RefreshCw
              className={`w-4 h-4 text-muted-foreground hover:text-primary ${
                status === "checking" ? "animate-spin" : ""
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
};

