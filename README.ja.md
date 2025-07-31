# LabelTool - インテリジェント文字検出・除去ツール

*[English](README.md) | [中文文档](README.zh-CN.md) | [日本語ドキュメント](README.ja.md)*

**デュアルモード編集システム**を備えた包括的なWebベースのインテリジェント文字処理ツール：OCR文字検出/修正とAI搭載インペインティングによる高度な文字生成。

## ✨ 主要機能

- 🤖 **高度なOCR**：PaddleOCRのPP-OCRv5モデルによる高精度文字検出
- 🖼️ **AI文字除去**：IOPaint LAMAモデルによるシームレスな背景保持
- ✨ **文字生成**：フォント分析と精密配置によるカスタム文字レンダリング
- 🎨 **インタラクティブキャンバス**：Konva.js駆動のドラッグアンドドロップ文字領域編集
- ↩️ **デュアル取り消し/やり直し**：OCRと処理モードの独立したコマンド履歴
- 🐳 **Docker対応**：永続的なモデルキャッシュを備えたフルスタックコンテナ化
- 📱 **レスポンシブデザイン**：デスクトップとタブレットデバイスでシームレスに動作

## 🚀 クイックスタート（推奨）

### Docker Composeの使用（最も簡単）

```bash
# アプリケーションをクローンして開始
git clone <repository-url>
cd labeltool
docker-compose up --build

# アプリケーションにアクセス
# フロントエンド：http://localhost:3000
# バックエンドAPI：http://localhost:8000
# APIドキュメント：http://localhost:8000/docs
```

これだけです！アプリケーションがすべての依存関係とともに完全に動作します。

## 💻 ローカル開発セットアップ

### 前提条件
- Docker & Docker Compose（推奨）
- *または* Python 3.11+ & Node.js 18+（ローカル開発用）

### オプション1：Docker開発
```bash
# バックエンドのみ実行
docker-compose up backend

# 開発用の特定サービスを実行
cd frontend && npm run dev  # フロントエンド開発サーバー :5173
```

### オプション2：ローカル開発
```bash
# バックエンド
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド（新しいターミナル）
cd frontend
npm install
npm run dev
```

## 🎯 使用方法

1. **画像アップロード**：画像をドラッグアンドドロップ（JPEG、PNG、WEBP、最大50MB）
2. **自動検出**：PaddleOCRが文字領域を自動検出
3. **領域編集**：
   - **OCRモード**：境界を調整、文字を修正
   - **処理モード**：生成用のカスタム文字を追加
4. **処理**：AIインペインティングで文字を除去（IOPaint LAMAモデル）
5. **文字生成**：フォント認識配置でカスタム文字をレンダリング
6. **ダウンロード**：処理された画像を取得

## 🛠️ 技術スタック

**フロントエンド**：React 18 + TypeScript + Konva.js + Zustand + Tailwind CSS  
**バックエンド**：FastAPI + Python 3.11 + PaddleOCR + IOPaint + Docker  
**AIモデル**：PP-OCRv5（文字検出）+ LAMA（インペインティング）

## 🔧 APIエンドポイント

```bash
# 画像アップロードでセッション作成
POST /api/v1/sessions

# 文字除去処理
POST /api/v1/sessions/{id}/process

# カスタム文字生成
POST /api/v1/sessions/{id}/generate-text

# 結果ダウンロード
GET /api/v1/sessions/{id}/result
```

完全なAPIドキュメント：http://localhost:8000/docs

## 📖 ドキュメント

- [Dockerデプロイメントガイド](DOCKER.ja.md) - 完全なDockerセットアップとデプロイメントガイド

## 🛠️ トラブルシューティング

**Dockerの問題**：
```bash
# Dockerが動作しているか確認
docker --version
docker-compose --version

# ログを表示
docker-compose logs backend
docker-compose logs frontend
```

**パフォーマンス**：初回実行時にAIモデルをダウンロードします（〜2GB）。その後の実行ははるかに高速です。

**メモリ**：大きな画像は自動的にリサイズされます。メモリ問題が発生した場合は、より小さな画像を使用してください。