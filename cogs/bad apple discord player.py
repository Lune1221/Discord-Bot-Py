import glob
import os
import time
from discord.ext import commands
from PIL import Image

ASCII_CHARS = ["⠀", "⠄", "⠆", "⠖", "⠶", "⡶", "⣩", "⣪", "⣫", "⣾", "⣿"]
ASCII_CHARS.reverse()
ASCII_CHARS = ASCII_CHARS[::-1]

WIDTH = 60
# 実際のフレーム数から自動計算するように変更、または適切な遅延に調整
TIMEOUT = 0.13  # テンポに応じて調整してください


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
    print("Bad Appleのフレームを読み込んでいます...")

    # framesフォルダ内の画像ファイルを番号順に自動取得
    frame_files = sorted(
        glob.glob("frames/frame*.jpg"),
        key=lambda x: int(x.split("frame")[1].split(".")[0]),
    )

    for path in frame_files:
      self.frames.append(runner(path))

    print(
        f"Bad Appleのフレーム読み込みが完了しました！合計 {len(self.frames)}"
        " フレーム"
    )

  @commands.command(name="bad_apple", aliases=["bad apple"])
  async def bad_apple(self, ctx):
    if not self.frames:
      await ctx.send("フレームが読み込まれていません。")
      return

    oldTimestamp = time.time()
    i = 0
    while i < len(self.frames) - 1:
      disp = False
      while not disp:
        newTimestamp = time.time()
        if (newTimestamp - oldTimestamp) >= TIMEOUT:
          frame_content = self.frames[int(i)]
          if frame_content:
            await ctx.send(frame_content)
          newTimestamp = time.time()
          i += (newTimestamp - oldTimestamp) / TIMEOUT
          oldTimestamp = newTimestamp
          disp = True


async def setup(bot):
  await bot.add_cog(BadApple(bot))
