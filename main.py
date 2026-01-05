"""
Integrated Thermal Image Analyzer
Uses specialized solar panel fault detection models from Web-API
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import json
import numpy as np
from os import fspath
from pathlib import Path
from dotenv import load_dotenv
from tensorflow.keras.models import load_model

# Import Web-API utilities
from utils.utils import get_yolo_boxes, disconnected
from utils.colors import get_color
import cv2

# Load environment variables
load_dotenv()

# Configuration
base_path = Path(".")
storage_path = base_path.joinpath("storage")

app = Flask(__name__)
CORS(app, origins="*")  # Allow all origins for development

# Model configuration - same as Web-API
class ModelManager:
    """Manages loading and access to the three YOLOv3 models"""
    
    net_h, net_w = 416, 416
    obj_thresh, nms_thresh = 0.5, 0.45
    
    model_compiled = {
        "model_1": fspath(storage_path.joinpath("model/yolo3_full_fault_1.h5")),
        "model_2": fspath(storage_path.joinpath("model/yolo3_full_fault_4.h5")),
        "model_3": fspath(storage_path.joinpath("model/yolo3_full_panel.h5")),
    }
    
    model_config = {
        "model_1": fspath(
            storage_path.joinpath("model/config/config_full_yolo_fault_1_infer.json")
        ),
        "model_2": fspath(
            storage_path.joinpath("model/config/config_full_yolo_fault_4_infer.json")
        ),
        "model_3": fspath(
            storage_path.joinpath("model/config/config_full_yolo_panel.json")
        ),
    }
    
    _models = None
    _models_loaded = False
    _configs_loaded = None
    
    @classmethod
    def _load_models(cls):
        """Load models once (lazy initialization)"""
        if not cls._models_loaded:
            print("Loading solar panel fault detection models...")
            try:
                cls._models = {
                    "model_1": load_model(cls.model_compiled["model_1"]),
                    "model_2": load_model(cls.model_compiled["model_2"]),
                    "model_3": load_model(cls.model_compiled["model_3"]),
                }
                cls._models_loaded = True
                print("✓ All models loaded successfully")
            except Exception as e:
                print(f"✗ Error loading models: {e}")
                print("Make sure model files are in storage/model/ directory")
                raise
        return cls._models
    
    @classmethod
    def _load_configs(cls):
        """Load model configurations"""
        if cls._configs_loaded is None:
            cls._configs_loaded = {}
            for key, config_path in cls.model_config.items():
                try:
                    with open(config_path) as f:
                        cls._configs_loaded[key] = json.load(f)
                except FileNotFoundError:
                    print(f"Warning: Config file not found: {config_path}")
                    cls._configs_loaded[key] = None
        return cls._configs_loaded
    
    @property
    def models(self):
        """Access to models (lazy loading)"""
        return self._load_models()
    
    @property
    def configs(self):
        """Access to configs (lazy loading)"""
        return self._load_configs()


model_manager = ModelManager()


def pil_to_numpy(image):
    """Convert PIL Image to numpy array (RGB format)"""
    return np.array(image)


def numpy_to_pil(image_array):
    """Convert numpy array to PIL Image"""
    return Image.fromarray(image_array.astype('uint8'))


def transform_detections_to_frontend_format(objects):
    """
    Transform Web-API detection format to frontend format
    
    Web-API format: {xmin, xmax, ymin, ymax, label, score, class}
    Frontend format: {label, confidence, coordinates: [x, y, width, height], severity}
    """
    detections = []
    
    for obj in objects:
        xmin = obj.get("xmin", 0)
        ymin = obj.get("ymin", 0)
        xmax = obj.get("xmax", 0)
        ymax = obj.get("ymax", 0)
        
        # Convert to [x, y, width, height] format
        x = float(xmin)
        y = float(ymin)
        width = float(xmax - xmin)
        height = float(ymax - ymin)
        
        # Get confidence score
        score_str = obj.get("score", "0")
        try:
            confidence = float(score_str)
        except (ValueError, TypeError):
            confidence = 0.0
        
        # Determine severity based on confidence
        if confidence > 0.8:
            severity = "High"
        elif confidence > 0.5:
            severity = "Medium"
        else:
            severity = "Low"
        
        detections.append({
            "label": obj.get("label", "Unknown"),
            "confidence": round(confidence, 2),
            "coordinates": [x, y, width, height],
            "severity": severity,
            "class": obj.get("class", ""),
        })
    
    return detections


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "Online",
        "message": "Solar Panel Fault Detection API is ready!",
        "models_loaded": model_manager._models_loaded
    })


@app.route("/analyze", methods=["POST"])
def analyze_image():
    """
    Analyze uploaded thermal image for solar panel faults
    Accepts multipart/form-data with 'file' field
    Returns detections in frontend-compatible format
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Read image data
        image_data = file.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Collect image metadata
        image_info = {
            "size": pil_image.size,
            "mode": pil_image.mode,
            "format": pil_image.format or "UNKNOWN",
            "width": pil_image.width,
            "height": pil_image.height
        }
        
        # Convert PIL to numpy array (RGB format)
        image_array = pil_to_numpy(pil_image)
        
        # Ensure image is in RGB format (3 channels)
        if len(image_array.shape) == 2:
            # Grayscale, convert to RGB
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
        elif image_array.shape[2] == 4:
            # RGBA, convert to RGB
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        elif image_array.shape[2] != 3:
            return jsonify({"error": f"Unsupported image format: {image_array.shape}"}), 400
        
        # Prepare images list (Web-API expects list)
        images = [image_array]
        
        # Load model configurations
        configs = model_manager.configs
        if not all(configs.values()):
            return jsonify({
                "error": "Model configuration files not found",
                "message": "Please ensure config files are in storage/model/config/"
            }), 500
        
        # Extract labels from configs
        labels_1 = configs["model_1"]["model"]["labels"]
        labels_2 = configs["model_2"]["model"]["labels"]
        labels_3 = configs["model_3"]["model"]["labels"]
        
        # Get models
        models = model_manager.models
        
        # Run inference with all three models
        boxes_p_1 = get_yolo_boxes(
            models["model_1"],
            images,
            model_manager.net_h,
            model_manager.net_w,
            configs["model_1"]["model"]["anchors"],
            model_manager.obj_thresh,
            model_manager.nms_thresh,
        )
        
        boxes_p_2 = get_yolo_boxes(
            models["model_2"],
            images,
            model_manager.net_h,
            model_manager.net_w,
            configs["model_2"]["model"]["anchors"],
            model_manager.obj_thresh,
            model_manager.nms_thresh,
        )
        
        boxes_p_3 = get_yolo_boxes(
            models["model_3"],
            images,
            model_manager.net_h,
            model_manager.net_w,
            configs["model_3"]["model"]["anchors"],
            model_manager.obj_thresh,
            model_manager.nms_thresh,
        )
        
        # Filter boxes by confidence threshold
        boxes_p_1 = [
            [box for box in boxes_image if box.get_score() > model_manager.obj_thresh]
            for boxes_image in boxes_p_1
        ]
        boxes_p_2 = [
            [box for box in boxes_image if box.get_score() > model_manager.obj_thresh]
            for boxes_image in boxes_p_2
        ]
        boxes_p_3 = [
            [box for box in boxes_image if box.get_score() > model_manager.obj_thresh]
            for boxes_image in boxes_p_3
        ]
        
        # Apply special processing for panel disconnect (model_3)
        boxes_p_3 = [
            disconnected(image, boxes_image)
            for image, boxes_image in zip(images, boxes_p_3)
        ]
        
        # Collect all detections
        all_objects = []
        
        # Process model_1 detections (Soiling Fault)
        for box in boxes_p_1[0]:
            all_objects.append({
                "class": labels_1[box.get_label()],
                "label": "Soiling Fault",
                "score": str(box.get_score()),
                "xmin": box.xmin,
                "xmax": box.xmax,
                "ymin": box.ymin,
                "ymax": box.ymax,
            })
        
        # Process model_2 detections (Diode Fault)
        for box in boxes_p_2[0]:
            all_objects.append({
                "class": labels_2[box.get_label()],
                "label": "Diode Fault",
                "score": str(box.get_score()),
                "xmin": box.xmin,
                "xmax": box.xmax,
                "ymin": box.ymin,
                "ymax": box.ymax,
            })
        
        # Process model_3 detections (Panel Disconnect)
        for box in boxes_p_3[0]:
            all_objects.append({
                "class": labels_3[box.get_label()],
                "label": "Panel Disconnect",
                "score": str(box.classes[0]),
                "xmin": box.xmin,
                "xmax": box.xmax,
                "ymin": box.ymin,
                "ymax": box.ymax,
            })
        
        # Transform to frontend format
        detections = transform_detections_to_frontend_format(all_objects)
        
        # Build response
        response = {
            "detections": detections,
            "analysis": detections,  # Keep for backward compatibility
            "image_info": image_info,
            "model_info": {
                "model": "YOLOv3 Solar Panel Fault Detection",
                "model_type": "Multi-model ensemble (Soiling, Diode, Panel Disconnect)",
                "note": "Specialized models for photovoltaic fault detection in thermal images."
            }
        }
        
        # Add warning if no detections found
        if len(detections) == 0:
            response["warning"] = (
                "No faults detected in the thermal image. This could mean the solar panels "
                "are in good condition, or the image may need adjustment."
            )
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error during analysis: {e}")
        print(error_trace)
        return jsonify({
            "error": str(e),
            "message": "An error occurred during image analysis"
        }), 500


# Pre-load models on startup (for both direct run and gunicorn)
try:
    model_manager._load_models()
    model_manager._load_configs()
except Exception as e:
    print(f"Warning: Could not pre-load models: {e}")
    print("Models will be loaded on first request")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
