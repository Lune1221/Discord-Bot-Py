## 📦 導入方法 (Installation)

利用環境や目的に合わせて、以下の3つの方法から選んで導入できます。

### 1. Botをそのまま自分のサーバーに入れる場合（一番楽）
すでにホスティングされている（またはご自身で動かす）Botを、そのままDiscordサーバーに招待して使う一般的な方法です。
1. [招待リンク](https://discord.com/oauth2/authorize?client_id=1528013651384991754&permissions=2147551232&integration_type=0&scope=applications.commands+bot) からボットをサーバーに追加します。
2. 必要なスラッシュコマンド（`/count`, `/omikuji`, `/aa` など）をそのまま使用できます。

### 2. Botのコードを自分の既存ボットに部分移植する場合
すでに動いている自作のDiscordボットに、特定の機能（音楽再生、画像アスキーアート変換、荒らし対策など）だけをCog単位で組み込みたい場合の方法です。
1. `cogs/` フォルダの中身（例: `music.py`, `image_to_aa.py` など）から、使いたいファイルをご自身のボットのプロジェクトにコピーします。
2. メインのボットファイル（`main.py` 等）で `await bot.load_extension("cogs.ファイル名")` を実行して読み込ませます。
3. 必要なライブラリ（`yt-dlp`, `Pillow` など）をインストールします。

### 3. Botの全コードをそのまま自分の環境に完全移植する場合
Botのすべての機能を含めたリポジトリをご自身の環境（VPSなど）で丸ごと動かしたい場合の方法です。
1. このリポジトリをクローンまたはダウンロードします。
2. 必要なPythonライブラリをインストールします。
   ```bash
   pip install -r requirements.txt
3. 環境変数（.env）にボットのトークンやデータベース接続情報を設定します。
4. メインファイルを起動します。
   ```bash
   python main.py

## 🛠️ 使用技術・ライブラリ

このボットを完全移植、または一部のCogを導入する際は、以下のライブラリが必要です。
環境に合わせて `pip install` で導入してください。

### 📦 Pythonパッケージ (`requirements.txt`)
* **[discord.py](https://github.com/Rapptz/discord.py)** : Discordボットのメインフレームワーク
* **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** : YouTubeからの音声を取得（Music機能）
* **[PyNaCl](https://pypi.org/project/PyNaCl/)** : ボイスチャンネルを利用するためのライブラリ
* **[Pillow (PIL)](https://pillow.readthedocs.io/)** : 画像のリサイズやアスキーアート変換処理（`/aa` 機能）
* **[asyncpg](https://github.com/MagicStack/asyncpg)** : PostgreSQLデータベースとの非同期接続（レベル・荒らし対策などのデータ管理）
* **[Flask](https://flask.palletsprojects.com/)** : ホスティング環境でのスリープ防止用Webサーバー

### ⚙️ 外部ツール（システム要件）
音楽機能（`cogs/music.py`）を使用する場合、Pythonライブラリに加えてシステム本体に以下のツールがインストールされている必要があります。
* **FFmpeg** : 音声データのストリーミング変換処理に使用します。

## 💻 必要な環境 (System Requirements)

このボットを動かす（完全移植する）ために、以下の環境および外部ツールがあらかじめ必要です。

### 1. Python バージョン
* **Python 3.10 以上** （※推奨: Python 3.14）
  * 非同期処理（`async/await`）やDiscord.pyの仕様に合わせた環境が必要です。

### 2. 外部システムツール
ボットの特定の機能を正常に動作させるために、サーバー（OS）側に以下のツールがインストールされている必要があります。

* **FFmpeg** （音楽・音声再生機能に必須）
  * YouTubeの音声ストリーミングや音声ファイルのデコード処理に必要です。
  * *確認方法*: ターミナルで `ffmpeg -version` を実行してバージョンが表示されることを確認してください。
* **PostgreSQL** （データベース機能に必須）
  * レベルシステム、荒らし対策設定、予約メッセージなどのデータ保存に使用します。
  * *補足*: Renderなどのクラウドサービスで動かす場合は、マネージドデータベース（PostgreSQL）を繋ぐことで動作します。

### 3. アカウント・事前準備
* **Discord Bot Token**
  * [Discord Developer Portal](https://discord.com/developers/applications) でボットを作成し、**Message Content Intent** などの必要なBot Intentsを有効にしてトークンを発行してください。

 ## ⚠️ 免責事項 (Disclaimer)

* **利用規約の遵守について**
  * 本ボットの利用およびコードの流用によって発生したいかなるトラブル、損害、Discord利用規約違反によるアカウント・サーバーのBAN（利用停止）等について、作成者は一切の責任を負いません。自己責任においてご利用・導入してください。
* **音楽再生機能に関する注意**
  * 本ボットの音楽再生機能（YouTube等のストリーミング）は、各プラットフォームの利用規約やAPIの仕様変更等により、予告なく動作しなくなる場合があります。また、著作権に関する法律および利用規約を遵守してご利用ください。
* **一括メンション機能について**
  * ロール等を対象とした一括メンション機能は、使い方を誤るとスパム行為とみなされ、Discordの規約に抵触する恐れがあります。サーバーのルールやモデレーション方針に従い、節度を持ってご使用ください。
