#!/usr/bin/env python3
"""
Docker内部端到端测试脚本：验证从图片上传到文本处理的完整流程
"""
import asyncio
import json
import base64
from io import BytesIO
import aiohttp
import websockets
from PIL import Image, ImageDraw, ImageFont


async def create_test_image():
    """创建包含文本的测试图片"""
    # 创建一个简单的测试图片，包含一些文本
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # 添加一些文本
    try:
        # 尝试使用默认字体
        font = ImageFont.load_default()
    except:
        font = None
    
    # 绘制文本（只使用英文避免编码问题）
    draw.text((50, 100), "Hello World", fill='black', font=font)
    draw.text((50, 150), "Test Text", fill='blue', font=font)
    draw.text((50, 200), "Sample Text", fill='red', font=font)
    
    # 保存为字节
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


async def test_backend_health():
    """测试backend健康状况"""
    print("🔍 检查backend健康状况...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://backend:8000/api/v1/health') as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Backend健康检查通过: {result.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ Backend健康检查失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Backend连接失败: {e}")
            return False


async def test_iopaint_health():
    """测试IOPaint健康状况"""
    print("🔍 检查IOPaint健康状况...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://iopaint-service:8081/api/v1/health') as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ IOPaint健康检查通过: {result.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ IOPaint健康检查失败: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ IOPaint连接失败: {e}")
            return False


async def upload_and_detect_text(session: aiohttp.ClientSession, image_data: bytes):
    """上传图片并进行OCR文本检测"""
    print("🔄 Step 1: 上传图片并进行OCR文本检测...")
    
    # 准备multipart form data
    form_data = aiohttp.FormData()
    form_data.add_field('file', image_data, filename='test_image.png', content_type='image/png')
    
    async with session.post('http://backend:8000/api/v1/sessions', data=form_data) as response:
        if response.status != 201:
            error_text = await response.text()
            raise Exception(f"OCR检测失败: {response.status} - {error_text}")
        
        result = await response.json()
        session_id = result['session_id']
        
        # 获取会话详情以获取文本区域
        async with session.get(f'http://backend:8000/api/v1/sessions/{session_id}') as detail_response:
            if detail_response.status != 200:
                error_text = await detail_response.text()
                raise Exception(f"获取会话详情失败: {detail_response.status} - {error_text}")
            
            detail_result = await detail_response.json()
            session_data = detail_result['session']
            text_regions = session_data['text_regions']
        
        print(f"✅ OCR检测成功:")
        print(f"   - Session ID: {session_id}")
        print(f"   - 检测到 {len(text_regions)} 个文本区域")
        
        for i, region in enumerate(text_regions):
            print(f"   - 区域 {i+1}: '{region.get('original_text', '')}' (置信度: {region.get('confidence', 0):.2f})")
        
        return session_id, text_regions


async def start_text_processing(session: aiohttp.ClientSession, session_id: str, text_regions: list):
    """启动文本处理"""
    print(f"🔄 Step 2: 启动异步文本处理...")
    
    if not text_regions:
        print("⚠️ 没有检测到文本区域，跳过处理步骤")
        return None
    
    # 使用第一个文本区域
    selected_region = text_regions[0]
    request_data = {
        "text_regions": [selected_region]
    }
    
    async with session.post(
        f'http://backend:8000/api/v1/sessions/{session_id}/process-async',
        json=request_data
    ) as response:
        if response.status != 202:
            error_text = await response.text()
            raise Exception(f"启动异步处理失败: {response.status} - {error_text}")
        
        result = await response.json()
        task_id = result['task_id']
        
        print(f"✅ 异步处理已启动:")
        print(f"   - Task ID: {task_id}")
        
        return task_id


async def test_websocket_directly():
    """直接测试IOPaint WebSocket连接"""
    print("🔄 Step 3: 直接测试IOPaint WebSocket连接...")
    
    ws_url = "ws://iopaint-service:8081/api/v1/ws/progress"
    
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
                return True
            except asyncio.TimeoutError:
                print("⏰ WebSocket响应超时")
                return False
            
    except Exception as e:
        print(f"❌ IOPaint WebSocket连接失败: {e}")
        return False


async def test_backend_websocket():
    """测试Backend WebSocket连接"""
    print("🔄 Step 4: 测试Backend WebSocket连接...")
    
    ws_url = "ws://backend:8000/api/v1/ws/progress"
    
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
                return True
            except asyncio.TimeoutError:
                print("⏰ WebSocket响应超时")
                return False
            
    except Exception as e:
        print(f"❌ Backend WebSocket连接失败: {e}")
        return False


async def check_final_result(session: aiohttp.ClientSession, session_id: str):
    """检查最终处理结果"""
    print(f"🔄 Step 5: 检查最终处理结果...")
    
    async with session.get(f'http://backend:8000/api/v1/sessions/{session_id}') as response:
        if response.status != 200:
            error_text = await response.text()
            print(f"❌ 获取会话信息失败: {response.status} - {error_text}")
            return
        
        result = await response.json()
        session_data = result['session']
        
        print(f"✅ 最终会话状态:")
        print(f"   - 状态: {session_data.get('status', 'unknown')}")
        print(f"   - 原始图片: {session_data.get('original_image', {}).get('filename', 'N/A')}")
        
        processed_image = session_data.get('processed_image')
        if processed_image:
            print(f"   - 处理后图片: {processed_image.get('filename', 'N/A')}")
            print(f"   - 处理结果可用: ✅")
        else:
            print(f"   - 处理结果: ❌ 未找到")


async def main():
    """主测试函数"""
    print("🚀 开始Docker内部端到端测试...")
    print("=" * 60)
    
    try:
        # Step 0: 健康检查
        backend_ok = await test_backend_health()
        iopaint_ok = await test_iopaint_health()
        
        if not backend_ok or not iopaint_ok:
            print("❌ 服务健康检查失败，退出测试")
            return
        
        print()
        
        # Step 1: WebSocket连接测试
        iopaint_ws_ok = await test_websocket_directly()
        backend_ws_ok = await test_backend_websocket()
        
        print()
        
        # Step 2: 完整流程测试
        async with aiohttp.ClientSession() as session:
            # 创建测试图片并上传进行OCR
            image_data = await create_test_image()
            session_id, text_regions = await upload_and_detect_text(session, image_data)
            
            print()
            
            # 启动异步文本处理
            task_id = await start_text_processing(session, session_id, text_regions)
            
            if task_id:
                print()
                print("⏱️ 等待处理完成...")
                await asyncio.sleep(5)  # 等待处理完成
                
                # 检查最终结果
                await check_final_result(session, session_id)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("🏁 Docker内部端到端测试完成")


if __name__ == "__main__":
    asyncio.run(main())