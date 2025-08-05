# Docker デプロイメントガイド

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

このドキュメントは、Docker で **LabelTool - Intelligent Text Detection & Removal Tool** プロジェクトの**マイクロサービスアーキテクチャ**（3つのサービス：フロントエンド、バックエンド、IOPaintサービス）を実行する方法を説明します。

## 🚀 クイックスタート

### 1. プロジェクトをクローンしてディレクトリに移動
```bash
git clone <your-repo-url>
cd Labeltool-fakeDataGenerator
```

### 2. 環境設定（オプション）
```bash
# 環境変数設定ファイルをコピー
cp .env.example .env

# 必要に応じて.envファイルの設定を変更
nano .env
```

### 3. サービスをビルドして開始
```bash
# 全3サービスをビルドして開始（IOPaint → バックエンド → フロントエンド の起動順序）
docker-compose up --build

# またはバックグラウンドで実行
docker-compose up --build -d
```

### 4. アプリケーションにアクセス
- **フロントエンド**: http://localhost:3000 (ユーザーインターフェース)
- **バックエンドAPI**: http://localhost:8000/docs (メインAPIドキュメント)
- **IOPaintサービス**: http://localhost:8081/docs (テキスト除去サービスドキュメント)
- **バックエンドステータス**: http://localhost:8000/ (APIヘルス状態)
- **IOPaintステータス**: http://localhost:8081/api/v1/health (IOPaintヘルス状態)

## 📋 マイクロサービスアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   フロントエンド  │    │   バックエンド    │    │ IOPaintサービス  │
│  (Reactアプリ)   │────│   (FastAPI)     │────│   (FastAPI)     │
│   ポート: 3000   │    │   ポート: 8000   │    │   ポート: 8081   │  
│                 │    │                 │    │                 │
│ - ユーザーUI    │    │ - OCRテキスト検出│    │ - テキスト除去   │
│ - キャンバス編集│    │ - セッション管理  │    │ - LAMAモデル     │
│ - ファイル上传   │    │ - APIゲートウェイ │    │ - インペインティング│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🎯 IOPaintサービス (labeltool-iopaint)
- **ポート**: 8081
- **技術スタック**: Python 3.11 + FastAPI 0.108.0 + IOPaint 1.6.0 + LAMAモデル
- **依存関係**: IOPaint、HuggingFace Hub、OpenCV、Pillow 9.5.0
- **機能**: AIを使用した高度なテキストインペインティングと除去
- **ヘルスチェック**: 初期化約60秒（初回実行時LAMAモデル約2GBダウンロード）
- **ボリューム**: 永続HuggingFaceモデルキャッシュ（約2GB）
- **サービス依存関係**: なし（完全に独立したサービス）

### 🔧 バックエンドサービス (labeltool-backend)
- **ポート**: 8000
- **技術スタック**: Python 3.11 + FastAPI 0.108.0 + PaddleOCR + Pydantic v2
- **依存関係**: PaddleOCR、PaddlePaddle、OpenCV、Pillow 9.5.0、WebSockets
- **機能**: OCRテキスト検出、セッション管理、APIオーケストレーション
- **ヘルスチェック**: 初期化約40秒（初回実行時PaddleOCRモデルダウンロード）
- **ボリューム**: 永続PaddleXモデルキャッシュ、アップロード、処理済みファイル、ログ
- **サービス依存関係**: IOPaintサービスがヘルシーである必要があります

### 🎨 フロントエンドサービス (labeltool-frontend)
- **ポート**: 3000（Nginxプロキシ）
- **技術スタック**: React 18 + TypeScript + Vite + Konva.js + Zustand
- **依存関係**: React-Konva、Axios、Tailwind CSS、Lucide React
- **機能**: インタラクティブキャンバス編集、ドラッグ＆ドロップファイルアップロード、リアルタイム進捗
- **ビルド**: Nginxで静的ファイルを提供するマルチステージDockerビルド
- **サービス依存関係**: バックエンドサービスのヘルスチェック通過後にのみ開始

## 🔧 Docker コマンドリファレンス

### サービス管理
```bash
# サービス開始
docker-compose up

# バックグラウンドでサービス開始
docker-compose up -d

# 再ビルドして開始
docker-compose up --build

# サービス停止
docker-compose down

# サービス停止してボリューム削除
docker-compose down -v

# サービス状態確認
docker-compose ps

# サービスログ確認
docker-compose logs

# 特定サービスのログ確認
docker-compose logs iopaint-service  # IOPaintサービスログ
docker-compose logs backend          # バックエンドサービスログ
docker-compose logs frontend         # フロントエンドサービスログ

# リアルタイムでログを追跡
docker-compose logs -f iopaint-service
```

### 個別サービスビルド
```bash
# IOPaintサービスのみビルド
docker-compose build iopaint-service

# バックエンドのみビルド
docker-compose build backend

# フロントエンドのみビルド
docker-compose build frontend
```

### サービス再起動
```bash
# 全サービス再起動
docker-compose restart

# 特定サービス再起動
docker-compose restart iopaint-service
docker-compose restart backend
docker-compose restart frontend
```

## 📁 データ永続化

プロジェクトはDockerボリュームを使用して重要なデータを永続化します：

### バックエンドサービスボリューム
- `backend_uploads`: アップロードされた画像ファイル
- `backend_processed`: 処理済み画像ファイル
- `backend_exports`: エクスポートファイル
- `backend_logs`: アプリケーションログ
- `paddlex_cache`: PaddleOCRモデルキャッシュ

### IOPaintサービスボリューム
- `huggingface_cache`: IOPaint LAMAモデルキャッシュ（~2GB）
- `iopaint_temp`: 一時処理ファイル

### ボリューム管理コマンド
```bash
# 全ボリューム確認
docker volume ls

# 特定ボリュームの詳細確認
docker volume inspect labeltool-fakedatagenerator_backend_uploads
docker volume inspect labeltool-fakedatagenerator_huggingface_cache
docker volume inspect labeltool-fakedatagenerator_paddlex_cache

# 未使用ボリューム削除
docker volume prune
```

## ⚙️ 環境変数設定

主要な環境変数：

### API設定
- `API_HOST`: APIリスニングアドレス (デフォルト: 0.0.0.0)
- `API_PORT`: APIポート (デフォルト: 8000)
- `LOG_LEVEL`: ログレベル (デフォルト: INFO)

### ファイル処理設定
- `MAX_FILE_SIZE`: 最大ファイルサイズ (デフォルト: 50MB)
- `UPLOAD_DIR`: アップロードディレクトリ (デフォルト: uploads)
- `PROCESSED_DIR`: 処理済みファイルディレクトリ (デフォルト: processed)

### OCR設定
- `PADDLEOCR_DEVICE`: デバイスタイプ (cpu/cuda, デフォルト: cpu)
- `PADDLEOCR_LANG`: OCR言語 (デフォルト: en)

### CORS設定
- `CORS_ORIGINS`: 許可されたフロントエンドドメイン

## 🐛 トラブルシューティング

### 1. ポート競合
ポート3000または8000が使用中の場合、`docker-compose.yml`のポートマッピングを変更：
```yaml
ports:
  - "3001:80"  # フロントエンドを3001に変更
  - "8001:8000"  # バックエンドを8001に変更
```

### 2. メモリ不足
PaddleOCRと画像処理には大量のメモリが必要です。Dockerに十分なメモリ割り当てを確保（推奨4GB+）。

### 3. サービス開始失敗
```bash
# 全サービスの詳細ログ確認
docker-compose logs -f iopaint-service
docker-compose logs -f backend
docker-compose logs -f frontend

# イメージ再ビルド
docker-compose build --no-cache

# サービスヘルス状態確認
docker-compose ps
```

### 4. IOPaintサービス問題
```bash
# IOPaintサービスログ確認
docker-compose logs -f iopaint-service

# IOPaintサービスのみ再起動
docker-compose restart iopaint-service

# IOPaintサービスヘルス確認
curl http://localhost:8081/api/v1/health
```

### 5. 権限問題
```bash
# ディレクトリ権限を正しく設定
sudo chown -R $USER:$USER uploads processed exports logs
```

### 6. ネットワーク接続問題
```bash
# ネットワーク接続確認
docker network ls
docker network inspect labeltool-fakedatagenerator_labeltool-network

# サービス接続性テスト
curl http://localhost:3000  # フロントエンド
curl http://localhost:8000/api/v1/health  # バックエンド
curl http://localhost:8081/api/v1/health  # IOPaintサービス
```

## 🔄 開発モード

開発中にコードを変更する必要がある場合：

### IOPaintサービス開発
```bash
# IOPaintサービスコンテナ停止
docker-compose stop iopaint-service

# 開発用にIOPaintサービスをローカル実行
cd iopaint-service
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8081
```

### バックエンド開発
```bash
# バックエンドコンテナ停止
docker-compose stop backend

# 開発用にバックエンドをローカル実行
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンド開発
```bash
# フロントエンドコンテナ停止
docker-compose stop frontend

# 開発用にフロントエンドをローカル実行
cd frontend
npm run dev
```

### 混合開発モード
```bash
# IOPaintとバックエンドをDockerで、フロントエンドをローカルで実行
docker-compose up iopaint-service backend
cd frontend && npm run dev

# IOPaintのみDockerで、バックエンドとフロントエンドをローカルで実行
docker-compose up iopaint-service
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

## 📊 監視とログ

### ヘルスチェック
全サービスでヘルスチェックが設定されています：
```bash
# サービスヘルス状態確認
docker-compose ps
```

### ログ確認
```bash
# 全ログをリアルタイム確認
docker-compose logs -f

# 最近のログ確認
docker-compose logs --tail=100

# エラーログのみ確認
docker-compose logs | grep ERROR
```

## 🚀 本番環境デプロイメント

### 1. 環境変数変更
```bash
# 本番環境設定
API_RELOAD=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
```

### 2. 外部データベース使用（必要に応じて）
`docker-compose.yml`を変更してデータベースサービスを追加。

### 3. リバースプロキシ設定
本番環境ではNginxまたは他のリバースプロキシの使用を推奨。

### 4. SSL証明書
安全なアクセスを確保するためHTTPS証明書を設定。

## 📝 更新とメンテナンス

### アプリケーション更新
```bash
# 最新コードをプル
git pull

# 再ビルドして開始
docker-compose up --build -d

# 古いイメージをクリーンアップ
docker image prune
```

### データバックアップ
```bash
# バックエンドアップロードと処理済みファイルのバックアップ
docker run --rm -v labeltool-fakedatagenerator_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_backend_processed:/data -v $(pwd):/backup alpine tar czf /backup/processed-backup.tar.gz -C /data .

# モデルキャッシュのバックアップ（高速起動のために重要）
docker run --rm -v labeltool-fakedatagenerator_huggingface_cache:/data -v $(pwd):/backup alpine tar czf /backup/iopaint-models-backup.tar.gz -C /data .
docker run --rm -v labeltool-fakedatagenerator_paddlex_cache:/data -v $(pwd):/backup alpine tar czf /backup/paddleocr-models-backup.tar.gz -C /data .
```

問題がある場合は、ログファイルを確認するか開発チームにお問い合わせください。