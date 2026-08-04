import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

# yt-dlpのオプション設定
YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": "True"}

# 音質と安定性を向上させたFFmpegオプション
FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn -ar 48000 -ac 2 -b:a 192k",
}


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

    await interaction.response.defer(ephemeral=True)
    channel = interaction.user.voice.channel
    try:
      if interaction.guild.voice_client is not None:
        await interaction.guild.voice_client.move_to(channel)
      else:
        await channel.connect()

      await interaction.followup.send(
          f"📢 **{channel.name}** に参加しました！", ephemeral=True
      )
    except Exception as e:
      await interaction.followup.send(
          f"❌ 参加に失敗しました: {e}", ephemeral=True
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
      name="play", description="URLまたは音声ファイル（添付）を再生します"
  )
  @app_commands.describe(
      url="再生する音楽のURLを入力してください",
      file="再生する音声ファイル（mp3/wavなど）を添付してください",
  )
  async def play(
      self,
      interaction: discord.Interaction,
      url: str = None,
      file: discord.Attachment = None,
  ):
    if not interaction.guild.voice_client:
      await interaction.response.send_message(
          "ボットがボイスチャンネルに参加していません。先に `/join`"
          " を実行してください。",
          ephemeral=True,
      )
      return

    # どちらも未指定、または両方指定されている場合はエラーにする
    if (url is None) == (file is None):
      await interaction.response.send_message(
          "❌ 「URL」または「ファイル」の**どちらか片方のみ**を必ず指定してください！",
          ephemeral=True,
      )
      return

    await interaction.response.defer(ephemeral=True)
    voice_client = interaction.guild.voice_client

    if voice_client.is_playing():
      voice_client.stop()

    try:
      if url:
        # URLからの再生処理
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(url, download=False)
          audio_url = info["url"]
          title = info.get("title", url)

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
        await interaction.followup.send(
            f"🎵 URLから再生を開始しました: **{title}**", ephemeral=True
        )

      elif file:
        # 添付ファイルからの再生処理
        file_url = file.url
        filename = file.filename

        source = discord.FFmpegPCMAudio(file_url, **FFMPEG_OPTIONS)
        voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )
        await interaction.followup.send(
            f"🎵 ファイルから再生を開始しました: **{filename}**", ephemeral=True
        )

    except Exception as e:
      await interaction.followup.send(
          f"❌ 再生に失敗しました: {e}", ephemeral=True
      )


async def setup(bot):
  await bot.add_cog(Music(bot))
