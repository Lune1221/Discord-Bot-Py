from datetime import datetime
import math
import discord
from discord import app_commands
from discord.ext import commands


def get_required_messages(level):
  return math.floor(10 + (level * level * 2))


def get_level_info(total_count):
  level = 0
  count = total_count
  while True:
    required = get_required_messages(level)
    if count >= required:
      count -= required
      level += 1
    else:
      return {"level": level, "current": count, "required": required}


class Level(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="level", description="指定したユーザーのレベルとメッセージ数を確認します"
  )
  @app_commands.describe(user="ユーザー（空欄なら自分）")
  async def level(
      self, interaction: discord.Interaction, user: discord.User = None
  ):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id) if interaction.guild else None
    target_user = user or interaction.user
    user_id = str(target_user.id)

    pool = self.bot.pool
    res = await pool.fetchrow(
        "SELECT count FROM message_counts WHERE user_id = $1 AND guild_id = $2",
        user_id,
        guild_id,
    )
    total_count = res["count"] if res else 0

    info = get_level_info(total_count)
    remaining = info["required"] - info["current"]

    embed = discord.Embed(
        color=discord.Color.from_str("#3498db"),
        title=f"{target_user.name} さんのレベル情報",
    )
    embed.add_field(name=" 現在のレベル", value=f"{info['level']}", inline=True)
    embed.add_field(
        name=" 次のレベルまで", value=f"あと {remaining} メッセージ", inline=False
    )
    embed.timestamp = datetime.now()

    await interaction.followup.send(embed=embed)


async def setup(bot):
  await bot.add_cog(Level(bot))
