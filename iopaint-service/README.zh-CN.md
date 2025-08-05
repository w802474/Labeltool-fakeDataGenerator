# IOPaint 文本移除服务

**🌍 中文 | [日本語](README.ja.md) | [English](README.md)**

🎯 **基于 IOPaint 1.6.0 的专业高级文本修复和移除微服务**

一个生产级别的独立微服务，提供强大的文本移除功能和实时进度跟踪。专为需要高质量图像文本修复的应用程序设计，易于集成。

## ✨ 核心特性

- 🔧 **高级文本移除**: 使用最先进的 IOPaint 和 LAMA 模型，实现无缝背景保护
- 🚀 **实时处理**: 基于 WebSocket 的进度跟踪，适用于长时间运行的任务  
- 🎛️ **多种处理模式**: 支持同步、异步和批量处理
- 🎨 **灵活的输入方式**: 支持基于掩码、区域和坐标的修复
- 🏗️ **生产就绪**: Docker 容器化、健康监控和全面的错误处理
- ⚡ **性能优化**: GPU 加速、内存管理和智能图像缩放
- 🔌 **易于集成**: RESTful API 与 OpenAPI 文档和多种 SDK
- 📊 **高级监控**: 资源跟踪、诊断和处理分析

## 📋 完整 API 参考

### 核心端点
- `GET /` - 服务信息和状态
- `GET /api/v1/health` - 带诊断信息的健康检查
- `GET /api/v1/model` - 当前模型信息
- `GET /api/v1/info` - 详细服务信息和功能

### 同步修复
- `POST /api/v1/inpaint` - 使用提供的掩码进行修复（返回图像二进制数据）
- `POST /api/v1/inpaint-regions` - 使用文本区域进行修复（返回图像二进制数据）
- `POST /api/v1/inpaint-regions-json` - 使用文本区域进行修复（返回 JSON 统计信息）

### 异步处理
- `POST /api/v1/inpaint-regions-async` - 启动带进度跟踪的异步修复
- `GET /api/v1/task-status/{task_id}` - 获取任务状态和进度
- `POST /api/v1/cancel-task/{task_id}` - 取消运行中的任务
- `GET /api/v1/tasks` - 获取任务统计和队列状态

### WebSocket 端点
- `WS /api/v1/ws/progress/{task_id}` - 特定任务的实时进度更新
- `WS /api/v1/ws/progress` - 所有任务的通用进度更新

### 文档
- `GET /docs` - 交互式 API 文档（Swagger UI）
- `GET /redoc` - 替代 API 文档（ReDoc）

## 🛠️ 配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|-------|------|
| `IOPAINT_HOST` | `0.0.0.0` | 服务主机地址 |
| `IOPAINT_PORT` | `8081` | 服务端口 |
| `IOPAINT_MODEL` | `lama` | 使用的 IOPaint 模型 |
| `IOPAINT_DEVICE` | `cpu` | 处理设备（cpu/cuda/mps） |
| `IOPAINT_LOW_MEM` | `true` | 启用低内存模式 |
| `IOPAINT_CPU_OFFLOAD` | `true` | 启用 CPU 卸载 |
| `MAX_IMAGE_SIZE` | `2048` | 图像最大尺寸 |
| `MAX_FILE_SIZE` | `52428800` | 最大文件大小（50MB） |
| `REQUEST_TIMEOUT` | `300` | 请求超时时间（秒） |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 支持的模型
- **lama**（默认）- 大型掩码修复模型（最佳质量）
- **ldm** - 潜在扩散模型
- **zits** - 增量 Transformer 结构
- **mat** - 掩码感知 Transformer
- **fcf** - 傅里叶卷积
- **manga** - 专门用于漫画/动画图像

## 🚢 Docker 部署

### 独立部署
```bash
# 构建镜像
docker build -t iopaint-service .

# 运行容器
docker run -d \
  --name iopaint-service \
  -p 8081:8081 \
  -e IOPAINT_MODEL=lama \
  -e IOPAINT_DEVICE=cpu \
  iopaint-service
```

### GPU 支持
```bash
docker run -d \
  --name iopaint-service \
  --gpus all \
  -p 8081:8081 \
  -e IOPAINT_DEVICE=cuda \
  iopaint-service
```

### Docker Compose 集成
```yaml
services:
  iopaint-service:
    build: ./iopaint-service
    container_name: iopaint-service
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - IOPAINT_MODEL=lama
      - IOPAINT_DEVICE=cpu
      - IOPAINT_LOW_MEM=true
    volumes:
      - iopaint_cache:/root/.cache/huggingface
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  iopaint_cache:
    driver: local

networks:
  app-network:
    driver: bridge
```

## 🔌 API 使用示例

### 健康检查
```bash
curl http://localhost:8081/api/v1/health
```

### 区域修复
```python
import requests
import base64

# 准备图像和区域
with open('image.jpg', 'rb') as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

regions = [
    {"x": 100, "y": 50, "width": 200, "height": 30},
    {"x": 150, "y": 200, "width": 150, "height": 25}
]

# 发送请求
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions',
    json={
        "image": image_b64,
        "regions": regions
    }
)

# 保存结果
if response.status_code == 200:
    with open('result.png', 'wb') as f:
        f.write(response.content)
```

### 获取处理统计信息（JSON 响应）
```python
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-json',
    json={
        "image": image_b64,
        "regions": regions
    }
)

stats = response.json()
print(f"处理了 {stats['processing_stats']['regions_processed']} 个区域")
print(f"处理时间: {stats['processing_stats']['processing_time']:.2f}秒")
```

### 带进度跟踪的异步处理
```python
import requests
import uuid

# 启动异步处理
task_id = str(uuid.uuid4())
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-async',
    json={
        "image": image_b64,
        "regions": regions,
        "task_id": task_id,
        "enable_progress": True
    }
)

async_result = response.json()
print(f"启动任务: {async_result['task_id']}")
print(f"WebSocket URL: {async_result['websocket_url']}")

# 检查任务状态
status_response = requests.get(f'http://localhost:8081/api/v1/task-status/{task_id}')
status = status_response.json()
print(f"任务状态: {status['status']}")
```

### 后端服务集成

此 IOPaint 服务设计为通过主后端 API 调用，而不是直接从前端应用程序调用。后端服务处理会话管理、文件存储，并协调完整的 OCR + 文本移除工作流程。

#### 后端集成示例 (Python)
```python
# 后端服务如何与 IOPaint 集成
# 文件: backend/app/infrastructure/clients/iopaint_client.py

import aiohttp
import base64

class IOPaintClient:
    def __init__(self, base_url="http://iopaint-service:8081"):
        self.base_url = base_url
    
    async def inpaint_regions_async(self, image_path: str, text_regions: List[dict], task_id: str):
        """启动异步文本移除处理。"""
        # 将图像转换为 base64
        async with aiofiles.open(image_path, 'rb') as f:
            image_data = await f.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # 将区域转换为 IOPaint 格式
        regions = []
        for region in text_regions:
            regions.append({
                "x": region["bounding_box"]["x"],
                "y": region["bounding_box"]["y"], 
                "width": region["bounding_box"]["width"],
                "height": region["bounding_box"]["height"]
            })
        
        # 调用 IOPaint 服务
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/inpaint-regions-async",
                json={
                    "image": image_b64,
                    "regions": regions,
                    "task_id": task_id,
                    "enable_progress": True
                }
            ) as response:
                return await response.json()
```

#### WebSocket 进度集成 (后端)
```python
# 后端 WebSocket 中继到前端
# 文件: backend/app/infrastructure/api/websocket_routes.py

from fastapi import WebSocket
import websockets
import json

async def relay_iopaint_progress(websocket: WebSocket, task_id: str):
    """通过后端 WebSocket 将 IOPaint 进度中继到前端。"""
    iopaint_ws_url = f"ws://iopaint-service:8081/api/v1/ws/progress/{task_id}"
    
    try:
        async with websockets.connect(iopaint_ws_url) as iopaint_ws:
            async for message in iopaint_ws:
                # 将进度中继到前端
                await websocket.send_text(message)
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"进度跟踪错误: {str(e)}"
        }))
```

### 带自定义参数的高级用法
```python
# 带自定义参数的高级修复
response = requests.post(
    'http://localhost:8081/api/v1/inpaint-regions-async',
    json={
        "image": image_b64,
        "regions": regions,
        "task_id": task_id,
        "enable_progress": True,
        # 高级 IOPaint 参数
        "sd_seed": 42,
        "sd_steps": 20,
        "sd_strength": 0.8,
        "sd_guidance_scale": 7.5,
        "hd_strategy": "Original",
        "hd_strategy_crop_trigger_size": 1024,
        "hd_strategy_crop_margin": 32
    }
)
```

## 🏗️ 开发

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

### 测试
```bash
# 测试健康端点
curl http://localhost:8081/api/v1/health

# 查看 API 文档
open http://localhost:8081/docs
```

## 📊 监控

### 健康检查端点
`/api/v1/health` 端点提供服务状态：
```json
{
  "status": "healthy",
  "message": "IOPaint service is running",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### 服务指标
响应头包含处理指标：
- `X-Processing-Time`: 处理持续时间（秒）
- `X-Regions-Count`: 处理的区域数量
- `X-Total-Area`: 处理的总面积（像素）
- `X-Timestamp`: 处理时间戳

## 🔧 故障排除

### 常见问题

1. **服务启动超时**
   - 增加启动超时时间（首次运行需要下载模型）
   - 检查网络连接用于模型下载
   - 确保有足够的磁盘空间用于模型缓存

2. **内存不足错误**
   - 启用 `IOPAINT_LOW_MEM=true`
   - 启用 `IOPAINT_CPU_OFFLOAD=true`
   - 减少 `MAX_IMAGE_SIZE`

3. **处理速度慢**
   - 使用 `IOPAINT_DEVICE=cuda` 进行 GPU 加速
   - 考虑使用更快的模型（fcf、zits）以牺牲质量换取速度
   - 降低图像分辨率

### 日志
服务日志提供处理的详细信息：
```bash
docker logs iopaint-service
```

## 🌟 集成到现有项目

### 基本集成步骤

1. **添加到现有 Docker Compose**
```yaml
# 在你的 docker-compose.yml 中添加
iopaint-service:
  image: iopaint-service:latest
  ports:
    - "8081:8081"
  environment:
    - IOPAINT_MODEL=lama
    - IOPAINT_DEVICE=cpu
```

2. **Python 集成示例**
```python
import aiohttp
import base64

class IOPaintClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
    
    async def remove_text_regions(self, image_path, regions):
        """从图像中移除指定区域的文本"""
        with open(image_path, 'rb') as f:
            image_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/inpaint-regions",
                json={"image": image_b64, "regions": regions}
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"请求失败: {response.status}")

# 使用示例
client = IOPaintClient()
regions = [{"x": 100, "y": 50, "width": 200, "height": 30}]
result = await client.remove_text_regions("input.jpg", regions)
```

3. **JavaScript/Node.js 集成示例**
```javascript
const axios = require('axios');
const fs = require('fs');

class IOPaintClient {
    constructor(baseUrl = 'http://localhost:8081') {
        this.baseUrl = baseUrl;
    }
    
    async removeTextRegions(imagePath, regions) {
        const imageBuffer = fs.readFileSync(imagePath);
        const imageB64 = imageBuffer.toString('base64');
        
        const response = await axios.post(
            `${this.baseUrl}/api/v1/inpaint-regions`,
            {
                image: imageB64,
                regions: regions
            },
            { responseType: 'arraybuffer' }
        );
        
        return response.data;
    }
}

// 使用示例
const client = new IOPaintClient();
const regions = [{x: 100, y: 50, width: 200, height: 30}];
const result = await client.removeTextRegions('input.jpg', regions);
fs.writeFileSync('output.png', result);
```

## 📈 性能优化建议

### 服务器配置
- **CPU**: 建议 4 核心以上
- **内存**: 建议 8GB 以上（LAMA 模型需要较多内存）
- **存储**: SSD 存储以提高模型加载速度
- **GPU**: NVIDIA GPU（支持 CUDA）可显著提升处理速度

### 生产环境部署
```yaml
# 生产环境 docker-compose.yml 示例
version: '3.8'
services:
  iopaint-service:
    build: ./iopaint-service
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    environment:
      - IOPAINT_MODEL=lama
      - IOPAINT_DEVICE=cuda
      - IOPAINT_LOW_MEM=false
      - MAX_IMAGE_SIZE=2048
    volumes:
      - iopaint_cache:/root/.cache/huggingface
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 📝 许可证

本服务是 LabelTool 项目的一部分，遵循相同的许可条款。