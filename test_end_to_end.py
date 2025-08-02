#!/usr/bin/env python3
"""
端到端测试脚本：验证从图片上传到文本处理的完整流程
"""
import asyncio
import json
import os
import time
import aiohttp
import websockets
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


async def create_test_image():
    """创建包含文本的测试图片"""
    # 创建一个简单的测试图片，包含一些文本
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # 添加一些文本
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        # 使用默认字体
        font = ImageFont.load_default()
    
    # 绘制文本
    draw.text((50, 100), "Hello World", fill='black', font=font)
    draw.text((50, 150), "Test Text", fill='blue', font=font)
    draw.text((50, 200), "样本文字", fill='red', font=font)
    
    # 保存为字节
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


async def upload_image_and_detect_text(session: aiohttp.ClientSession, image_data: bytes):
    """上传图片并进行OCR文本检测"""
    print("🔄 Step 1: 上传图片并进行OCR文本检测...")
    
    # 准备multipart form data
    form_data = aiohttp.FormData()
    form_data.add_field('file', image_data, filename='test_image.png', content_type='image/png')
    
    async with session.post('http://localhost:3000/api/v1/sessions', data=form_data) as response:
        if response.status != 201:
            error_text = await response.text()
            raise Exception(f"OCR检测失败: {response.status} - {error_text}")
        
        result = await response.json()
        session_id = result['session']['id']
        text_regions = result['session']['text_regions']
        
        print(f"✅ OCR检测成功:")
        print(f"   - Session ID: {session_id}")
        print(f"   - 检测到 {len(text_regions)} 个文本区域")
        
        for i, region in enumerate(text_regions):
            print(f"   - 区域 {i+1}: '{region.get('original_text', '')}' (置信度: {region.get('confidence', 0):.2f})")
        
        return session_id, text_regions


async def process_text_removal(session: aiohttp.ClientSession, session_id: str, text_regions: list):
    """处理文本移除"""
    print(f"🔄 Step 2: 开始文本移除处理...")
    
    # 准备请求数据 - 选择第一个文本区域进行处理
    if not text_regions:
        print("⚠️ 没有检测到文本区域，跳过处理步骤")
        return None
    
    # 使用第一个文本区域
    selected_region = text_regions[0]
    request_data = {
        "text_regions": [selected_region]
    }
    
    async with session.post(
        f'http://localhost:3000/api/v1/sessions/{session_id}/process-async',
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


async def monitor_websocket_progress(task_id: str, session_id: str):
    """通过WebSocket监控处理进度"""
    print(f"🔄 Step 3: 通过WebSocket监控处理进度...")
    
    ws_url = f"ws://localhost:3000/api/v1/ws/progress"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ WebSocket连接成功: {ws_url}")
            
            # 订阅任务进度
            subscribe_message = {
                "type": "subscribe_task",
                "task_id": task_id
            }
            await websocket.send(json.dumps(subscribe_message))
            print(f"📡 已订阅任务进度: {task_id}")
            
            # 监听进度更新
            timeout_count = 0
            max_timeout = 30  # 30秒超时
            
            while timeout_count < max_timeout:
                try:
                    # 等待消息，超时时间1秒
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    print(f"📊 收到消息: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'progress_update':
                        progress = data.get('overall_progress', 0)
                        stage = data.get('stage', 'unknown')
                        message_text = data.get('message', '')
                        status = data.get('status', 'unknown')
                        
                        print(f"   - 进度: {progress:.1f}% | 阶段: {stage} | 状态: {status}")
                        print(f"   - 消息: {message_text}")
                        
                        # 检查是否完成
                        if status in ['completed', 'error']:
                            if status == 'completed':
                                print("🎉 处理完成!")
                                result_path = data.get('result_path')
                                if result_path:
                                    print(f"   - 结果路径: {result_path}")
                            else:
                                error_msg = data.get('error', '未知错误')
                                print(f"❌ 处理失败: {error_msg}")
                            break
                    
                    elif data.get('type') == 'connection_established':
                        print(f"🔗 连接已建立: {data.get('connection_id', '')}")
                    
                    elif data.get('type') == 'task_subscribed':
                        print(f"✅ 任务订阅成功: {data.get('task_id', '')}")
                    
                    elif data.get('type') == 'error':
                        error_msg = data.get('error', '未知错误')
                        print(f"❌ WebSocket错误: {error_msg}")
                        break
                    
                    timeout_count = 0  # 重置超时计数
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏱️ 等待进度更新... ({timeout_count}/{max_timeout})")
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket连接已关闭")
                    break
                except Exception as e:
                    print(f"❌ WebSocket错误: {e}")
                    break
            
            if timeout_count >= max_timeout:
                print("⏰ WebSocket监控超时")
                
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")


async def check_final_result(session: aiohttp.ClientSession, session_id: str):
    """检查最终处理结果"""
    print(f"🔄 Step 4: 检查最终处理结果...")
    
    async with session.get(f'http://localhost:3000/api/v1/sessions/{session_id}') as response:
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
    print("🚀 开始端到端测试...")
    print("=" * 60)
    
    try:
        # 创建HTTP会话
        async with aiohttp.ClientSession() as session:
            # Step 1: 创建测试图片并上传进行OCR
            image_data = await create_test_image()
            session_id, text_regions = await upload_image_and_detect_text(session, image_data)
            
            print()
            
            # Step 2: 启动异步文本处理
            task_id = await process_text_removal(session, session_id, text_regions)
            
            if task_id:
                print()
                
                # Step 3: 通过WebSocket监控进度
                await monitor_websocket_progress(task_id, session_id)
                
                print()
                
                # Step 4: 检查最终结果
                await check_final_result(session, session_id)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("🏁 端到端测试完成")


if __name__ == "__main__":
    # 检查依赖
    required_packages = ['aiohttp', 'websockets', 'Pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package if package != 'Pillow' else 'PIL')
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print(f"请运行: pip install {' '.join(missing_packages)}")
        exit(1)
    
    # 运行测试
    asyncio.run(main())