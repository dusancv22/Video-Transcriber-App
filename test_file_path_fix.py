#!/usr/bin/env python3
"""
Test script to verify file path handling fixes
"""

import requests
import json
import time
import sys
from pathlib import Path

# API base URL
BASE_URL = "http://127.0.0.1:7050"

def test_api_connectivity():
    """Test if the API is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print("✓ API Health Check:", response.json())
        return True
    except Exception as e:
        print("✗ API not accessible:", e)
        return False

def test_file_path_validation():
    """Test file path validation with various inputs"""
    test_cases = [
        ("relative_path.mp4", False, "Relative path should be rejected"),
        ("C:\\test\\video.mp4", False, "Non-existent file should be rejected"),
        ("C:\\Windows\\System32", False, "Directory path should be rejected"),
    ]
    
    print("\n--- Testing File Path Validation ---")
    for path, should_succeed, description in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/files/add",
                json={"files": [path]}
            )
            if response.status_code == 200:
                if not should_succeed:
                    print(f"✗ {description}: Unexpectedly succeeded")
                else:
                    print(f"✓ {description}: Passed")
            else:
                if should_succeed:
                    print(f"✗ {description}: Unexpectedly failed - {response.json()}")
                else:
                    print(f"✓ {description}: Correctly rejected - {response.json().get('detail', 'No detail')}")
        except Exception as e:
            print(f"✗ {description}: Error - {e}")

def test_debug_endpoint():
    """Test the debug endpoint"""
    print("\n--- Testing Debug Endpoint ---")
    try:
        response = requests.get(f"{BASE_URL}/api/debug/queue")
        data = response.json()
        print("✓ Debug endpoint accessible")
        print(f"  Queue items: {len(data.get('detailed_items', []))}")
        print(f"  Pipeline ready: {data.get('pipeline_ready', False)}")
        print(f"  Is processing: {data.get('is_processing', False)}")
        
        # Show details of queued items
        for item in data.get('detailed_items', []):
            print(f"\n  File: {item.get('file_path', 'Unknown')}")
            print(f"    - Absolute path: {item.get('path_is_absolute', False)}")
            print(f"    - File exists: {item.get('file_exists', False)}")
            print(f"    - Is file: {item.get('is_file', False)}")
            print(f"    - Status: {item.get('status', 'Unknown')}")
            
    except Exception as e:
        print(f"✗ Debug endpoint error: {e}")

def test_with_real_file():
    """Test with a real video file if available"""
    print("\n--- Testing with Real File ---")
    
    # Try to find a test video file
    test_video_paths = [
        r"C:\Users\Dusan\Videos\test.mp4",
        r"C:\Users\Dusan\Downloads\test.mp4",
        r"C:\Users\Dusan\Desktop\test.mp4",
    ]
    
    test_file = None
    for path in test_video_paths:
        if Path(path).exists():
            test_file = path
            break
    
    if not test_file:
        print("ℹ No test video file found. Create a test.mp4 file in Videos, Downloads, or Desktop folder to test.")
        return
    
    print(f"Found test file: {test_file}")
    
    try:
        # Add file to queue
        response = requests.post(
            f"{BASE_URL}/api/files/add",
            json={"files": [test_file]}
        )
        
        if response.status_code == 200:
            print(f"✓ Successfully added file to queue")
            result = response.json()
            print(f"  Added: {result.get('added_count', 0)} files")
            print(f"  Skipped: {result.get('skipped_count', 0)} files")
        else:
            print(f"✗ Failed to add file: {response.json()}")
            
    except Exception as e:
        print(f"✗ Error adding file: {e}")

def main():
    print("=== Video Transcriber File Path Fix Test ===\n")
    
    # Wait a moment for the server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    if not test_api_connectivity():
        print("\nAPI is not running. Please start the application first.")
        sys.exit(1)
    
    test_file_path_validation()
    test_debug_endpoint()
    test_with_real_file()
    
    print("\n=== Test Complete ===")
    print("\nNext steps:")
    print("1. Try dragging and dropping a video file into the application")
    print("2. Check the console logs for file path information")
    print("3. Use the debug endpoint to verify files are queued correctly")
    print("4. Try starting the transcription process")

if __name__ == "__main__":
    main()