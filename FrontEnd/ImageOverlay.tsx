import { useEffect, useRef, useState } from "react";

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
  confidence?: number;
}

interface Detection {
  bbox?: number[];
  bounding_box?: number[];
  coordinates?: number[];
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  w?: number;
  h?: number;
  label?: string;
  class?: string;
  class_name?: string;
  confidence?: number;
  score?: number;
}

interface ImageOverlayProps {
  imageUrl: string;
  detections: Detection[] | null;
}

// Color palette for different detection classes
const COLORS = [
  "hsl(25, 100%, 50%)",   // Orange (primary)
  "hsl(142, 76%, 45%)",   // Green
  "hsl(200, 100%, 50%)",  // Cyan
  "hsl(280, 100%, 60%)",  // Purple
  "hsl(45, 100%, 50%)",   // Yellow
];

export const ImageOverlay = ({ imageUrl, detections }: ImageOverlayProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const [naturalDimensions, setNaturalDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setNaturalDimensions({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.src = imageUrl;
  }, [imageUrl]);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setImageDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, [imageUrl]);

  // Normalize various bounding box formats
  const normalizeBoundingBoxes = (detections: Detection[]): BoundingBox[] => {
    return detections.map((d) => {
      let x = 0, y = 0, width = 0, height = 0;

      // Handle different bbox formats
      if (d.bbox && Array.isArray(d.bbox)) {
        [x, y, width, height] = d.bbox;
      } else if (d.bounding_box && Array.isArray(d.bounding_box)) {
        [x, y, width, height] = d.bounding_box;
      } else if (d.coordinates && Array.isArray(d.coordinates)) {
        [x, y, width, height] = d.coordinates;
      } else {
        x = d.x ?? 0;
        y = d.y ?? 0;
        width = d.width ?? d.w ?? 0;
        height = d.height ?? d.h ?? 0;
      }

      return {
        x,
        y,
        width,
        height,
        label: d.label ?? d.class ?? d.class_name,
        confidence: d.confidence ?? d.score,
      };
    });
  };

  const boxes = detections ? normalizeBoundingBoxes(detections) : [];
  const scaleX = imageDimensions.width / (naturalDimensions.width || 1);
  const scaleY = imageDimensions.height / (naturalDimensions.height || 1);

  return (
    <div ref={containerRef} className="relative inline-block w-full">
      <img
        src={imageUrl}
        alt="Analyzed thermal image"
        className="w-full h-auto rounded-md"
        onLoad={() => {
          if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            setImageDimensions({ width: rect.width, height: rect.height });
          }
        }}
      />

      {/* Bounding boxes overlay */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ overflow: "visible" }}
      >
        {boxes.map((box, index) => {
          const color = COLORS[index % COLORS.length];
          const scaledX = box.x * scaleX;
          const scaledY = box.y * scaleY;
          const scaledWidth = box.width * scaleX;
          const scaledHeight = box.height * scaleY;

          return (
            <g key={index}>
              {/* Box rectangle */}
              <rect
                x={scaledX}
                y={scaledY}
                width={scaledWidth}
                height={scaledHeight}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeDasharray="4 2"
              />
              
              {/* Corner accents */}
              <path
                d={`M ${scaledX} ${scaledY + 10} L ${scaledX} ${scaledY} L ${scaledX + 10} ${scaledY}`}
                fill="none"
                stroke={color}
                strokeWidth="3"
              />
              <path
                d={`M ${scaledX + scaledWidth - 10} ${scaledY} L ${scaledX + scaledWidth} ${scaledY} L ${scaledX + scaledWidth} ${scaledY + 10}`}
                fill="none"
                stroke={color}
                strokeWidth="3"
              />
              <path
                d={`M ${scaledX + scaledWidth} ${scaledY + scaledHeight - 10} L ${scaledX + scaledWidth} ${scaledY + scaledHeight} L ${scaledX + scaledWidth - 10} ${scaledY + scaledHeight}`}
                fill="none"
                stroke={color}
                strokeWidth="3"
              />
              <path
                d={`M ${scaledX + 10} ${scaledY + scaledHeight} L ${scaledX} ${scaledY + scaledHeight} L ${scaledX} ${scaledY + scaledHeight - 10}`}
                fill="none"
                stroke={color}
                strokeWidth="3"
              />

              {/* Label background */}
              {(box.label || box.confidence !== undefined) && (
                <>
                  <rect
                    x={scaledX}
                    y={scaledY - 22}
                    width={Math.max(80, (box.label?.length ?? 0) * 8 + 50)}
                    height="20"
                    fill={color}
                    rx="2"
                  />
                  <text
                    x={scaledX + 4}
                    y={scaledY - 8}
                    fill="hsl(220, 20%, 8%)"
                    fontSize="11"
                    fontFamily="JetBrains Mono, monospace"
                    fontWeight="600"
                  >
                    {box.label ?? `Detection ${index + 1}`}
                    {box.confidence !== undefined && ` ${(box.confidence * 100).toFixed(0)}%`}
                  </text>
                </>
              )}
            </g>
          );
        })}
      </svg>

      {/* Detection count badge */}
      {boxes.length > 0 && (
        <div className="absolute top-2 left-2 bg-primary text-primary-foreground px-2 py-1 rounded text-xs font-mono">
          {boxes.length} detection{boxes.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
};
