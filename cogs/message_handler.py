import discord
from discord.ext import commands
import time

# ユーザーごとの履歴管理用マップ
user_message_history = {}
user_last_warn_timestamp = {}

def get_level_info(count):
    level = 0
    while True:
        req = int(10 + (level * level * 2))
        if count >= req:
            count -= req
            level += 1
        else:
            return {"level": level, "current": count, "required": req}

class MessageHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        pool = self.bot.pool

        # 🛡️ 荒らし対策チェック
        try:
            async with pool.acquire() as conn:
                raid_check = await conn.fetch('SELECT enabled FROM antiraid_settings WHERE guild_id = $1', str(message.guild.id))
                if raid_check and raid_check[0]['enabled']:
                    
                    # 1. 大量メンション検知（5個以上）[span_11](start_span)[span_11](end_span)
                    if len(message.mentions) >= 5 or len(message.role_mentions) >= 5:
                        try:
                            await message.delete()
                        except Exception as err:
                            print(f"メッセージ削除エラー(メンション): {err}[span_12](start_span)[span_12](end_span)")
                        
                        user_id = message.author.id
                        now = time.time() * 1000
                        last_warn = user_last_warn_timestamp.get(user_id, 0)

                        if now - last_warn > 3000:
                            user_last_warn_timestamp[user_id] = now
                            warn = await message.channel.send(f"🛡️ {message.author.mention} さんのメッセージは荒らし対策（大量メンション検知）により削除されました。[span_13](start_span)[span_13](end_span)")
                            self.bot.loop.create_task(self.delete_later(warn, 5))
                        return

                    # 2. 短時間の連投検知（3秒以内に5回以上）[span_14](start_span)[span_14](end_span)
                    user_id = message.author.id
                    now = time.time() * 1000
                    if user_id not in user_message_history:
                        user_message_history[user_id] = []
                    
                    history = user_message_history[user_id]
                    history.append({"timestamp": now, "message_id": message.id})

                    # 3秒以内の履歴だけ残す[span_15](start_span)[span_15](end_span)
                    history = [item for item in history if now - item['timestamp'] <= 3000]
                    user_message_history[user_id] = history

                    if len(history) >= 5:
                        for item in history:
                            try:
                                msg_to_delete = await message.channel.fetch_message(int(item['message_id']))
                                if msg_to_delete:
                                    await msg_to_delete.delete()
                            except Exception as err:
                                print(f"連投メッセージ一括削除エラー: {err}[span_16](start_span)[span_16](end_span)")

                        last_warn = user_last_warn_timestamp.get(user_id, 0)
                        if now - last_warn > 3000:
                            user_last_warn_timestamp[user_id] = now
                            warn = await message.channel.send(f"🛡️ {message.author.mention} さんのメッセージは荒らし対策（短時間の連投検知）により削除されました。[span_17](start_span)[span_17](end_span)")
                            self.bot.loop.create_task(self.delete_later(warn, 5))

                        user_message_history[user_id] = []
                        return
        except Exception as e:
            print(f"荒らし対策エラー: {e}[span_18](start_span)[span_18](end_span)")

        # レベルアップ処理[span_19](start_span)[span_19](end_span)
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO message_counts (user_id, guild_id, count) 
                    VALUES ($1, $2, 1) 
                    ON CONFLICT(user_id, guild_id) 
                    DO UPDATE SET count = message_counts.count + 1 
                    RETURNING count;
                    """,
                    str(message.author.id), str(message.guild.id)
                )
                new_count = row['count']
                old_info = get_level_info(new_count - 1)
                new_info = get_level_info(new_count)

                if new_info['level'] > old_info['level']:
                    set_res = await conn.fetchrow('SELECT level_channel_id FROM guild_settings WHERE guild_id = $1', str(message.guild.id))
                    target_channel = message.channel
                    if set_res and set_res['level_channel_id']:
                        ch = message.guild.get_channel(int(set_res['level_channel_id']))
                        if ch:
                            target_channel = ch
                    
                    await target_channel.send(f"🎉 {message.author.mention} おめでとうございます！レベル **{new_info['level']}** にアップしました！[span_20](start_span)[span_20](end_span)")
        except Exception as e:
            print(f"レベル処理エラー: {e}[span_21](start_span)[span_21](end_span)")

        # スティッキーメッセージ処理[span_22](start_span)[span_22](end_span)
        try:
            async with pool.acquire() as conn:
                sticky_res = await conn.fetchrow('SELECT * FROM sticky_messages WHERE channel_id = $1', str(message.channel.id))
                if sticky_res:
                    if sticky_res['message_id']:
                        try:
                            old_msg = await message.channel.fetch_message(int(sticky_res['message_id']))
                            if old_msg:
                                await old_msg.delete()
                        except:
                            pass
                    
                    embed = discord.Embed(title=sticky_res['title'], description=sticky_res['description'], color=0x3498db)
                    embed.timestamp = discord.utils.utcnow()
                    new_msg = await message.channel.send(embed=embed)
                    await conn.execute('UPDATE sticky_messages SET message_id = $1 WHERE channel_id = $2', str(new_msg.id), str(message.channel.id))
        except Exception as e:
            pass

    async def delete_later(self, message, delay):
        import asyncio
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except:
            pass

async def setup(bot):
    await bot.add_cog(MessageHandler(bot))
