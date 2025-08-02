#!/usr/bin/env python3
"""
Simple test to directly test IOPaint callback mechanism.
"""

import asyncio
import aiohttp
import base64
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

# Create a larger test image (100x100 white PNG)
TEST_IMAGE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVHic7doxAQAAAMKg9U9tCU+gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAeNrtwQEBAAAAgqD1T20JTqAAAAAAAAAAAAAAAAA8BjYsAAFgK2V+AAAAAElFTkSuQmCC"

class CallbackHandler(BaseHTTPRequestHandler):
    received_callbacks = []
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            callback_data = json.loads(post_data.decode('utf-8'))
            print(f"📨 Received callback: {callback_data}")
            self.received_callbacks.append(callback_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "received"}')
            
        except Exception as e:
            print(f"❌ Error processing callback: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def start_callback_server():
    """Start a simple HTTP server to receive callbacks."""
    server = HTTPServer(('localhost', 9999), CallbackHandler)
    server.serve_forever()

async def test_iopaint_callback():
    """Test IOPaint service with callback."""
    
    print("🧪 Testing IOPaint Callback Mechanism")
    print("=" * 50)
    
    # Start callback server in background thread
    print("1. Starting callback server on localhost:9999...")
    callback_thread = threading.Thread(target=start_callback_server, daemon=True)
    callback_thread.start()
    time.sleep(1)  # Give server time to start
    print("   ✅ Callback server started")
    
    # Test IOPaint service
    print("\n2. Testing IOPaint service...")
    
    iopaint_url = "http://localhost:8081"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Check health
            async with session.get(f"{iopaint_url}/api/v1/health") as response:
                if response.status == 200:
                    print("   ✅ IOPaint service is healthy")
                else:
                    print(f"   ❌ IOPaint service error: {response.status}")
                    return False
            
            # Start async processing with callback
            request_data = {
                "image": TEST_IMAGE_B64,
                "regions": [
                    {"x": 10, "y": 10, "width": 30, "height": 30}
                ],
                "enable_progress": True,
                "callback_url": "http://host.docker.internal:9999/callback"
            }
            
            print("\n3. Starting async processing with callback...")
            async with session.post(
                f"{iopaint_url}/api/v1/inpaint-regions-async",
                json=request_data
            ) as response:
                if response.status in [200, 202]:
                    result = await response.json()
                    task_id = result.get('task_id')
                    print(f"   ✅ Processing started - Task ID: {task_id}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to start processing: {response.status} - {error_text}")
                    return False
            
            # Monitor task status
            print("\n4. Monitoring task progress...")
            for i in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                
                async with session.get(f"{iopaint_url}/api/v1/task-status/{task_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data.get('status')
                        progress = status_data.get('overall_progress', 0)
                        print(f"   📊 Status: {status}, Progress: {progress:.1f}%")
                        
                        if status == 'completed':
                            print("   ✅ Processing completed!")
                            break
                        elif status == 'failed':
                            print(f"   ❌ Processing failed: {status_data.get('error_message')}")
                            return False
                    else:
                        print(f"   ⚠️  Could not get status: {response.status}")
            
            # Check if callback was received
            print("\n5. Checking callback receipt...")
            await asyncio.sleep(2)  # Give callback time to arrive
            
            if CallbackHandler.received_callbacks:
                callback = CallbackHandler.received_callbacks[0]
                if callback.get('status') == 'completed' and 'image_data' in callback:
                    print("   ✅ Callback received with completed status and image data!")
                    print(f"   📊 Image data size: {len(callback['image_data'])} characters")
                    return True
                else:
                    print(f"   ❌ Callback received but invalid format: {callback}")
                    return False
            else:
                print("   ❌ No callback received")
                return False
                
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def main():
    """Main test function."""
    
    print("IOPaint Callback Test")
    print("This test verifies the HTTP callback mechanism in IOPaint service")
    print()
    
    success = await test_iopaint_callback()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CALLBACK TEST PASSED - IOPaint callback mechanism is working!")
    else:
        print("❌ CALLBACK TEST FAILED - IOPaint callback mechanism needs fixing")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())