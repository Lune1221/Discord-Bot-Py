import discord
from discord import app_commands
from discord.ext import commands

class VCIntroCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /vcintro グループコマンドの定義（サーバー管理権限が必要）[span_2](start_span)[span_2](end_span)
    vcintro_group = app_commands.Group(
        name="vcintro",
        description="VC参加時の自己紹介自動表示の設定を管理します",
        default_permissions=discord.Permissions(manage_guild=True)
    )

    @vcintro_group.command(name="set", description="自己紹介チャンネルとの連携設定を追加します")
    @app_commands.describe(
        source="自己紹介が投稿されているテキストチャンネル（例: #自己紹介）",
        keyword="検索するキーワード（例: 名前：、ハンネ：等。省略時は「名前：」）"
    )
    async def vcintro_set(
        self, 
        interaction: discord.Interaction, 
        source: discord.TextChannel, 
        keyword: str = "名前："
    ):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        pool = self.bot.pool

        async with pool.acquire() as conn:
            # データベースに設定を保存[span_3](start_span)[span_3](end_span)
            await conn.execute(
                """INSERT INTO intro_channel_settings (guild_id, source_channel_id, keyword) 
                   VALUES ($1, $2, $3)""",
                guild_id, str(source.id), keyword
            )

        await interaction.editReply(
            content=f"✨ VC自己紹介の設定を追加しました！\n• 読み取り元チャンネル: {source.mention}\n• 検索ワード: `{keyword}`\n*(※ 参加したVCのインサイドチャットに自動で送信されます)*[span_4](start_span)"[span_4](end_span)
        )

    @vcintro_group.command(name="list", description="現在登録されている自己紹介の設定一覧を表示します")
    async def vcintro_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        pool = self.bot.pool

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT id, source_channel_id, keyword FROM intro_channel_settings WHERE guild_id = $1 ORDER BY id ASC',
                guild_id
            )[span_5](start_span)[span_5](end_span)

        if not rows:
            return await interaction.editReply(content="📭 現在登録されているVC自己紹介の設定はありません。[span_6](start_span)[span_6](end_span)")

        list_text = "📋 **現在のVC自己紹介設定一覧**\n"
        for row in rows:
            list_text += f"• **ID: {row['id']}** | 読み取り: <#{row['source_channel_id']}> (ワード: `{row['keyword']}`)\n[span_7](start_span)"[span_7](end_span)

        await interaction.editReply(content=list_text)

    @vcintro_group.command(name="delete", description="IDを指定して設定を削除します")
    @app_commands.describe(id="削除する設定のID (listコマンドで確認できます)")
    async def vcintro_delete(self, interaction: discord.Interaction, id: int):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        pool = self.bot.pool

        async with pool.acquire() as conn:
            deleted = await conn.fetchrow(
                'DELETE FROM intro_channel_settings WHERE id = $1 AND guild_id = $2 RETURNING id',
                id, guild_id
            )[span_8](start_span)[span_8](end_span)

        if not deleted:
            return await interaction.editReply(
                content=f"❌ ID `{id}` の設定が見つからないか、このサーバーの設定ではありません。[span_9](start_span)[span_9](end_span)"
            )

        await interaction.editReply(content=f"🗑️ ID `{id}` の設定を削除しました。[span_10](start_span)[span_10](end_span)")

async def setup(bot):
    await bot.add_cog(VCIntroCog(bot))
