# Docker 部署指南

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

本文档介绍如何使用 Docker 来运行 LabelTool 项目。

## 🚀 快速开始

### 1. 克隆项目并进入目录
```bash
git clone <your-repo-url>
cd labeltool
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
# 构建并启动所有服务（后端优先启动，前端等待后端健康检查通过后启动）
docker-compose up --build

# 或者在后台运行
docker-compose up --build -d
```

### 4. 访问应用
- 前端访问地址: http://localhost:3000
- 后端API文档: http://localhost:8000/docs
- 后端API状态: http://localhost:8000/

## 📋 服务说明

### 后端服务 (labeltool-backend)
- **端口**: 8000
- **技术栈**: Python 3.11.13 + FastAPI + PaddleOCR
- **功能**: 提供 OCR 文字检测和图像处理 API
- **健康检查**: 自动检查服务状态，启动后约需 40 秒完成初始化

### 前端服务 (labeltool-frontend)
- **端口**: 3000
- **技术栈**: React 18 + TypeScript + Nginx
- **功能**: 提供用户界面和图像标注功能
- **依赖**: 等待后端服务健康检查通过后才启动

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
docker-compose logs backend
docker-compose logs frontend
```

### 单独构建服务
```bash
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
docker-compose restart backend
docker-compose restart frontend
```

## 📁 数据持久化

项目使用 Docker 卷来持久化重要数据：

- `backend_uploads`: 上传的图像文件
- `backend_processed`: 处理后的图像文件
- `backend_exports`: 导出的文件
- `backend_logs`: 应用日志

### 卷管理命令
```bash
# 查看所有卷
docker volume ls

# 查看特定卷详细信息
docker volume inspect labeltool_backend_uploads

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
- `PROCESSED_DIR`: 处理后文件目录 (默认: processed)

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
# 查看详细日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重新构建镜像
docker-compose build --no-cache
```

### 4. 权限问题
```bash
# 确保目录权限正确
sudo chown -R $USER:$USER uploads processed exports logs
```

### 5. 网络连接问题
```bash
# 检查网络连接
docker network ls
docker network inspect labeltool_labeltool-network
```

## 🔄 开发模式

如果需要在开发过程中修改代码：

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
# 备份卷数据
docker run --rm -v labeltool_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

如有问题，请查看日志文件或联系开发团队。