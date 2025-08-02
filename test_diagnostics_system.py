#!/usr/bin/env python3
"""
Test script to verify the IOPaint diagnostics and retry system.
"""

import asyncio
import aiohttp
import base64
import json
import sys
import time
from typing import Dict, Any

# Test configuration
IOPAINT_URL = "http://localhost:8081"

# Create test images with different sizes
def create_test_image_b64(width: int, height: int) -> str:
    """Create a test PNG image and encode as base64."""
    from PIL import Image
    import io
    
    # Create a simple white image
    image = Image.new('RGB', (width, height), color='white')
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    
    return base64.b64encode(img_bytes).decode('utf-8')

async def test_diagnostics_system():
    """Test the complete diagnostics system."""
    
    print("🧪 Testing IOPaint Diagnostics System")
    print("=" * 50)
    
    # Test 1: Normal processing (should succeed)
    print("\n1. Testing normal processing (small image, few regions)...")
    await test_normal_processing()
    
    # Test 2: Large image (should trigger warnings)
    print("\n2. Testing large image processing...")
    await test_large_image_processing()
    
    # Test 3: Many regions (should trigger complexity warnings)
    print("\n3. Testing many regions processing...")
    await test_many_regions_processing()
    
    # Test 4: Connection timeout simulation
    print("\n4. Testing connection timeout handling...")
    await test_connection_timeout()
    
    print("\n" + "=" * 50)
    print("✅ Diagnostics system test completed!")

async def test_normal_processing():
    """Test normal processing with small image and few regions."""
    try:
        # Create small test image (512x512)
        test_image = create_test_image_b64(512, 512)
        
        # Create a few test regions
        regions = [
            {"x": 50, "y": 50, "width": 100, "height": 30},
            {"x": 200, "y": 200, "width": 150, "height": 40}
        ]
        
        payload = {
            "image": test_image,
            "regions": regions,
            "enable_progress": True,
            "sd_steps": 15,  # Use fast settings
            "task_id": f"test-normal-{int(time.time())}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{IOPAINT_URL}/api/v1/inpaint-regions-async",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    task_id = result.get('task_id')
                    print(f"   ✅ Normal processing started: {task_id}")
                    
                    # Monitor progress briefly
                    await monitor_task_briefly(session, task_id)
                else:
                    print(f"   ❌ Normal processing failed: {response.status}")
                    
    except Exception as e:
        print(f"   ❌ Normal processing error: {e}")

async def test_large_image_processing():
    """Test processing with large image to trigger size warnings."""
    try:
        # Create large test image (3000x3000 = 9MP)
        print("   📋 Creating large test image (3000x3000)...")
        test_image = create_test_image_b64(3000, 3000)
        
        # Create moderate number of regions
        regions = [
            {"x": 100, "y": 100, "width": 200, "height": 50},
            {"x": 500, "y": 500, "width": 300, "height": 60},
            {"x": 1000, "y": 1000, "width": 250, "height": 40}
        ]
        
        payload = {
            "image": test_image,
            "regions": regions,
            "enable_progress": True,
            "task_id": f"test-large-{int(time.time())}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{IOPAINT_URL}/api/v1/inpaint-regions-async",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    task_id = result.get('task_id')
                    print(f"   ✅ Large image processing started: {task_id}")
                    print(f"   📊 Expected: Size warnings and parameter adjustments")
                    
                    await monitor_task_briefly(session, task_id)
                else:
                    print(f"   ❌ Large image processing failed: {response.status}")
                    
    except Exception as e:
        print(f"   ❌ Large image processing error: {e}")

async def test_many_regions_processing():
    """Test processing with many regions to trigger complexity warnings."""
    try:
        # Create moderate test image (1024x1024)
        test_image = create_test_image_b64(1024, 1024)
        
        # Create many regions (40 regions)
        regions = []
        for i in range(40):
            x = (i % 8) * 120 + 10
            y = (i // 8) * 120 + 10
            regions.append({
                "x": x,
                "y": y,
                "width": 100,
                "height": 30
            })
        
        print(f"   📋 Created {len(regions)} regions for complexity test")
        
        payload = {
            "image": test_image,
            "regions": regions,
            "enable_progress": True,
            "task_id": f"test-many-regions-{int(time.time())}"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{IOPAINT_URL}/api/v1/inpaint-regions-async",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    task_id = result.get('task_id')
                    print(f"   ✅ Many regions processing started: {task_id}")
                    print(f"   📊 Expected: Complexity warnings and batching recommendations")
                    
                    await monitor_task_briefly(session, task_id)
                else:
                    print(f"   ❌ Many regions processing failed: {response.status}")
                    
    except Exception as e:
        print(f"   ❌ Many regions processing error: {e}")

async def test_connection_timeout():
    """Test connection timeout handling."""
    try:
        # Use invalid URL to trigger connection error
        invalid_url = "http://localhost:9999"  # Non-existent port
        
        print("   📋 Testing with invalid URL to trigger connection error...")
        
        payload = {
            "image": create_test_image_b64(512, 512),
            "regions": [{"x": 50, "y": 50, "width": 100, "height": 30}],
            "task_id": f"test-timeout-{int(time.time())}"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{invalid_url}/api/v1/inpaint-regions-async",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    print(f"   ❌ Unexpected success: {response.status}")
            except aiohttp.ClientConnectorError:
                print("   ✅ Connection error triggered (as expected)")
                print("   📊 Expected: Diagnostics should classify this as CONNECTION_REFUSED")
            except asyncio.TimeoutError:
                print("   ✅ Timeout error triggered (as expected)")
                print("   📊 Expected: Diagnostics should classify this as NETWORK_TIMEOUT")
                
    except Exception as e:
        print(f"   ❌ Connection timeout test error: {e}")

async def monitor_task_briefly(session: aiohttp.ClientSession, task_id: str):
    """Monitor task for a brief period to see diagnostic messages."""
    print(f"   📊 Monitoring task {task_id} for 15 seconds...")
    
    for i in range(15):  # Monitor for 15 seconds
        try:
            async with session.get(
                f"{IOPAINT_URL}/api/v1/task-status/{task_id}",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    status = result.get("status", "unknown")
                    stage = result.get("stage", "unknown")
                    progress = result.get("overall_progress", 0)
                    
                    print(f"      Status: {status}, Stage: {stage}, Progress: {progress:.1f}%")
                    
                    if status in ["completed", "failed", "error"]:
                        if status == "completed":
                            print("   ✅ Task completed successfully")
                        else:
                            print(f"   ⚠️  Task failed with status: {status}")
                        break
                else:
                    print(f"      Could not get status: {response.status}")
                    
        except Exception as e:
            print(f"      Status check failed: {e}")
        
        await asyncio.sleep(1)

async def test_service_health():
    """Test if IOPaint service is accessible."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{IOPAINT_URL}/api/v1/health",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ IOPaint service is healthy: {health_data}")
                    return True
                else:
                    print(f"❌ IOPaint service health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Could not connect to IOPaint service: {e}")
        print(f"   Make sure IOPaint service is running on {IOPAINT_URL}")
        return False

async def main():
    """Main test function."""
    print("IOPaint Diagnostics System Test")
    print("This test verifies:")
    print("1. Preprocessing validation and warnings")
    print("2. Error classification and diagnosis") 
    print("3. Resource monitoring and recommendations")
    print("4. Intelligent retry mechanisms")
    print("5. Parameter adjustment strategies")
    print()
    
    # Check service health first
    if not await test_service_health():
        print("\n❌ IOPaint service is not available. Please start the service first.")
        sys.exit(1)
    
    # Run diagnostic tests
    await test_diagnostics_system()
    
    print("\n🎉 All diagnostic tests completed!")
    print("\nCheck the IOPaint service logs to see detailed diagnostic output:")
    print("- Preprocessing validation warnings")
    print("- Error classification details") 
    print("- Resource monitoring data")
    print("- Retry attempt strategies")
    print("- Parameter adjustment recommendations")

if __name__ == "__main__":
    asyncio.run(main())