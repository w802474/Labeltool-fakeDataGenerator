# LabelTool - Intelligent Text Detection & Removal Tool

*[中文文档](#中文文档) | [日本語ドキュメント](#日本語ドキュメント)*

A comprehensive web-based tool for intelligent text processing with **dual-mode editing system**: OCR text detection/correction and advanced text generation with AI-powered inpainting.

## ✨ Key Features

- 🤖 **Advanced OCR**: PaddleOCR with PP-OCRv5 models for high-precision text detection
- 🖼️ **AI Text Removal**: IOPaint LAMA model for seamless background preservation
- ✨ **Text Generation**: Custom text rendering with font analysis and precise positioning
- 🎨 **Interactive Canvas**: Konva.js-powered drag-and-drop text region editing
- ↩️ **Dual Undo/Redo**: Separate command histories for OCR and processed modes
- 🐳 **Docker Ready**: Full-stack containerization with persistent model caching
- 📱 **Responsive Design**: Works seamlessly on desktop and tablet devices

## 🚀 Quick Start (Recommended)

### Using Docker Compose (Easiest)

```bash
# Clone and start the application
git clone <repository-url>
cd labeltool
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! The application will be fully running with all dependencies.

## 💻 Local Development Setup

### Prerequisites
- Docker & Docker Compose (recommended)
- *OR* Python 3.11+ & Node.js 18+ (for local development)

### Option 1: Docker Development
```bash
# Run backend only
docker-compose up backend

# Run specific service for development
cd frontend && npm run dev  # Frontend dev server on :5173
```

### Option 2: Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 🎯 How to Use

1. **Upload Image**: Drag and drop an image (JPEG, PNG, WEBP, max 50MB)
2. **Auto Detection**: PaddleOCR automatically detects text regions
3. **Edit Regions**: 
   - **OCR Mode**: Adjust boundaries, correct text
   - **Processed Mode**: Add custom text for generation
4. **Process**: Remove text with AI inpainting (IOPaint LAMA model)
5. **Generate Text**: Render custom text with font-aware positioning
6. **Download**: Get your processed image

## 🛠️ Technology Stack

**Frontend**: React 18 + TypeScript + Konva.js + Zustand + Tailwind CSS  
**Backend**: FastAPI + Python 3.11 + PaddleOCR + IOPaint + Docker  
**AI Models**: PP-OCRv5 (text detection) + LAMA (inpainting)

## 🔧 API Endpoints

```bash
# Create session with image upload
POST /api/v1/sessions

# Process text removal
POST /api/v1/sessions/{id}/process

# Generate custom text
POST /api/v1/sessions/{id}/generate-text

# Download result
GET /api/v1/sessions/{id}/result
```

Full API documentation: http://localhost:8000/docs

## 🛠️ Troubleshooting

**Docker issues**:
```bash
# Check if Docker is running
docker --version
docker-compose --version

# View logs
docker-compose logs backend
docker-compose logs frontend
```

**Performance**: First run downloads AI models (~2GB). Subsequent runs are much faster.

**Memory**: Large images are automatically resized. Use smaller images if you encounter memory issues.

---

# 中文文档

## 🚀 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆并启动应用
git clone <repository-url>
cd labeltool
docker-compose up --build

# 访问应用
# 前端：http://localhost:3000
# 后端 API：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

## ✨ 主要功能

- 🤖 **智能OCR识别**：使用 PaddleOCR PP-OCRv5 模型进行高精度文本检测
- 🖼️ **AI文本移除**：IOPaint LAMA 模型实现无缝背景保护
- ✨ **文本生成**：基于字体分析的精确文本渲染
- 🎨 **交互式画布**：Konva.js 驱动的拖拽式文本区域编辑
- ↩️ **双重撤销**：OCR 和处理模式分别的命令历史
- 🐳 **Docker 部署**：完整容器化，持久化模型缓存

## 🎯 使用方法

1. **上传图片**：拖拽上传图片（支持 JPEG、PNG、WEBP，最大 50MB）
2. **自动检测**：PaddleOCR 自动检测文本区域
3. **编辑区域**：
   - **OCR 模式**：调整边界，修正文本
   - **处理模式**：添加自定义文本用于生成
4. **处理**：使用 AI 修复技术移除文本（IOPaint LAMA 模型）
5. **生成文本**：智能字体感知的文本渲染
6. **下载**：获取处理后的图片

## 🛠️ 故障排除

**Docker 问题**：
```bash
# 检查 Docker 是否运行
docker --version
docker-compose --version

# 查看日志
docker-compose logs backend
docker-compose logs frontend
```

**性能提示**：首次运行会下载 AI 模型（约 2GB），后续运行会更快。

---

# 日本語ドキュメント

## 🚀 クイックスタート

### Docker Compose を使用（推奨）

```bash
# アプリケーションのクローンと起動
git clone <repository-url>
cd labeltool
docker-compose up --build

# アプリケーションへのアクセス
# フロントエンド：http://localhost:3000
# バックエンド API：http://localhost:8000
# API ドキュメント：http://localhost:8000/docs
```

## ✨ 主要機能

- 🤖 **高度なOCR**：PaddleOCR PP-OCRv5モデルによる高精度テキスト検出
- 🖼️ **AIテキスト除去**：IOPaint LAMAモデルによるシームレスな背景保護
- ✨ **テキスト生成**：フォント解析による精密なテキスト配置
- 🎨 **インタラクティブキャンバス**：Konva.jsによるドラッグ＆ドロップテキスト領域編集
- ↩️ **デュアル アンドゥ/リドゥ**：OCRとプロセスモード別のコマンド履歴
- 🐳 **Docker対応**：完全コンテナ化、永続的モデルキャッシング

## 🎯 使用方法

1. **画像アップロード**：画像をドラッグ＆ドロップ（JPEG、PNG、WEBP対応、最大50MB）
2. **自動検出**：PaddleOCRが自動的にテキスト領域を検出
3. **領域編集**：
   - **OCRモード**：境界調整、テキスト修正
   - **プロセスモード**：生成用カスタムテキスト追加
4. **処理**：AI修復技術でテキスト除去（IOPaint LAMAモデル）
5. **テキスト生成**：フォント認識テキストレンダリング
6. **ダウンロード**：処理済み画像の取得

## 🛠️ トラブルシューティング

**Dockerの問題**：
```bash
# Dockerが動作しているか確認
docker --version
docker-compose --version

# ログの確認
docker-compose logs backend
docker-compose logs frontend
```

**パフォーマンス**：初回実行時はAIモデルをダウンロード（約2GB）します。以降の実行はより高速になります。