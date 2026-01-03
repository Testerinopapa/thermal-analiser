from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import uvicorn
import torch

# Fix for PyTorch 2.6+ weights_only security feature
# Patch torch.load to allow loading ultralytics models
# This is safe since we're loading from trusted Hugging Face models
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# Now import YOLO after patching torch.load
from ultralyticsplus import YOLO

app = FastAPI()

# Allow Lovable to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load thermal-specific model
print("Loading thermal image detection model...")
model = YOLO('foduucom/thermal-image-object-detection')

# Set model parameters for thermal image detection
model.overrides['conf'] = 0.25  # NMS confidence threshold
model.overrides['iou'] = 0.45  # NMS IoU threshold
model.overrides['agnostic_nms'] = False  # NMS class-agnostic
model.overrides['max_det'] = 1000  # maximum number of detections per image
print("✓ Thermal model loaded successfully")

@app.get("/")
def home():
    return {"status": "Online", "message": "Thermal Backend is ready!"}

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    
    # Collect image metadata for diagnostics
    image_info = {
        "size": image.size,
        "mode": image.mode,
        "format": image.format,
        "width": image.width,
        "height": image.height
    }

    # Perform inference with thermal model
    results = model.predict(image)
    detections = []
    
    for result in results:
        if result.boxes is not None:
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
                label = model.names[cls] if cls < len(model.names) else f"Class_{cls}"

                detections.append({
                    "label": label,
                    "confidence": round(conf, 2),
                    "coordinates": [x, y, width, height],  # [x, y, width, height] format
                    "severity": "High" if conf > 0.8 else "Medium" if conf > 0.5 else "Low"
                })
    
    # Add diagnostic information
    response = {
        "detections": detections,
        "analysis": detections,  # Keep for backward compatibility
        "image_info": image_info,
        "model_info": {
            "model": "foduucom/thermal-image-object-detection",
            "model_type": "YOLOv8 (thermal image object detection)",
            "note": "This model is specifically trained for thermal/infrared image detection."
        }
    }
    
    # Add warning if no detections found
    if len(detections) == 0:
        response["warning"] = (
            "No detections found in the thermal image. This could mean there are no "
            "detectable objects, or the image quality/format may need adjustment."
        )
    
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
