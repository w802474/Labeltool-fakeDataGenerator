# LabelTool - 智能文本检测与移除工具

*[English](README.md) | [中文文档](README.zh-CN.md) | [日本語ドキュメント](README.ja.md)*

一个功能全面的基于Web的智能文本处理工具，具有**双模式编辑系统**：OCR文本检测/校正和高级文本生成与AI智能修复。

## ✨ 核心功能

- 🤖 **高级OCR**：采用PaddleOCR的PP-OCRv5模型，实现高精度文本检测
- 🖼️ **AI文本移除**：IOPaint LAMA模型实现无缝背景保留
- ✨ **文本生成**：自定义文本渲染，具备字体分析和精确定位
- 🎨 **交互式画布**：Konva.js驱动的拖拽式文本区域编辑
- ↩️ **双重撤销/重做**：OCR和处理模式的独立命令历史
- 🐳 **Docker就绪**：全栈容器化，具备持久模型缓存
- 📱 **响应式设计**：在桌面和平板设备上无缝工作

## 🚀 快速开始（推荐）

### 使用Docker Compose（最简单）

```bash
# 克隆并启动应用程序
git clone <repository-url>
cd labeltool
docker-compose up --build

# 访问应用程序
# 前端：http://localhost:3000
# 后端API：http://localhost:8000
# API文档：http://localhost:8000/docs
```

就这样！应用程序将完全运行，包含所有依赖项。

## 💻 本地开发设置

### 前置要求
- Docker & Docker Compose（推荐）
- *或者* Python 3.11+ & Node.js 18+（用于本地开发）

### 选项1：Docker开发
```bash
# 仅运行后端
docker-compose up backend

# 为开发运行特定服务
cd frontend && npm run dev  # 前端开发服务器在 :5173
```

### 选项2：本地开发
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 🎯 使用方法

1. **上传图片**：拖拽图片文件（JPEG、PNG、WEBP，最大50MB）
2. **自动检测**：PaddleOCR自动检测文本区域
3. **编辑区域**：
   - **OCR模式**：调整边界，校正文本
   - **处理模式**：添加自定义文本用于生成
4. **处理**：使用AI修复移除文本（IOPaint LAMA模型）
5. **生成文本**：使用字体感知定位渲染自定义文本
6. **下载**：获取处理后的图片

## 🛠️ 技术栈

**前端**：React 18 + TypeScript + Konva.js + Zustand + Tailwind CSS  
**后端**：FastAPI + Python 3.11 + PaddleOCR + IOPaint + Docker  
**AI模型**：PP-OCRv5（文本检测）+ LAMA（修复）

## 🔧 API端点

```bash
# 创建会话并上传图片
POST /api/v1/sessions

# 处理文本移除
POST /api/v1/sessions/{id}/process

# 生成自定义文本
POST /api/v1/sessions/{id}/generate-text

# 下载结果
GET /api/v1/sessions/{id}/result
```

完整API文档：http://localhost:8000/docs

## 📖 文档

- [Docker部署指南](DOCKER.zh-CN.md) - 完整的Docker设置和部署说明

## 🛠️ 故障排除

**Docker问题**：
```bash
# 检查Docker是否运行
docker --version
docker-compose --version

# 查看日志
docker-compose logs backend
docker-compose logs frontend
```

**性能**：首次运行会下载AI模型（~2GB）。后续运行会更快。

**内存**：大图片会自动调整大小。如果遇到内存问题，请使用较小的图片。