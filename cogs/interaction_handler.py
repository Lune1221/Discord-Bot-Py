import discord
from discord.ext import commands

class InteractionHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        # ボタン操作の処理[span_24](start_span)[span_24](end_span)
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            parts = custom_id.split("_")
            if len(parts) >= 3:
                action, page_str, executor_id = parts[0], parts[1], parts[2]
                if str(interaction.user.id) != executor_id:
                    await interaction.response.send_message("❌ 本人しか操作できません。[span_25](start_span)[span_25](end_span)", ephemeral=True)
                    return
                
                ranking_cog = self.bot.get_cog("Ranking") # ランキングCog側で定義する関数を呼び出し
                if ranking_cog and hasattr(ranking_cog, "execute_button"):
                    new_page = int(page_str) + (-1 if action == 'prev' else 1)
                    await ranking_cog.execute_button(interaction, self.bot.pool, new_page, executor_id)

async def setup(bot):
    await bot.add_cog(InteractionHandler(bot))
