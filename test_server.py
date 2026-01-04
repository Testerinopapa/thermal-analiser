#!/usr/bin/env python3
"""Test script for Thermal Analyzer backend"""

import sys
import requests
from pathlib import Path

def test_dependencies():
    """Test if all required dependencies are available"""
    print("Testing dependencies...")
    try:
        import fastapi
        import ultralytics
        import PIL
        import uvicorn
        print("✓ All dependencies available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        return False

def test_model_file():
    """Test if model file exists"""
    print("\nTesting model file...")
    if Path("yolov8n.pt").exists():
        print("✓ Model file (yolov8n.pt) exists")
        return True
    else:
        print("✗ Model file (yolov8n.pt) NOT found")
        return False

def test_model_loading():
    """Test if model can be loaded"""
    print("\nTesting model loading...")
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        print("✓ Model loaded successfully")
        print(f"  Model classes: {len(model.names)}")
        return True
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return False

def test_server_running(base_url="http://localhost:5000"):
    """Test if server is running and responding"""
    print("\nTesting server connection...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running. Start it with: uv run python main.py")
        return False
    except Exception as e:
        print(f"✗ Error connecting to server: {e}")
        return False

def test_analyze_endpoint(base_url="http://localhost:5000", image_path=None):
    """Test the /analyze endpoint"""
    print("\nTesting /analyze endpoint...")
    
    if not image_path:
        print("  (Skipping - no image provided)")
        print("  To test: python test_server.py --analyze <image_path>")
        return None
    
    if not Path(image_path).exists():
        print(f"✗ Image file not found: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/analyze", files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Analysis successful")
            print(f"  Detections: {len(result.get('analysis', []))}")
            for i, det in enumerate(result.get('analysis', [])[:3], 1):
                print(f"    {i}. {det.get('label')} (conf: {det.get('confidence')}, severity: {det.get('severity')})")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error testing analyze endpoint: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Thermal Analyzer Backend - Test Suite")
    print("=" * 50)
    
    # Basic tests
    deps_ok = test_dependencies()
    model_file_ok = test_model_file()
    
    if deps_ok and model_file_ok:
        model_ok = test_model_loading()
    
    # Server tests (only if server might be running)
    if "--server" in sys.argv or "--all" in sys.argv:
        test_server_running()
    
    # Analyze endpoint test
    if "--analyze" in sys.argv:
        idx = sys.argv.index("--analyze")
        if idx + 1 < len(sys.argv):
            image_path = sys.argv[idx + 1]
            test_analyze_endpoint(image_path=image_path)
        else:
            print("\n✗ --analyze requires an image path")
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("  Run with --server to test server connection")
    print("  Run with --analyze <image_path> to test image analysis")
    print("  Run with --all to test everything")
    print("=" * 50)





