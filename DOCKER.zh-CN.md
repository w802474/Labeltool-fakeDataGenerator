# Docker 部署指南

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

本文档介绍如何使用 Docker 来运行 **LabelTool - Intelligent Text Detection & Removal Tool** 项目的**微服务架构**（3个服务：前端、后端、IOPaint服务）。

## 🚀 快速开始

### 1. 克隆项目并进入目录
```bash
git clone <your-repo-url>
cd Labeltool-fakeDataGenerator
```

### 2. 环境配置（可选）
```bash
# 复制环境变量配置文件
cp .env.example .env

# 根据需要修改 .env 文件中的配置
nano .env
```

### 3. 构建并启动服务
```bash
# 构建并启动所有3个服务（IOPaint → 后端 → 前端 启动顺序）
docker-compose up --build

# 或者在后台运行
docker-compose up --build -d
```

### 4. 访问应用
- **前端界面**: http://localhost:3000 (用户界面)
- **后端API**: http://localhost:8000/docs (主要API文档)
- **IOPaint服务**: http://localhost:8081/docs (文本移除服务文档)
- **后端状态**: http://localhost:8000/ (API健康状态)
- **IOPaint状态**: http://localhost:8081/api/v1/health (IOPaint健康状态)

## 📋 微服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     前端        │    │     后端        │    │  IOPaint服务    │
│   (React应用)   │────│   (FastAPI)     │────│   (FastAPI)     │
│   端口: 3000    │    │   端口: 8000    │    │   端口: 8081    │  
│                 │    │                 │    │                 │
│ - 用户界面      │    │ - OCR文本检测   │    │ - 文本移除      │
│ - 画布编辑器    │    │ - 会话管理      │    │ - LAMA模型      │
│ - 文件上传      │    │ - API网关       │    │ - 图像修复      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🎯 IOPaint服务 (labeltool-iopaint)
- **端口**: 8081
- **技术栈**: Python 3.11 + FastAPI 0.108.0 + IOPaint 1.6.0 + LAMA模型
- **依赖**: IOPaint、HuggingFace Hub、OpenCV、Pillow 9.5.0
- **功能**: 使用AI进行高级文本修复和移除
- **健康检查**: 初始化约需60秒（首次运行下载LAMA模型约2GB）
- **数据卷**: 持久化HuggingFace模型缓存（约2GB）
- **服务依赖**: 无（完全独立的服务）

### 🔧 后端服务 (labeltool-backend)
- **端口**: 8000
- **技术栈**: Python 3.11 + FastAPI 0.108.0 + PaddleOCR + Pydantic v2
- **依赖**: PaddleOCR、PaddlePaddle、OpenCV、Pillow 9.5.0、WebSockets
- **功能**: OCR文本检测、会话管理、API编排
- **健康检查**: 初始化约需40秒（首次运行下载PaddleOCR模型）
- **数据卷**: 持久化PaddleX模型缓存、上传文件、处理文件、日志
- **服务依赖**: 需要IOPaint服务健康才能启动

### 🎨 前端服务 (labeltool-frontend)
- **端口**: 3000（Nginx代理）
- **技术栈**: React 18 + TypeScript + Vite + Konva.js + Zustand
- **依赖**: React-Konva、Axios、Tailwind CSS、Lucide React
- **功能**: 交互式画布编辑、拖拽文件上传、实时进度显示
- **构建**: 多阶段Docker构建，Nginx提供静态文件服务
- **服务依赖**: 需要后端服务健康检查通过后才启动

## 🔧 Docker 命令参考

### 服务管理
```bash
# 启动服务
docker-compose up

# 后台启动服务
docker-compose up -d

# 重新构建并启动
docker-compose up --build

# 停止服务
docker-compose down

# 停止服务并删除卷
docker-compose down -v

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs iopaint-service  # IOPaint服务日志
docker-compose logs backend          # 后端服务日志
docker-compose logs frontend         # 前端服务日志

# 实时跟踪日志
docker-compose logs -f iopaint-service
```

### 单独构建服务
```bash
# 只构建IOPaint服务
docker-compose build iopaint-service

# 只构建后端
docker-compose build backend

# 只构建前端
docker-compose build frontend
```

### 服务重启
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart iopaint-service
docker-compose restart backend
docker-compose restart frontend
```

## 📁 数据持久化

项目使用 Docker 卷来持久化重要数据：

### 后端服务卷
- `backend_uploads`: 上传的图像文件
- `backend_removal`: 文本移除处理后的图像文件
- `backend_generated`: 文本生成结果图像文件
- `backend_exports`: 导出的文件
- `backend_logs`: 应用日志
- `paddlex_cache`: PaddleOCR模型缓存

### IOPaint服务卷
- `huggingface_cache`: IOPaint LAMA模型缓存（~2GB）
- `iopaint_temp`: 临时处理文件

### 卷管理命令
```bash
# 查看所有卷
docker volume ls

# 查看特定卷详细信息
docker volume inspect labeltool-fakedatagenerator_backend_uploads
docker volume inspect labeltool-fakedatagenerator_huggingface_cache
docker volume inspect labeltool-fakedatagenerator_paddlex_cache

# 删除未使用的卷
docker volume prune
```

## ⚙️ 环境变量配置

主要环境变量说明：

### API 配置
- `API_HOST`: API 监听地址 (默认: 0.0.0.0)
- `API_PORT`: API 端口 (默认: 8000)
- `LOG_LEVEL`: 日志级别 (默认: INFO)

### 文件处理配置
- `MAX_FILE_SIZE`: 最大文件大小 (默认: 50MB)
- `UPLOAD_DIR`: 上传目录 (默认: uploads)
- `REMOVAL_DIR`: 文本移除结果目录 (默认: removal)
- `GENERATED_DIR`: 文本生成结果目录 (默认: generated)

### OCR 配置
- `PADDLEOCR_DEVICE`: 设备类型 (cpu/cuda, 默认: cpu)
- `PADDLEOCR_LANG`: OCR 语言 (默认: en)

### 跨域配置
- `CORS_ORIGINS`: 允许的前端域名

## 🐛 故障排除

### 1. 端口冲突
如果端口 3000 或 8000 被占用，修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "3001:80"  # 前端改为 3001
  - "8001:8000"  # 后端改为 8001
```

### 2. 内存不足
PaddleOCR 和图像处理需要较多内存，确保 Docker 有足够内存分配（建议 4GB+）。

### 3. 服务启动失败
```bash
# 查看所有服务的详细日志
docker-compose logs -f iopaint-service
docker-compose logs -f backend
docker-compose logs -f frontend

# 重新构建镜像
docker-compose build --no-cache

# 检查服务健康状态
docker-compose ps
```

### 4. IOPaint服务问题
```bash
# 检查IOPaint服务日志
docker-compose logs -f iopaint-service

# 仅重启IOPaint服务
docker-compose restart iopaint-service

# 检查IOPaint服务健康状态
curl http://localhost:8081/api/v1/health
```

### 5. 权限问题
```bash
# 确保目录权限正确
sudo chown -R $USER:$USER uploads removal generated exports logs
```

### 6. 网络连接问题
```bash
# 检查网络连接
docker network ls
docker network inspect labeltool-fakedatagenerator_labeltool-network

# 测试服务连通性
curl http://localhost:3000  # 前端
curl http://localhost:8000/api/v1/health  # 后端
curl http://localhost:8081/api/v1/health  # IOPaint服务
```

## 🔄 开发模式

如果需要在开发过程中修改代码：

### IOPaint服务开发
```bash
# 停止容器中的IOPaint服务
docker-compose stop iopaint-service

# 本地运行IOPaint服务进行开发
cd iopaint-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

### 后端开发
```bash
# 停止容器中的后端
docker-compose stop backend

# 本地运行后端进行开发
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发
```bash
# 停止容器中的前端
docker-compose stop frontend

# 本地运行前端进行开发
cd frontend
npm run dev
```

### 混合开发模式
```bash
# Docker运行IOPaint和后端，本地运行前端
docker-compose up iopaint-service backend
cd frontend && npm run dev

# 仅Docker运行IOPaint，本地运行后端和前端
docker-compose up iopaint-service
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

## 📊 监控和日志

### 健康检查
所有服务都配置了健康检查：
```bash
# 查看服务健康状态
docker-compose ps
```

### 日志查看
```bash
# 实时查看所有日志
docker-compose logs -f

# 查看最近的日志
docker-compose logs --tail=100

# 只查看错误日志
docker-compose logs | grep ERROR
```

## 🚀 生产环境部署

### 1. 修改环境变量
```bash
# 生产环境配置
API_RELOAD=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
```

### 2. 使用外部数据库（如需要）
修改 `docker-compose.yml` 添加数据库服务。

### 3. 配置反向代理
建议在生产环境中使用 Nginx 或其他反向代理。

### 4. SSL 证书
配置 HTTPS 证书以确保安全访问。

## 📝 更新和维护

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up --build -d

# 清理旧镜像
docker image prune
```

### 备份数据
```bash
# 备份后端上传和结果文件
docker run --rm -v labeltool-fakedatagenerator_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_backend_removal:/data -v $(pwd):/backup alpine tar czf /backup/removal-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_backend_generated:/data -v $(pwd):/backup alpine tar czf /backup/generated-backup.tar.gz -C /data .

# 备份模型缓存（对快速启动很重要）
docker run --rm -v labeltool-fakedatagenerator_huggingface_cache:/data -v $(pwd):/backup alpine tar czf /backup/iopaint-models-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_paddlex_cache:/data -v $(pwd):/backup alpine tar czf /backup/paddleocr-models-backup.tar.gz -C /data .
```

如有问题，请查看日志文件或联系开发团队。