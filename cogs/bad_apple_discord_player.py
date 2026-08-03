import time
from discord.ext import commands

WIDTH = 60
TIMEOUT = 0.13


class BadApple(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.frames = []

    # Pythonファイルから一瞬で読み込む
    try:
      from frames_data import FRAMES

      self.frames = FRAMES
      print(f"Bad Apple: プリセットから {len(self.frames)} フレームを読み込みました！")
    except Exception as e:
      print(f"Bad Apple: フレームデータの読み込みに失敗しました: {e}")

  @commands.command(name="bad_apple", aliases=["badapple"])
  async def bad_apple(self, ctx):
    if not self.frames:
      await ctx.send(
          "フレームデータ（frames_data.py）が読み込まれていません。"
      )
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
