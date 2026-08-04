import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

# yt-dlpのオプション設定
YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": "True"}
FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn",
}


class MusicSelectView(discord.ui.View):

  def __init__(self):
    super().__init__(timeout=60)
    self.selection = None

  @discord.ui.button(
      label="URLから再生", style=discord.ButtonStyle.primary, emoji="🔗"
  )
  async def url_button(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    self.selection = "url"
    self.stop()
    await interaction.response.defer()

  @discord.ui.button(
      label="ファイルから再生", style=discord.ButtonStyle.secondary, emoji="📁"
  )
  async def file_button(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    self.selection = "file"
    self.stop()
    await interaction.response.defer()


class Music(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="join", description="あなたが接続しているボイスチャンネルに参加します"
  )
  async def join(self, interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
      await interaction.response.send_message(
          "先にボイスチャンネルに参加してください！", ephemeral=True
      )
      return

    channel = interaction.user.voice.channel
    if interaction.guild.voice_client is not None:
      await interaction.guild.voice_client.move_to(channel)
    else:
      await channel.connect()

    await interaction.response.send_message(
        f"📢 **{channel.name}** に参加しました！", ephemeral=True
    )

  @app_commands.command(
      name="leave", description="ボイスチャンネルから退出します"
  )
  async def leave(self, interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
      await interaction.response.send_message(
          "ボットはどのボイスチャンネルにも参加していません。", ephemeral=True
      )
      return

    channel_name = interaction.guild.voice_client.channel.name
    await interaction.guild.voice_client.disconnect()

    await interaction.response.send_message(
        f"👋 **{channel_name}** から退出しました！", ephemeral=True
    )

  @app_commands.command(
      name="play", description="指定したURLまたはファイルパスの音楽を再生します"
  )
  @app_commands.describe(music="再生するURLまたはローカルファイルパスを入力してください")
  async def play(self, interaction: discord.Interaction, music: str):
    if not interaction.guild.voice_client:
      await interaction.response.send_message(
          "ボットがボイスチャンネルに参加していません。先に `/join`"
          " を実行してください。",
          ephemeral=True,
      )
      return

    # 選択式ボタンを表示
    view = MusicSelectView()
    await interaction.response.send_message(
        f"入力された内容: `{music}`\n再生方法を選択してください：",
        view=view,
        ephemeral=True,
    )

    # ユーザーのボタン入力を待機
    await view.wait()

    if view.selection is None:
      try:
        await interaction.edit_original_response(
            content="選択時間がタイムアウトしました。", view=None
        )
      except Exception:
        pass
      return

    voice_client = interaction.guild.voice_client

    if view.selection == "url":
      await interaction.edit_original_response(
          content=f"🔗 URLから再生準備中... (`{music}`)", view=None
      )
      try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(music, download=False)
          url2 = info["url"]

        if voice_client.is_playing():
          voice_client.stop()

        source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)
        voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
        await interaction.edit_original_response(
            content=f"🎵 再生を開始しました: **{info.get('title', music)}**"
        )
      except Exception as e:
        await interaction.edit_original_response(
            content=f"❌ URLの再生に失敗しました: {e}"
        )

    elif view.selection == "file":
      await interaction.edit_original_response(
          content=f"📁 ファイルから再生準備中... (`{music}`)", view=None
      )
      if not os.path.exists(music):
        await interaction.edit_original_response(
            content=f"❌ 指定されたファイルが見つかりません: `{music}`"
        )
        return

      try:
        if voice_client.is_playing():
          voice_client.stop()

        source = discord.FFmpegPCMAudio(music)
        voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
        await interaction.edit_original_response(
            content=f"🎵 ローカルファイルの再生を開始しました: **{music}**"
        )
      except Exception as e:
        await interaction.edit_original_response(
            content=f"❌ ファイルの再生に失敗しました: {e}"
        )


async def setup(bot):
  await bot.add_cog(Music(bot))
