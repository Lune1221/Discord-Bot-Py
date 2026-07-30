import discord
from discord import app_commands
from discord.ext import commands

class StickyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /sticky グループコマンドの定義（メッセージ管理権限が必要）
    sticky_group = app_commands.Group(
        name="sticky",
        description="指定したチャンネルにスティッキーメッセージ（固定埋め込み）を設定・解除します",
        default_permissions=discord.Permissions(manage_messages=True)
    )

    @sticky_group.command(name="set", description="スティッキーメッセージを設定します")
    @app_commands.describe(
        title="埋め込みのタイトル",
        description="埋め込みの説明文",
        channel="送信先のチャンネル（省略した場合は現在のチャンネル）"
    )
    async def sticky_set(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        description: str, 
        channel: discord.TextChannel = None
    ):
        await interaction.response.defer(ephemeral=True)
        target_channel = channel or interaction.channel
        channel_id = str(target_channel.id)
        pool = self.bot.pool

        async with pool.acquire() as conn:
            # データベースにテーブルがなければ自動作成[span_1](start_span)[span_1](end_span)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sticky_messages (
                    channel_id VARCHAR(32) PRIMARY KEY,
                    message_id VARCHAR(32),
                    title TEXT,
                    description TEXT
                )
            """)

            # 既存の設定を確認して、古いメッセージがあれば削除を試みる[span_2](start_span)[span_2](end_span)
            res = await conn.fetchrow('SELECT message_id FROM sticky_messages WHERE channel_id = $1', channel_id)
            if res and res['message_id']:
                try:
                    old_msg = await target_channel.fetch_message(int(res['message_id']))
                    if old_msg:
                        await old_msg.delete()
                except Exception:
                    pass

            # 新しいスティッキーメッセージをターゲットチャンネルに送信[span_3](start_span)[span_3](end_span)
            embed = discord.Embed(title=title, description=description, color=0x3498db)
            embed.timestamp = discord.utils.utcnow()
            sent_message = await target_channel.send(embed=embed)

            # データベースに保存・更新[span_4](start_span)[span_4](end_span)
            await conn.execute("""
                INSERT INTO sticky_messages (channel_id, message_id, title, description)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (channel_id) 
                DO UPDATE SET message_id = $2, title = $3, description = $4
            """, channel_id, str(sent_message.id), title, description)

        await interaction.editReply(content=f"✨ {target_channel.mention} にスティッキーメッセージを設定しました！[span_5](start_span)[span_5](end_span)")

    @sticky_group.command(name="remove", description="指定したチャンネルのスティッキーメッセージを解除します")
    @app_commands.describe(channel="解除するチャンネル（省略した場合は現在のチャンネル）")
    async def sticky_remove(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
        target_channel = channel or interaction.channel
        channel_id = str(target_channel.id)
        pool = self.bot.pool

        async with pool.acquire() as conn:
            res = await conn.fetchrow('SELECT message_id FROM sticky_messages WHERE channel_id = $1', channel_id)

            if res:
                if res['message_id']:
                    try:
                        old_msg = await target_channel.fetch_message(int(res['message_id']))
                        if old_msg:
                            await old_msg.delete()
                    except Exception:
                        pass
                await conn.execute('DELETE FROM sticky_messages WHERE channel_id = $1', channel_id)
                await interaction.editReply(content=f"🗑️ {target_channel.mention} のスティッキーメッセージを解除しました。[span_6](start_span)[span_6](end_span)")
            else:
                await interaction.editReply(content=f"⚠️ {target_channel.mention} にはスティッキーメッセージが設定されていません。[span_7](start_span)[span_7](end_span)")

async def setup(bot):
    await bot.add_cog(StickyCog(bot))
