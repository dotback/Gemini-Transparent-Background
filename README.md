# Gemini Transparent Background (背景透過ツール)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Gemini Nano Banana Proで作った「グリーンバック画像」から、クロマキー処理して透過PNGに変換するPythonツールです。

## インストール

1. **リポジトリをクローン**
   ```bash
   git clone https://github.com/dotback/Gemini-Transparent-Background.git
   cd Gemini-Transparent-Background
   ```

2. **仮想環境の作成と有効化**
   ```bash
   # 仮想環境の作成 
   python3 -m venv .venv

   # 仮想環境の有効化 
   source .venv/bin/activate

   # 仮想環境の有効化
   # .venv\Scripts\activate
   ```

3. **パッケージのインストール**
   ```bash
   pip install -e .
   ```

## 使い方

## 使い方

### Webアプリ (Gradio)
Webアプリを使用する場合は、追加の依存関係をインストールしてください。

```bash
pip install -e ".[web]"
```

**Gemini APIの設定 (画像生成機能を使う場合)**
`.env.example` をコピーして `.env` ファイルを作成し、APIキーを設定してください。

```bash
cp .env.example .env
# .envファイルを開き、GEMINI_API_KEYにキーを入力
```

```bash
python -m gemini_transparent_background.web
```

http://127.0.0.1:7860 にアクセスしてください。

## 機能
- **高度な背景除去 (Advanced Mode)**:
    - **エッジ検出**: 境界線をきれいに保ちます。
    - **フェザリング**: ギザギザしたエッジを滑らかにします。
    - **デスピル (Despill)**: 被写体の縁に残った緑色の反射（緑かぶり）を除去します。
    - **収縮/膨張**: マスク領域を微調整してノイズを除去したり、欠けを防いだりします。

## ライセンス
[MIT](LICENSE)
