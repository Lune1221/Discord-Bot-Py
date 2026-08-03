from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands


class Say(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="say",
      description="指定したチャンネルにメッセージを送信させます【管理者専用】",
  )
  @app_commands.describe(
      channel="メッセージを送信するテキストチャンネルを指定してください",
      text="Embedに表示させたい本文を入力してください",
      color="Embedの色（例: #3498db などの16進数カラーコード。省略時は青）",
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def say(
      self,
      interaction: discord.Interaction,
      channel: discord.TextChannel,
      text: str,
      color: str = "#3498db",
  ):
    await interaction.response.defer()
    try:
      color_val = discord.Color.from_str(color)
    except ValueError:
      color_val = discord.Color.from_str("#3498db")

    try:
      embed = discord.Embed(description=text, color=color_val)
      embed.timestamp = datetime.now()

      await channel.send(embed=embed)
      await interaction.followup.send(
          f"✅ {channel.mention} にメッセージを送信しました！"
      )
    except Exception as error:
      print(error)
      await interaction.followup.send(
          "❌ メッセージの送信に失敗しました（カラーコードの形式が間違っているか、権限が不足しています）。",
          ephemeral=True,
      )


async def setup(bot):
  await bot.add_cog(Say(bot))
