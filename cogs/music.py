import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

# yt-dlpのオプション設定
YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": "True"}

# 警告が出ないように最適化したFFmpegオプション
FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn -b:a 192k",
}


class Music(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    # サーバーごとのループ状態を保持する辞書
    self.loop_modes = {}

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
    if interaction.guild_id in self.loop_modes:
      del self.loop_modes[interaction.guild_id]

    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message(
        f"👋 **{channel_name}** から退出しました！", ephemeral=True
    )

  @app_commands.command(name="stop", description="音楽の再生を停止します")
  async def stop(self, interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if not voice_client or not voice_client.is_playing():
      await interaction.response.send_message(
          "現在再生中の音楽はありません。", ephemeral=True
      )
      return

    voice_client.stop()
    if interaction.guild_id in self.loop_modes:
      self.loop_modes[interaction.guild_id]["type"] = "off"

    await interaction.response.send_message(
        "⏹️ 音楽の再生を停止しました。", ephemeral=True
    )

  @app_commands.command(
      name="repeat", description="現在の曲のループ再生を切り替えます"
  )
  @app_commands.choices(
      mode=[
          app_commands.Choice(name="オフ (Off)", value="off"),
          app_commands.Choice(name="1曲ループ (Single)", value="single"),
      ]
  )
  async def repeat(self, interaction: discord.Interaction, mode: str):
    guild_id = interaction.guild_id
    if guild_id not in self.loop_modes:
      self.loop_modes[guild_id] = {"type": "off", "url": None, "file_url": None}

    self.loop_modes[guild_id]["type"] = mode

    if mode == "single":
      await interaction.response.send_message(
          "🔂 1曲ループを有効にしました。", ephemeral=True
      )
    else:
      await interaction.response.send_message(
          "🔁 ループをオフにしました。", ephemeral=True
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

    if (url is None) == (file is None):
      await interaction.response.send_message(
          "❌ 「URL」または「ファイル」の**どちらか片方のみ**を必ず指定してください！",
          ephemeral=True,
      )
      return

    await interaction.response.defer(ephemeral=True)
    voice_client = interaction.guild.voice_client

    guild_id = interaction.guild_id
    if guild_id not in self.loop_modes:
      self.loop_modes[guild_id] = {"type": "off", "url": None, "file_url": None}

    if url:
      self.loop_modes[guild_id]["url"] = url
      self.loop_modes[guild_id]["file_url"] = None
    elif file:
      self.loop_modes[guild_id]["url"] = None
      self.loop_modes[guild_id]["file_url"] = file.url

    if voice_client.is_playing():
      voice_client.stop()

    def play_next(error):
      if error:
        print(f"Player error: {error}")
        return

      mode_data = self.loop_modes.get(guild_id, {"type": "off"})
      if mode_data["type"] == "single":
        try:
          if mode_data["url"]:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
              info = ydl.extract_info(mode_data["url"], download=False)
              audio_url = info["url"]
            source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
            voice_client.play(source, after=play_next)
          elif mode_data["file_url"]:
            source = discord.FFmpegPCMAudio(
                mode_data["file_url"], **FFMPEG_OPTIONS
            )
            voice_client.play(source, after=play_next)
        except Exception as e:
          print(f"Loop play error: {e}")

    try:
      if url:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
          info = ydl.extract_info(url, download=False)
          audio_url = info["url"]
          title = info.get("title", url)

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=play_next)
        await interaction.followup.send(
            f"🎵 URLから再生を開始しました: **{title}**", ephemeral=True
        )

      elif file:
        file_url = file.url
        filename = file.filename

        source = discord.FFmpegPCMAudio(file_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=play_next)
        await interaction.followup.send(
            f"🎵 ファイルから再生を開始しました: **{filename}**", ephemeral=True
        )

    except Exception as e:
      await interaction.followup.send(
          f"❌ 再生に失敗しました: {e}", ephemeral=True
      )


async def setup(bot):
  await bot.add_cog(Music(bot))
