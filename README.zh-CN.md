# LabelTool - 智能文本检测与移除工具

**🌍 中文 | [日本語](README.ja.md) | [English](README.md)**

一个全面的基于Web的智能文本注释和处理工具，提供完整的文本处理工作流：从自动检测到手动调整、智能移除和智能文本生成。采用现代微服务架构构建，具备高可扩展性和可维护性。

## 🎯 项目概览

LabelTool 是一个生产级智能文本处理平台，将尖端AI模型与直观用户界面相结合，提供专业的文本注释和移除功能：

### 🔄 完整处理工作流
1. **自动文本检测** 使用 PaddleOCR 实现高精度检测
2. **手动文本区域调整** 提供直观的拖拽界面  
3. **高级修复文本移除** 使用 IOPaint 实现无缝背景保护
4. **文本生成与替换** 允许用户在处理后的图像中添加自定义文本
5. **双模式编辑系统** 同时支持 OCR 编辑和处理图像文本生成

### 🏗️ 现代架构
- **微服务架构**: 独立服务提供更好的可扩展性和资源管理
- **领域驱动设计**: 后端采用 DDD 模式，清晰的关注点分离
- **实时处理**: 基于 WebSocket 的长时间任务进度跟踪
- **生产就绪**: Docker 容器化，全面监控和错误处理

## ✨ 核心特性

### 🤖 高级AI功能
- **高精度OCR**: PaddleOCR 配合 PP-OCRv5 模型实现精准文本检测
- **最先进的修复技术**: IOPaint LAMA 模型实现无缝背景保护
- **智能字体分析**: 自动检测字体属性用于文本生成
- **智能图像缩放**: 大图像自动优化处理

### 🎨 交互式用户体验
- **交互式画布**: Konva.js 驱动的拖拽文本区域编辑
- **双模式系统**: OCR 纠错和文本生成的独立编辑模式
- **高级撤销/重做**: 基于命令模式的操作历史，支持模式分离
- **实时进度**: 处理过程中的实时 WebSocket 更新
- **响应式设计**: 针对桌面和平板设备优化

### 🏗️ 技术卓越性
- **微服务架构**: 独立服务支持可扩展性
- **生产就绪**: 全面的错误处理、健康监控和诊断
- **Docker 原生**: 完整容器化，持久化模型缓存
- **性能优化**: GPU 加速、内存管理和智能资源使用

## 🚀 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆仓库
git clone <repository-url>
cd labeltool-fakeDataGenerator

# 启动所有服务
docker-compose up --build

# 访问应用程序
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000/docs
# IOPaint 服务: http://localhost:8081/docs
```

就是这样！应用程序将完全运行，包含所有 AI 模型和依赖项。

### 性能说明
- **首次运行**: 下载 AI 模型（约2-3GB），可能需要5-10分钟
- **后续运行**: 模型已缓存，启动速度更快
- **GPU 支持**: 启用 CUDA 以获得更快的处理速度（请参阅配置）

## 🏗️ 架构概览

### 微服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端服务      │    │    后端服务     │    │ IOPaint 服务   │
│   (React App)   │────│  (FastAPI)      │────│   (FastAPI)     │
│   端口: 3000    │    │   端口: 8000    │    │   端口: 8081    │  
│                 │    │                 │    │                 │
│ • 用户界面      │    │ • OCR 检测      │    │ • 文本移除      │
│ • 画布编辑器    │    │ • 会话管理      │    │ • LAMA 模型     │
│ • 文件上传      │    │ • API 网关      │    │ • 图像修复      │
│ • 状态管理      │    │ • 业务逻辑      │    │ • 进度跟踪      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        └─────────── WebSocket & HTTP/REST ───────────────┘
```

### 服务职责

**前端服务**:
- React 18 + TypeScript + Vite
- 交互式 Konva.js 画布用于区域编辑
- Zustand 状态管理与撤销/重做系统
- 实时 WebSocket 进度跟踪
- 响应式 Tailwind CSS 设计

**后端服务**:
- FastAPI + Python 3.11 与 DDD 架构
- PaddleOCR 集成用于文本检测
- 会话和任务管理
- IOPaint 服务客户端集成
- 带有全面文档的 RESTful API

**IOPaint 服务** ([📖 详细文档](iopaint-service/README.zh-CN.md)):
- 独立的 FastAPI 微服务
- IOPaint 1.6.0 配合 LAMA 模型
- 高级图像修复功能
- 资源监控和优化
- 独立部署能力

## 🛠️ 技术栈

### 前端技术
- **框架**: React 18 + TypeScript + Vite
- **画布**: Konva.js + react-konva 用于交互式编辑
- **状态管理**: Zustand 配合持久化和撤销/重做
- **样式**: Tailwind CSS 配合自定义组件
- **HTTP 客户端**: Axios 配合拦截器
- **文件上传**: React-Dropzone 配合进度跟踪
- **测试**: Jest + React Testing Library

### 后端技术
- **框架**: FastAPI + Python 3.11 + Pydantic v2
- **OCR 引擎**: PaddleOCR（最新版配合 PP-OCRv5 模型）
- **图像处理**: OpenCV + Pillow + NumPy
- **架构**: 领域驱动设计（DDD）
- **异步处理**: aiohttp + WebSocket 支持
- **配置**: Pydantic Settings 配合环境变量
- **日志**: Loguru 配合结构化日志

### IOPaint 服务技术
- **框架**: FastAPI + Python 3.11
- **AI 模型**: IOPaint 1.6.0 配合 LAMA 修复模型
- **图像处理**: 高级缩放和优化
- **监控**: 资源跟踪和诊断
- **错误处理**: 智能重试和恢复机制

### 基础设施与DevOps
- **容器化**: Docker + Docker Compose
- **模型缓存**: AI 模型的持久化卷
- **网络**: 桥接网络配合服务发现
- **健康监控**: 全面的健康检查
- **卷管理**: 图像和缓存的共享存储

## 🎯 用户工作流

### 1. 基本文本移除工作流
```
上传图像 → OCR检测 → 手动调整 → AI修复 → 下载结果
   ↓         ↓        ↓        ↓       ↓
 验证     文本区域   拖拽操作  LAMA模型  PNG导出
```

### 2. 高级文本生成工作流
```
上传图像 → OCR检测 → AI修复 → 文本生成 → 下载结果
   ↓         ↓       ↓        ↓         ↓
 验证     文本区域  背景移除  字体分析   增强图像
                            + 定位
```

### 3. 双模式编辑系统

**OCR模式**:
- 编辑检测到的文本内容
- 调整文本区域边界
- 纠正OCR识别错误
- 适用于文本注释和纠错

**处理模式**:
- 使用修复后的背景图像
- 添加智能定位的自定义文本
- 字体感知的文本渲染
- 适用于文本替换和增强

## 🔌 API 文档

### 主后端 API（端口 8000）

**会话管理**:
```bash
POST   /api/v1/sessions                    # 创建会话并进行OCR检测
GET    /api/v1/sessions/{id}               # 获取会话详情
PUT    /api/v1/sessions/{id}/regions       # 更新文本区域（双模式）
DELETE /api/v1/sessions/{id}               # 清理会话和文件
```

**处理端点**:
```bash
POST   /api/v1/sessions/{id}/process-async # 启动异步文本移除
GET    /api/v1/tasks/{id}/status           # 获取处理状态
POST   /api/v1/tasks/{id}/cancel           # 取消处理任务
```

**文本生成**:
```bash
POST   /api/v1/sessions/{id}/generate-text # 在区域中生成文本
POST   /api/v1/sessions/{id}/preview-text  # 预览文本生成
```

**文件操作**:
```bash
GET    /api/v1/sessions/{id}/image         # 获取原始图像
GET    /api/v1/sessions/{id}/result        # 下载处理结果
```

### IOPaint 服务 API（端口 8081）

详细的 IOPaint 服务文档，请参阅：**[IOPaint 服务文档](iopaint-service/README.zh-CN.md)**

**核心端点**:
```bash
GET    /api/v1/health                      # 健康检查及诊断
GET    /api/v1/info                        # 服务信息
POST   /api/v1/inpaint-regions            # 文本区域修复
POST   /api/v1/inpaint-regions-json       # 修复及统计信息
```

## 💻 开发设置

### 本地开发

**先决条件**:
- Docker & Docker Compose（推荐）
- Python 3.11+ & Node.js 18+（用于本地开发）
- Git 版本控制

**选项1: Docker 开发**
```bash
# 全栈开发
docker-compose up --build

# 仅后端
docker-compose up backend iopaint-service

# 前端开发服务器
cd frontend && npm run dev  # 端口5173，支持热重载
```

**选项2: 本地开发**
```bash
# 后端设置
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# IOPaint 服务设置（新终端）
cd iopaint-service
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload

# 前端设置（新终端）
cd frontend
npm install
npm run dev
```

### 测试

**后端测试**:
```bash
cd backend
pytest tests/ -v --cov=app
```

**前端测试**:
```bash
cd frontend
npm run test        # 运行测试
npm run test:watch  # 监控模式
npm run test:coverage  # 覆盖率报告
```

**集成测试**:
```bash
# 使用Docker测试完整工作流
docker-compose up -d
curl http://localhost:8000/api/v1/health
curl http://localhost:8081/api/v1/health
```

## 🚢 生产部署

### Docker 生产设置

```bash
# 生产构建
docker-compose -f docker-compose.prod.yml up --build -d

# GPU 支持
docker-compose -f docker-compose.gpu.yml up --build -d

# 监控服务
docker-compose logs -f
docker-compose ps
```

### 环境配置

**后端环境**:
```env
# OCR 配置
PADDLEOCR_DEVICE=cpu          # cpu/cuda
PADDLEOCR_LANG=en             # 语言支持

# IOPaint 服务
IOPAINT_SERVICE_URL=http://iopaint-service:8081
IOPAINT_TIMEOUT=300           # 处理超时

# 应用设置
MAX_FILE_SIZE=52428800        # 50MB最大上传
LOG_LEVEL=INFO                # 日志级别
```

**IOPaint 服务环境**:
```env
# 模型配置
IOPAINT_MODEL=lama            # AI模型选择
IOPAINT_DEVICE=cpu            # cpu/cuda/mps
IOPAINT_LOW_MEM=true          # 内存优化

# 性能设置
MAX_IMAGE_SIZE=2048           # 最大尺寸
REQUEST_TIMEOUT=300           # 处理超时
```

## 📊 监控与可观测性

### 健康监控

**服务健康检查**:
```bash
# 主应用健康检查
curl http://localhost:8000/api/v1/health

# IOPaint 服务健康检查
curl http://localhost:8081/api/v1/health

# Docker 健康状态
docker-compose ps
```

**处理指标**:
- 通过 WebSocket 实时进度跟踪
- 处理时间和资源使用情况
- 错误率和重试统计
- 模型性能指标

### 日志记录

**结构化日志**:
- 生产环境JSON格式日志
- 请求/响应跟踪
- 错误跟踪及堆栈跟踪
- 性能指标日志

**日志访问**:
```bash
# 查看服务日志
docker-compose logs -f backend
docker-compose logs -f iopaint-service
docker-compose logs -f frontend

# 导出日志
docker-compose logs --no-color > application.log
```

## 🔧 配置与自定义

### OCR 配置

**PaddleOCR 设置**:
```python
OCR_CONFIG = {
    "det_db_thresh": 0.3,        # 检测阈值
    "det_db_box_thresh": 0.6,    # 边界框阈值
    "det_limit_side_len": 1920,  # 最大图像尺寸
    "use_angle_cls": True,       # 文本角度分类
    "lang": "en"                 # 语言支持
}
```

### IOPaint 配置

**模型选项**:
- **lama**（默认）: 最佳质量修复
- **ldm**: 潜在扩散模型
- **zits**: 快速处理
- **mat**: 掩码感知Transformer
- **fcf**: 傅里叶卷积
- **manga**: 专门用于动漫/漫画

**性能调优**:
```env
IOPAINT_LOW_MEM=true          # 在内存有限时启用
IOPAINT_CPU_OFFLOAD=true      # CPU/GPU负载均衡
MAX_IMAGE_SIZE=2048           # 减少以提高处理速度
```

## 🛠️ 故障排除

### 常见问题

**1. 服务启动问题**
```bash
# 检查Docker状态
docker --version
docker-compose --version

# 查看服务日志
docker-compose logs backend
docker-compose logs iopaint-service

# 重启服务
docker-compose restart
```

**2. 模型下载问题**
```bash
# 检查网络连接
curl -I https://huggingface.co

# 清除模型缓存
rm -rf volumes/huggingface_cache/*
rm -rf volumes/paddlex_cache/*

# 使用新模型重建
docker-compose down -v
docker-compose up --build
```

**3. 性能问题**
```bash
# 启用GPU支持
docker-compose -f docker-compose.gpu.yml up

# 减少图像大小限制
# 编辑环境变量:
# MAX_IMAGE_SIZE=1024
# MAX_FILE_SIZE=10485760  # 10MB
```

**4. 内存问题**
```bash
# 启用低内存模式
# IOPaint 服务环境:
IOPAINT_LOW_MEM=true
IOPAINT_CPU_OFFLOAD=true

# 减少并发处理
MAX_CONCURRENT_TASKS=1
```

### 获取帮助

**日志和诊断**:
```bash
# 生成诊断报告
docker-compose logs --no-color > diagnostic.log
docker-compose ps >> diagnostic.log
docker system df >> diagnostic.log

# 检查资源使用情况
docker stats
```

**常见解决方案**:
- 首次运行由于模型下载需要更长时间
- 如果内存有限，请使用较小的图像
- 启用GPU支持以获得更快的处理速度
- 检查防火墙设置以获取端口访问权限

## 📖 附加文档

- **[IOPaint 服务](iopaint-service/README.zh-CN.md)** - 详细服务文档
- **[Docker 部署](DOCKER.md)** - 完整部署指南
- **[API 参考](http://localhost:8000/docs)** - 交互式API文档
- **[开发指南](docs/DEVELOPMENT.md)** - 贡献指南

## 🤝 贡献

我们欢迎贡献！请查看我们的贡献指南了解以下详情：
- 代码风格和标准
- 测试要求
- 拉取请求流程
- 问题报告

## 📝 许可证

该项目在 MIT 许可证下授权 - 详情请参阅 LICENSE 文件。

## 🙏 致谢

- **PaddleOCR 团队** 提供出色的 OCR 模型
- **IOPaint 开发者** 提供最先进的修复功能
- **React & FastAPI 社区** 提供强大的框架
- **Docker** 提供容器化支持