from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


class Count(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="count", description="指定したユーザーの発言回数を表示します"
  )
  @app_commands.describe(user="ユーザー（空欄なら自分）")
  async def count(
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
    count_val = res["count"] if res else 0

    embed = discord.Embed(
        title="📊 発言回数の確認",
        description=f"<@{user_id}> さんの発言回数は **{count_val}回** です！",
        color=discord.Color.from_str("#3498db"),
    )
    embed.timestamp = datetime.now()

    await interaction.followup.send(embed=embed)


async def setup(bot):
  await bot.add_cog(Count(bot))
