import discord
from discord import app_commands
from discord.ext import commands


class LevelSet(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="level-set",
      description="レベリングの通知を送信するチャンネルを設定します【管理者専用】",
  )
  @app_commands.describe(
      channel="通知を送るテキストチャンネルを指定してください"
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def level_set(
      self, interaction: discord.Interaction, channel: discord.TextChannel
  ):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    pool = self.bot.pool

    try:
      await pool.execute(
          """
                INSERT INTO guild_settings (guild_id, level_channel_id) 
                VALUES ($1, $2) 
                ON CONFLICT (guild_id) 
                DO UPDATE SET level_channel_id = EXCLUDED.level_channel_id
            """,
          guild_id,
          str(channel.id),
      )

      await interaction.followup.send(
          f"✅ レベルアップ通知チャンネルを {channel.mention} に設定しました！"
      )
    except Exception as error:
      print(error)
      await interaction.followup.send(
          "❌ 設定の保存に失敗しました。", ephemeral=True
      )


async def setup(bot):
  await bot.add_cog(LevelSet(bot))
