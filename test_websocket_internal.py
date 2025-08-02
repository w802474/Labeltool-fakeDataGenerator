#!/usr/bin/env python3
"""
在容器内部测试WebSocket连接
"""
import asyncio
import json
import websockets

async def test_websocket_internal():
    """在容器内部测试WebSocket"""
    print("🔄 在容器内部测试WebSocket连接...")
    
    # 测试后端WebSocket (容器内部地址)
    ws_url = "ws://localhost:8000/api/v1/ws/progress"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ 容器内WebSocket连接成功: {ws_url}")
            
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
        print(f"❌ 容器内WebSocket连接失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket_internal())