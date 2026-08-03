from datetime import datetime
import random
import discord
from discord import app_commands
from discord.ext import commands
from zoneinfo import ZoneInfo

omikuji_results = [
    "大吉 ",
    "中吉 ",
    "中吉 ",
    "小吉 ",
    "小吉 ",
    "吉 ",
    "吉 ",
    "吉 ",
    "凶 ",
    "凶 ",
]


class Omikuji(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="omikuji", description="今日のおみくじを引きます（1日1回限定）"
  )
  async def omikuji(self, interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id) if interaction.guild else None
    user_id = str(interaction.user.id)

    today_str = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d")
    pool = self.bot.pool

    cooldown_res = await pool.fetchrow(
        "SELECT last_date FROM omikuji_cooldowns WHERE user_id = $1 AND guild_id"
        " = $2",
        user_id,
        guild_id,
    )

    if cooldown_res and cooldown_res["last_date"] == today_str:
      embed_error = discord.Embed(
          title="❌ おみくじは1日1回まで",
          description="今日のおみくじは既に引いています！また明日引いてね！",
          color=discord.Color.from_str("#ff4757"),
      )
      embed_error.timestamp = datetime.now()
      await interaction.followup.send(embed=embed_error)
      return

    fortune = random.choice(omikuji_results)

    await pool.execute(
        """
            INSERT INTO omikuji_cooldowns (user_id, guild_id, last_date) 
            VALUES ($1, $2, $3) 
            ON CONFLICT(user_id, guild_id) DO UPDATE SET last_date = $3
        """,
        user_id,
        guild_id,
        today_str,
    )

    embed = discord.Embed(
        title="おみくじ結果",
        description=f"<@{interaction.user.id}> さんの今日の運勢は...",
        color=discord.Color.from_str("#ff4757"),
    )
    embed.add_field(name="【運勢】", value=f"**{fortune}**")
    embed.timestamp = datetime.now()

    await interaction.followup.send(embed=embed)


async def setup(bot):
  await bot.add_cog(Omikuji(bot))
