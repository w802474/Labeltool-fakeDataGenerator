#!/usr/bin/env python3
"""
直接测试WebSocket连接的简单脚本
"""
import asyncio
import json
import websockets

async def test_backend_websocket():
    """测试Backend WebSocket连接"""
    print("🔄 测试Backend WebSocket连接...")
    
    ws_url = "ws://localhost:3000/api/v1/ws/progress"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Backend WebSocket连接成功: {ws_url}")
            
            # 发送ping消息
            ping_message = {
                "type": "ping",
                "timestamp": "2025-08-02T13:30:00.000Z"
            }
            await websocket.send(json.dumps(ping_message))
            print("📡 发送ping消息")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📊 收到响应: {data.get('type', 'unknown')}")
                print(f"   完整响应: {data}")
                return True
            except asyncio.TimeoutError:
                print("⏰ WebSocket响应超时")
                return False
            
    except Exception as e:
        print(f"❌ Backend WebSocket连接失败: {e}")
        return False

async def test_iopaint_websocket():
    """测试IOPaint WebSocket连接"""
    print("🔄 测试IOPaint WebSocket连接...")
    
    ws_url = "ws://localhost:3001/api/v1/ws/progress"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ IOPaint WebSocket连接成功: {ws_url}")
            
            # 发送ping消息
            ping_message = {
                "type": "ping",
                "timestamp": "2025-08-02T13:30:00.000Z"
            }
            await websocket.send(json.dumps(ping_message))
            print("📡 发送ping消息")
            
            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📊 收到响应: {data.get('type', 'unknown')}")
                print(f"   完整响应: {data}")
                return True
            except asyncio.TimeoutError:
                print("⏰ WebSocket响应超时")
                return False
            
    except Exception as e:
        print(f"❌ IOPaint WebSocket连接失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始WebSocket连接测试...")
    print("=" * 60)
    
    # 测试Backend WebSocket
    backend_ok = await test_backend_websocket()
    print()
    
    # 测试IOPaint WebSocket
    iopaint_ok = await test_iopaint_websocket()
    print()
    
    print("=" * 60)
    print(f"🏁 测试完成:")
    print(f"   Backend WebSocket: {'✅ 工作正常' if backend_ok else '❌ 有问题'}")
    print(f"   IOPaint WebSocket: {'✅ 工作正常' if iopaint_ok else '❌ 有问题'}")

if __name__ == "__main__":
    asyncio.run(main())