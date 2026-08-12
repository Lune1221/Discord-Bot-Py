import asyncio
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands, tasks

# ユーザーごとのメッセージ履歴・前回の警告送信時刻を保持するメモリ
user_message_history = {}
user_last_warn_timestamp = {}


def get_level_info(count):
  level = 0
  while True:
    req = 10 + (level * level * 2)
    if count >= req:
      count -= req
      level += 1
    else:
      return {"level": level, "current": count, "required": req}


class Events(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.scheduled_message_loop.start()

  def cog_unload(self):
    self.scheduled_message_loop.cancel()

  # 1. 予約メッセージ送信ループ
  @tasks.loop(minutes=1)
  async def scheduled_message_loop(self):
    pool = getattr(self.bot, "pool", None)
    if not pool:
      return
    try:
      now = datetime.now()
      res = await pool.fetch(
          "SELECT * FROM scheduled_messages WHERE send_at <= $1", now
      )
      for row in res:
        channel = self.bot.get_channel(int(row["channel_id"]))
        if not channel:
          try:
            channel = await self.bot.fetch_channel(int(row["channel_id"]))
          except Exception:
            channel = None
        if channel:
          await channel.send(row["message_content"])
        await pool.execute(
            "DELETE FROM scheduled_messages WHERE id = $1", row["id"]
        )
    except Exception as e:
      print("予約メッセージエラー:", e)

  @scheduled_message_loop.before_loop
  async def before_scheduled_message_loop(self):
    await self.bot.wait_until_ready()

  # 2. 起動時・コマンド自動同期
  @commands.Cog.listener()
  async def on_ready(self):
    print(f"{self.bot.user} でログインしました！")
    guild_count = len(self.bot.guilds)
    await self.bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{guild_count} 個のサーバーで稼働",
        )
    )

  # 3. メッセージ作成・荒らし対策・レベルアップ・スティッキー
  @commands.Cog.listener()
  async def on_message(self, message: discord.Message):
    if message.author.bot or not message.guild:
      return
    pool = getattr(self.bot, "pool", None)
    if not pool:
      return

    # 🛡️ 荒らし対策チェック
    try:
      raid_check = await pool.fetchrow(
          "SELECT enabled FROM antiraid_settings WHERE guild_id = $1",
          str(message.guild.id),
      )
      if raid_check and raid_check["enabled"]:
        # 1. 大量メンション検知（5個以上）
        if len(message.mentions) >= 5 or len(message.role_mentions) >= 5:
          try:
            await message.delete()
          except Exception as err:
            print("メッセージ削除エラー(メンション):", err)

          user_id = str(message.author.id)
          now_ts = datetime.now().timestamp() * 1000
          last_warn = user_last_warn_timestamp.get(user_id, 0)

          if now_ts - last_warn > 3000:
            user_last_warn_timestamp[user_id] = now_ts
            warn = await message.channel.send(
                f"🛡️ {message.author.mention}"
                " さんのメッセージは荒らし対策（大量メンション検知）により削除されました。"
            )
            asyncio.create_task(self._delete_later(warn, 5))
          return

        # 2. 短時間の連投検知（3秒以内に5回以上）
        user_id = str(message.author.id)
        now_ts = datetime.now().timestamp() * 1000
        if user_id not in user_message_history:
          user_message_history[user_id] = []
        history = user_message_history[user_id]
        history.append({"timestamp": now_ts, "messageId": str(message.id)})

        history = [item for item in history if now_ts - item["timestamp"] <= 3000]
        user_message_history[user_id] = history

        if len(history) >= 5:
          for item in history:
            try:
              msg_to_delete = await message.channel.fetch_message(
                  int(item["messageId"])
              )
              if msg_to_delete:
                await msg_to_delete.delete()
            except Exception as err:
              print("連投メッセージ一括削除エラー:", err)

          last_warn = user_last_warn_timestamp.get(user_id, 0)
          if now_ts - last_warn > 3000:
            user_last_warn_timestamp[user_id] = now_ts
            warn = await message.channel.send(
                f"🛡️ {message.author.mention}"
                " さんのメッセージは荒らし対策（短時間の連投検知）により削除されました。"
            )
            asyncio.create_task(self._delete_later(warn, 5))

          user_message_history[user_id] = []
          return
    except Exception as e:
      print("荒らし対策エラー:", e)

    # レベルアップ処理
    try:
      res = await pool.fetchrow(
          """
                INSERT INTO message_counts (user_id, guild_id, count) 
                VALUES ($1, $2, 1) 
                ON CONFLICT(user_id, guild_id) 
                DO UPDATE SET count = message_counts.count + 1 
                RETURNING count;
            """,
          str(message.author.id),
          str(message.guild.id),
      )
      new_count = res["count"]
      old_info = get_level_info(new_count - 1)
      new_info = get_level_info(new_count)

      if new_info["level"] > old_info["level"]:
        set_res = await pool.fetchrow(
            "SELECT level_channel_id FROM guild_settings WHERE guild_id = $1",
            str(message.guild.id),
        )
        target_channel = message.channel
        if set_res and set_res["level_channel_id"]:
          ch = message.guild.get_channel(int(set_res["level_channel_id"]))
          if ch:
            target_channel = ch
        await target_channel.send(
            f"🎉 {message.author.mention} おめでとうございます！レベル"
            f" **{new_info['level']}** にアップしました！"
        )
    except Exception as e:
      print("レベル処理エラー:", e)

    # スティッキーメッセージ処理
    try:
      sticky_res = await pool.fetch(
          "SELECT * FROM sticky_messages WHERE channel_id = $1",
          str(message.channel.id),
      )
      if sticky_res:
        sticky = sticky_res[0]
        if sticky["message_id"]:
          try:
            old_msg = await message.channel.fetch_message(
                int(sticky["message_id"])
            )
            if old_msg:
              await old_msg.delete()
          except Exception:
            pass
        embed = discord.Embed(
            title=sticky["title"],
            description=sticky["description"],
            color=discord.Color.from_str("#3498db"),
        )
        embed.timestamp = datetime.now()
        new_msg = await message.channel.send(embed=embed)
        await pool.execute(
            "UPDATE sticky_messages SET message_id = $1 WHERE channel_id = $2",
            str(new_msg.id),
            str(message.channel.id),
        )
    except Exception:
      pass

  async def _delete_later(self, message, seconds):
    await asyncio.sleep(seconds)
    try:
      await message.delete()
    except Exception:
      pass

  # 4. ボイスステート更新・VC自己紹介表示
  @commands.Cog.listener()
  async def on_voice_state_update(
      self,
      member: discord.Member,
      before: discord.VoiceState,
      after: discord.VoiceState,
  ):
    if before.channel == after.channel:
      return
    
    # member.guild から確実にサーバーを取得する
    guild = member.guild
    pool = getattr(self.bot, "pool", None)
    if not pool:
      return

    try:
      setting_res = await pool.fetchrow(
          "SELECT source_channel_id, keyword FROM intro_channel_settings WHERE"
          " guild_id = $1",
          str(guild.id),
      )
      if not setting_res:
        return
      source_channel_id = setting_res["source_channel_id"]
      keyword = setting_res["keyword"]
      source_channel = guild.get_channel(int(source_channel_id))
      if not source_channel:
        return

      messages = [m async for m in source_channel.history(limit=100)]

      async def update_vc_intro(channel):
        if not channel:
          return
        members = [m for m in channel.members if not m.bot]
        text = "参加メンバー\n\n"
        if not members:
          text += "現在、誰も参加していません。"
        else:
          for m in members:
            user_msg = next(
                (
                    msg
                    for msg in messages
                    if msg.author.id == m.id
                    and (
                        keyword in msg.content
                        if keyword
                        else "名前：" in msg.content
                    )
                ),
                None,
            )
            if user_msg:
              content = (
                  user_msg.content[:80] + "..."
                  if len(user_msg.content) > 80
                  else user_msg.content
              )
            else:
              content = "（自己紹介がありません）"
            text += f"• **{m.display_name}** :\n{content}\n\n"

        try:
          vc_msgs = [m async for m in channel.history(limit=30)]
          existing = next(
              (
                  m
                  for m in vc_msgs
                  if m.author.id == self.bot.user.id
                  and m.content.startswith("参加メンバー")
              ),
              None,
          )
          if existing:
            await existing.edit(content=text)
          else:
            await channel.send(text)
        except Exception as err:
          print("VC更新エラー:", err)

      if before.channel:
        await update_vc_intro(before.channel)
      if after.channel:
        await update_vc_intro(after.channel)
    except Exception as e:
      print("VCイベントエラー:", e)


async def setup(bot):
  await bot.add_cog(Events(bot))
