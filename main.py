from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import uvicorn

app = FastAPI()

# Allow Lovable to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load standard model for testing
model = YOLO("yolov8n.pt")

@app.get("/")
def home():
    return {"status": "Online", "message": "Thermal Backend is ready!"}

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))

    results = model(image)
    detections = []
    for result in results:
        for box in result.boxes:
            # YOLO returns [x1, y1, x2, y2] format
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = xyxy
            
            # Convert to [x, y, width, height] format for frontend
            x = x1
            y = y1
            width = x2 - x1
            height = y2 - y1
            
            conf = float(box.conf)
            cls = int(box.cls)
            label = model.names[cls]

            detections.append({
                "label": label,
                "confidence": round(conf, 2),
                "coordinates": [x, y, width, height],  # [x, y, width, height] format
                "severity": "High" if conf > 0.8 else "Medium"
            })
    
    # Return both 'detections' (for frontend) and 'analysis' (for backward compatibility)
    return {
        "detections": detections,
        "analysis": detections  # Keep for backward compatibility
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
