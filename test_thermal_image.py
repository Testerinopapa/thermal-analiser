#!/usr/bin/env python3
"""
Test script to analyze the thermal image: 000001.jpg
This script sends the image to the backend /analyze endpoint and displays results.
"""

import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Configuration
IMAGE_PATH = "000001.jpg"
BACKEND_URL = "http://localhost:5000"
OUTPUT_FILE = "thermal_analysis_results.json"


def check_server(base_url: str) -> bool:
    """Check if the backend server is running"""
    print("Checking server connection...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"✓ Server is online at {base_url}")
            print(f"  Status: {response.json()}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {base_url}")
        print("  Make sure the server is running:")
        print("  uv run python main.py")
        return False
    except Exception as e:
        print(f"✗ Error connecting to server: {e}")
        return False


def analyze_thermal_image(image_path: str, base_url: str) -> dict | None:
    """Analyze the thermal image using the backend API"""
    print(f"\nAnalyzing thermal image: {image_path}")
    
    if not Path(image_path).exists():
        print(f"✗ Image file not found: {image_path}")
        return None
    
    # Get image file size
    file_size = Path(image_path).stat().st_size
    print(f"  Image size: {file_size / 1024:.2f} KB")
    
    try:
        print("  Uploading image to backend...")
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            response = requests.post(
                f"{base_url}/analyze",
                files=files,
                timeout=60  # Longer timeout for image processing
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Analysis completed successfully")
            return result
        else:
            print(f"✗ Server returned status {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("✗ Request timed out. The image may be too large or processing is taking too long.")
        return None
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        return None


def display_results(result: dict):
    """Display the analysis results in a formatted way"""
    print("\n" + "=" * 70)
    print("THERMAL ANALYSIS RESULTS")
    print("=" * 70)
    
    # Display image information
    if 'image_info' in result:
        img_info = result['image_info']
        print("\nImage Information:")
        print(f"  Dimensions: {img_info.get('width')} x {img_info.get('height')} pixels")
        print(f"  Format: {img_info.get('format', 'Unknown')}")
        print(f"  Color Mode: {img_info.get('mode', 'Unknown')}")
    
    # Display model information
    if 'model_info' in result:
        model_info = result['model_info']
        print("\nModel Information:")
        print(f"  Model: {model_info.get('model', 'Unknown')}")
        print(f"  Type: {model_info.get('model_type', 'Unknown')}")
        if 'note' in model_info:
            print(f"  Note: {model_info['note']}")
    
    # Display warning if present
    if 'warning' in result:
        print("\n⚠ WARNING:")
        print(f"  {result['warning']}")
    
    # Get detections from either 'detections' or 'analysis' field
    detections = result.get('detections', result.get('analysis', []))
    
    if not detections:
        print("\n⚠ No detections found in the image")
        print("  This could mean:")
        print("  - The model didn't detect any objects in this thermal image")
        print("  - The image may not contain recognizable thermal patterns")
        print("  - The confidence threshold may be too high")
        print("\n  💡 Note: The thermal model is configured with confidence threshold 0.25")
        print("     You may want to adjust the model parameters in main.py if needed.")
        return
    
    print(f"\nTotal Detections: {len(detections)}")
    print("-" * 70)
    
    # Group by label
    by_label = {}
    for det in detections:
        label = det.get('label', 'Unknown')
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(det)
    
    # Display summary by label
    print("\nSummary by Detection Type:")
    for label, items in sorted(by_label.items()):
        avg_conf = sum(d.get('confidence', 0) for d in items) / len(items)
        high_severity = sum(1 for d in items if d.get('severity') == 'High')
        print(f"  {label}: {len(items)} detection(s), avg confidence: {avg_conf:.2%}, "
              f"high severity: {high_severity}")
    
    # Display detailed detections
    print("\nDetailed Detections:")
    print("-" * 70)
    for i, det in enumerate(detections, 1):
        label = det.get('label', 'Unknown')
        confidence = det.get('confidence', 0)
        severity = det.get('severity', 'Unknown')
        coords = det.get('coordinates', [])
        
        print(f"\n{i}. {label}")
        print(f"   Confidence: {confidence:.2%}")
        print(f"   Severity: {severity}")
        if coords and len(coords) >= 4:
            x, y, width, height = coords[:4]
            print(f"   Location: x={x:.0f}, y={y:.0f}, width={width:.0f}, height={height:.0f}")
            print(f"   Bounding Box: [{x:.0f}, {y:.0f}, {width:.0f}, {height:.0f}]")
    
    print("\n" + "=" * 70)


def save_results(result: dict, output_file: str, image_path: str = None, backend_url: str = None):
    """Save results to a JSON file"""
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "image_path": image_path or IMAGE_PATH,
        "backend_url": backend_url or BACKEND_URL,
        "analysis": result
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n✓ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠ Could not save results to file: {e}")


def main(image_path: str = None, backend_url: str = None):
    """Main test function"""
    # Use provided values or defaults
    img_path = image_path or IMAGE_PATH
    backend = backend_url or BACKEND_URL
    
    print("=" * 70)
    print("THERMAL IMAGE ANALYSIS TEST")
    print("=" * 70)
    print(f"Image: {img_path}")
    print(f"Backend: {backend}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    if not check_server(backend):
        print("\n⚠ Please start the server first:")
        print("   uv run python main.py")
        sys.exit(1)
    
    # Analyze the image
    result = analyze_thermal_image(img_path, backend)
    
    if result:
        # Display results
        display_results(result)
        
        # Save results
        save_results(result, OUTPUT_FILE, img_path, backend)
        
        print("\n✓ Test completed successfully!")
    else:
        print("\n✗ Test failed - could not analyze image")
        sys.exit(1)


if __name__ == "__main__":
    # Allow custom image path and backend URL via command line
    # Usage: python test_thermal_image.py [image_path] [backend_url]
    image_path = None
    backend_url = None
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"Using custom image: {image_path}")
    if len(sys.argv) > 2:
        backend_url = sys.argv[2]
        print(f"Using custom backend URL: {backend_url}")
    
    main(image_path, backend_url)

