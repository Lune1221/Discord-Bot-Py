import time
from discord.ext import commands

# 3分39秒 = 219.0秒（本家の正確な長さ）
TOTAL_DURATION = 219.0


class BadApple(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.frames = []

    try:
      from frames_data import FRAMES

      self.frames = FRAMES
      print(f"Bad Apple: {len(self.frames)} フレームを読み込みました！")
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
    total_frames = len(self.frames)
    start_time = time.time()

    last_index = 0
    while True:
      elapsed = time.time() - start_time
      if elapsed >= TOTAL_DURATION:
        break

      # 【超重要】いま何秒経過したかから「何番目のフレームを表示すべきか」を自動計算する
      # これにより、フレーム数が何枚であっても必ず「219秒」のなかに綺麗に収まります
      current_index = int((elapsed / TOTAL_DURATION) * total_frames)
      if current_index >= total_frames:
        current_index = total_frames - 1

      if current_index != last_index:
        last_index = current_index
        try:
          await play_msg.edit(content=self.frames[current_index])
        except Exception:
          break

      # Discordの過負荷を防ぐための短い待機
      time.sleep(0.03)


async def setup(bot):
  await bot.add_cog(BadApple(bot))
