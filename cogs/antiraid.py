import discord
from discord import app_commands
from discord.ext import commands

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="antiraid", description="荒らし対策機能の有効/無効を切り替えます")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(status=[
        app_commands.Choice(name="有効", value="on"),
        app_commands.Choice(name="無効", value="off")
    ])
    async def antiraid(self, interaction: discord.Interaction, status: str):
        if not interaction.guild:
            return

        guild_id = str(interaction.guild.id)
        is_enabled = (status == "on")

        # データベースに設定を保存 (存在する場合は更新)
        async with self.bot.pool.acquire() as connection:
            await connection.execute("""
                INSERT INTO antiraid_settings (guild_id, enabled) 
                VALUES ($1, $2)
                ON CONFLICT (guild_id) 
                DO UPDATE SET enabled = $2;
            """, guild_id, is_enabled)

        status_text = "有効" if is_enabled else "無効"
        await interaction.response.send_message(
            f"🛡️ 荒らし対策機能を **{status_text}** に設定しました。",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
