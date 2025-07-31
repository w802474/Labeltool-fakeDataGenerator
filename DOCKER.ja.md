# Docker デプロイメントガイド

*[English](DOCKER.md) | [中文文档](DOCKER.zh-CN.md) | [日本語ドキュメント](DOCKER.ja.md)*

このドキュメントは、DockerでLabelToolプロジェクトを実行する方法を説明します。

## 🚀 クイックスタート

### 1. プロジェクトをクローンしてディレクトリに移動
```bash
git clone <your-repo-url>
cd labeltool
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
# 全サービスをビルドして開始（バックエンドが先に起動、フロントエンドはバックエンドのヘルスチェック通過後に開始）
docker-compose up --build

# またはバックグラウンドで実行
docker-compose up --build -d
```

### 4. アプリケーションにアクセス
- フロントエンド: http://localhost:3000
- バックエンドAPIドキュメント: http://localhost:8000/docs
- バックエンドAPIステータス: http://localhost:8000/

## 📋 サービス説明

### バックエンドサービス (labeltool-backend)
- **ポート**: 8000
- **技術スタック**: Python 3.11.13 + FastAPI + PaddleOCR
- **機能**: OCRテキスト検出および画像処理APIを提供
- **ヘルスチェック**: サービス状態を自動チェック、起動後約40秒で初期化完了

### フロントエンドサービス (labeltool-frontend)
- **ポート**: 3000
- **技術スタック**: React 18 + TypeScript + Nginx
- **機能**: ユーザーインターフェースと画像アノテーション機能を提供
- **依存関係**: バックエンドサービスのヘルスチェック通過後にのみ開始

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
docker-compose logs backend
docker-compose logs frontend
```

### 個別サービスビルド
```bash
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
docker-compose restart backend
docker-compose restart frontend
```

## 📁 データ永続化

プロジェクトはDockerボリュームを使用して重要なデータを永続化します：

- `backend_uploads`: アップロードされた画像ファイル
- `backend_processed`: 処理済み画像ファイル
- `backend_exports`: エクスポートファイル
- `backend_logs`: アプリケーションログ

### ボリューム管理コマンド
```bash
# 全ボリューム確認
docker volume ls

# 特定ボリュームの詳細確認
docker volume inspect labeltool_backend_uploads

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
# 詳細ログ確認
docker-compose logs -f backend
docker-compose logs -f frontend

# イメージ再ビルド
docker-compose build --no-cache
```

### 4. 権限問題
```bash
# ディレクトリ権限を正しく設定
sudo chown -R $USER:$USER uploads processed exports logs
```

### 5. ネットワーク接続問題
```bash
# ネットワーク接続確認
docker network ls
docker network inspect labeltool_labeltool-network
```

## 🔄 開発モード

開発中にコードを変更する必要がある場合：

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
# ボリュームデータのバックアップ
docker run --rm -v labeltool_backend_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

問題がある場合は、ログファイルを確認するか開発チームにお問い合わせください。