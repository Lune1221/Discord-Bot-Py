import discord
from discord import app_commands
from discord.ext import commands


class Antiraid(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="antiraid", description="荒らし対策機能のオンオフを切り替えます"
  )
  @app_commands.describe(status="オンにするかオフにするかを選択してください")
  @app_commands.choices(
      status=[
          app_commands.Choice(name="オン", value="on"),
          app_commands.Choice(name="オフ", value="off"),
      ]
  )
  @app_commands.checks.has_permissions(administrator=True)
  async def antiraid(self, interaction: discord.Interaction, status: str):
    await interaction.response.defer()
    enabled = status == "on"
    pool = self.bot.pool

    await pool.execute(
        """
            INSERT INTO antiraid_settings (guild_id, enabled) VALUES ($1, $2)
             ON CONFLICT (guild_id) DO UPDATE SET enabled = $2
        """,
        str(interaction.guild_id),
        enabled,
    )

    status_text = "有効" if enabled else "無効"
    await interaction.followup.send(
        f"🛡️ 荒らし対策機能を **{status_text}** に設定しました。"
    )


async def setup(bot):
  await bot.add_cog(Antiraid(bot))
