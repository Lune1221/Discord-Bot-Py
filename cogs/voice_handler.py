import discord
from discord.ext import commands

class VoiceHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, old_state: discord.VoiceState, new_state: discord.VoiceState):
        if old_state.channel_id == new_state.channel_id:
            return
        
        guild = new_state.guild or old_state.guild
        pool = self.bot.pool
        if not pool:
            return

        try:
            async with pool.acquire() as conn:
                setting_res = await conn.fetchrow('SELECT source_channel_id, keyword FROM intro_channel_settings WHERE guild_id = $1', str(guild.id))
                if not setting_res:
                    return
                
                source_channel_id = int(setting_res['source_channel_id'])
                keyword = setting_res['keyword'] or '名前：'
                source_channel = guild.get_channel(source_channel_id)
                if not source_channel:
                    return

                messages = [m async for m in source_channel.history(limit=100)]

                async def update_vc_intro(channel):
                    if not channel:
                        return
                    
                    active_members = [m for m in channel.members if not m.bot]
                    text = "参加メンバー\n\n"
                    
                    if not active_members:
                        text += "現在、誰も参加していません。[span_27](start_span)[span_27](end_span)"
                    else:
                        for m in active_members:
                            user_msg = next((msg for msg in messages if msg.author.id == m.id and keyword in msg.content), None)
                            if user_msg:
                                content = user_msg.content
                                if len(content) > 80:
                                    content = content[:80] + '...'
                            else:
                                content = "（自己紹介がありません）"
                            
                            text += f"• **{m.display_name}** :\n{content}\n\n"

                    try:
                        vc_msgs = [m async for m in channel.history(limit=30)]
                        existing = next((m for m in vc_msgs if m.author.id == self.bot.user.id and m.content.startswith("参加メンバー")), None)
                        
                        if existing:
                            await existing.edit(content=text)
                        else:
                            await channel.send(text)
                    except Exception as err:
                        print(f"VC更新エラー: {err}[span_28](start_span)[span_28](end_span)")

                if old_state.channel:
                    await update_vc_intro(old_state.channel)
                if newState.channel:
                    await update_vc_intro(newState.channel)

        except Exception as e:
            print(f"VCイベントエラー: {e}[span_29](start_span)[span_29](end_span)")

async def setup(bot):
    await bot.add_cog(VoiceHandler(bot))
