#!/usr/bin/env python3
"""
Test script to verify the IOPaint callback mechanism.
This script tests the complete flow from Backend -> IOPaint -> Callback -> Backend.
"""

import asyncio
import aiohttp
import base64
import json
import sys
from pathlib import Path

# Test configuration
BACKEND_URL = "http://localhost:8000"
IOPAINT_URL = "http://localhost:8081"

async def test_callback_flow():
    """Test the complete callback flow."""
    
    print("🔄 Testing IOPaint HTTP Callback Flow")
    print("=" * 50)
    
    # Step 1: Check services are running
    print("1. Checking service health...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check Backend
            async with session.get(f"{BACKEND_URL}/api/v1/health") as response:
                if response.status == 200:
                    print("   ✅ Backend service is healthy")
                else:
                    print(f"   ❌ Backend service error: {response.status}")
                    return False
            
            # Check IOPaint
            async with session.get(f"{IOPAINT_URL}/api/v1/health") as response:
                if response.status == 200:
                    print("   ✅ IOPaint service is healthy")
                else:
                    print(f"   ❌ IOPaint service error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Service health check failed: {e}")
        return False
    
    # Step 2: Create a test image
    print("\n2. Creating test image...")
    
    try:
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/58BAAMBAwACKKKKAAAAAElFTkSuQmCC"
        )
        test_image_b64 = base64.b64encode(test_image_data).decode('utf-8')
        print("   ✅ Test image created")
        
    except Exception as e:
        print(f"   ❌ Failed to create test image: {e}")
        return False
    
    # Step 3: Start async processing via Backend
    print("\n3. Starting async processing via Backend...")
    
    try:
        # Upload image to Backend first
        session_data = {
            "image": test_image_b64,
            "regions": [
                {
                    "bounding_box": {
                        "x": 0, "y": 0, "width": 1, "height": 1
                    },
                    "confidence": 0.9
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            # Create session
            form_data = aiohttp.FormData()
            form_data.add_field('file', test_image_data, filename='test.png', content_type='image/png')
            
            async with session.post(f"{BACKEND_URL}/api/v1/sessions", data=form_data) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    session_id = response_data.get("session_id")
                    print(f"   ✅ Session created: {session_id}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to create session: {response.status} - {error_text}")
                    return False
            
            # Add test regions to the session
            update_data = {
                "text_regions": [
                    {
                        "id": "test-region-1",
                        "bounding_box": {"x": 0, "y": 0, "width": 1, "height": 1},
                        "confidence": 0.9,
                        "corners": [
                            {"x": 0, "y": 0}, {"x": 1, "y": 0}, 
                            {"x": 1, "y": 1}, {"x": 0, "y": 1}
                        ],
                        "is_selected": False,
                        "is_user_modified": False,
                        "original_text": "test"
                    }
                ]
            }
            
            async with session.put(f"{BACKEND_URL}/api/v1/sessions/{session_id}/regions", json=update_data) as response:
                if response.status == 200:
                    print("   ✅ Test regions added to session")
                else:
                    error_text = await response.text()
                    print(f"   ⚠️  Could not add regions: {response.status} - {error_text}")
                    # Continue anyway
            
            # Start processing
            async with session.post(f"{BACKEND_URL}/api/v1/sessions/{session_id}/process") as response:
                if response.status in [200, 202]:
                    process_info = await response.json()
                    task_id = process_info.get("task_id")
                    print(f"   ✅ Processing started - Task ID: {task_id}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to start processing: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Failed to start processing: {e}")
        return False
    
    # Step 4: Monitor progress
    print("\n4. Monitoring progress...")
    
    try:
        async with aiohttp.ClientSession() as session:
            for i in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                
                # Check session status
                async with session.get(f"{BACKEND_URL}/api/v1/sessions/{session_id}") as response:
                    if response.status == 200:
                        session_data = await response.json()
                        status = session_data["session"]["status"]
                        print(f"   📊 Status: {status}")
                        
                        if status == "completed":
                            print("   ✅ Processing completed successfully!")
                            
                            # Check if processed image exists
                            if session_data["session"].get("processed_image"):
                                print("   ✅ Processed image available")
                                return True
                            else:
                                print("   ❌ Processed image not found")
                                return False
                                
                        elif status == "error":
                            error_msg = session_data["session"].get("error_message", "Unknown error")
                            print(f"   ❌ Processing failed: {error_msg}")
                            return False
                            
                    else:
                        print(f"   ❌ Failed to get session status: {response.status}")
                        return False
            
            print("   ⏰ Timeout waiting for processing completion")
            return False
            
    except Exception as e:
        print(f"   ❌ Error monitoring progress: {e}")
        return False

async def main():
    """Main test function."""
    
    print("Starting IOPaint Callback Flow Test")
    print("This test verifies the HTTP callback mechanism between Backend and IOPaint services")
    print()
    
    success = await test_callback_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED - Callback flow is working correctly!")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED - Callback flow needs fixing")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())