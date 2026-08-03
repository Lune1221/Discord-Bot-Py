import asyncio
import glob
import os
import pickle
import time
from discord.ext import commands
from PIL import Image
from supabase import create_client

ASCII_CHARS = ["⠀", "⠄", "⠆", "⠖", "⠶", "⡶", "⣩", "⣪", "⣫", "⣾", "⣿"]
ASCII_CHARS.reverse()
ASCII_CHARS = ASCII_CHARS[::-1]

WIDTH = 60
TIMEOUT = 0.13
CACHE_FILE = "bad_apple_cache.pkl"
BUCKET_NAME = "bad-apple-cache"  # Supabaseで作成したバケット名

# Supabaseクライアントの初期化
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def resize(image, new_width=WIDTH):
  old_width, old_height = image.size
  aspect_ratio = float(old_height) / float(old_width)
  new_height = int((aspect_ratio * new_width) / 2)
  return image.resize((new_width, new_height))


def grayscalify(image):
  return image.convert("L")


def modify(image, buckets=25):
  initial_pixels = list(image.getdata())
  new_pixels = [
      ASCII_CHARS[pixel_value // buckets] for pixel_value in initial_pixels
  ]
  return "".join(new_pixels)


def do(image, new_width=WIDTH):
  image = resize(image)
  image = grayscalify(image)
  pixels = modify(image)
  len_pixels = len(pixels)
  return "\n".join([
      pixels[index : index + int(new_width)]
      for index in range(0, len_pixels, int(new_width))
  ])


def runner(path):
  try:
    image = Image.open(path)
  except Exception:
    return None
  return do(image)


class BadApple(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.frames = []
    self.frame_files = sorted(
        glob.glob("frames/frame*.jpg"),
        key=lambda x: int(
            os.path.basename(x).replace("frame", "").replace(".jpg", "")
        ),
    )
    print(
        f"Bad Apple: {len(self.frame_files)}枚のフレームファイルを確認しました。"
    )

    # 1. まずローカルにキャッシュがあればそこから読み込む
    if os.path.exists(CACHE_FILE):
      try:
        with open(CACHE_FILE, "rb") as f:
          self.frames = pickle.load(f)
        print(
            f"Bad Apple: ローカルキャッシュから {len(self.frames)}"
            " フレームを読み込みました！"
        )
      except Exception as e:
        print(f"Bad Apple: ローカルキャッシュの読み込みに失敗しました: {e}")

    # 2. ローカルになくても Supabase が設定されていればストレージから取得を試みる
    if not self.frames and supabase:
      try:
        res = supabase.storage.from_(BUCKET_NAME).download(CACHE_FILE)
        with open(CACHE_FILE, "wb") as f:
          f.write(res)
        with open(CACHE_FILE, "rb") as f:
          self.frames = pickle.load(f)
        print(
            f"Bad Apple: Supabaseからキャッシュを復元しました！"
            f" ({len(self.frames)} フレーム)"
        )
      except Exception as e:
        print(f"Bad Apple: Supabaseからのキャッシュ取得はありませんでした: {e}")

  @commands.command(name="bad_apple", aliases=["badapple"])
  async def bad_apple(self, ctx):
    if not self.frame_files:
      await ctx.send(
          "フレームファイルが見つかりません（frames/ フォルダを確認してください）。"
      )
      return

    # キャッシュがない場合のみ変換して保存
    if not self.frames:
      status_msg = await ctx.send(
          "🎬 初回変換中（次回からは一瞬です）..."
      )

      def load_and_cache_frames():
        loaded = []
        for path in self.frame_files:
          res = runner(path)
          if res:
            loaded.append(res)

        # ローカルに保存
        try:
          with open(CACHE_FILE, "wb") as f:
            pickle.dump(loaded, f)
        except Exception as e:
          print(f"ローカルキャッシュの保存に失敗しました: {e}")

        # Supabase Storageにもアップロード（永続化）
        if supabase:
          try:
            with open(CACHE_FILE, "rb") as f:
              file_bytes = f.read()
            supabase.storage.from_(BUCKET_NAME).upload(
                path=CACHE_FILE,
                file=file_bytes,
                file_options={"upsert": "true"},  # 既に存在する場合は上書き
            )
            print("Bad Apple: Supabaseへキャッシュをアップロードしました。")
          except Exception as e:
            print(f"Supabaseへのアップロードに失敗しました: {e}")

        return loaded

      self.frames = await asyncio.to_thread(load_and_cache_frames)
      # 変換が終わったらメッセージを削除する
      await status_msg.delete()

    if not self.frames:
      await ctx.send("フレームの読み込みに失敗しました。")
      return

    play_msg = await ctx.send(self.frames[0])

    oldTimestamp = time.time()
    i = 0
    while i < len(self.frames) - 1:
      disp = False
      while not disp:
        newTimestamp = time.time()
        if (newTimestamp - oldTimestamp) >= TIMEOUT:
          frame_content = self.frames[int(i)]
          if frame_content:
            try:
              await play_msg.edit(content=frame_content)
            except Exception:
              break
          newTimestamp = time.time()
          i += (newTimestamp - oldTimestamp) / TIMEOUT
          oldTimestamp = newTimestamp
          disp = True


async def setup(bot):
  await bot.add_cog(BadApple(bot))
