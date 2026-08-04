  @app_commands.command(
      name="join", description="あなたが接続しているボイスチャンネルに参加します"
  )
  async def join(self, interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
      await interaction.response.send_message(
          "先にボイスチャンネルに参加してください！", ephemeral=True
      )
      return

    # ★ 3秒制限のタイムアウトを防ぐため、先に「考え中（保留）」の状態にする
    await interaction.response.defer(ephemeral=True)

    channel = interaction.user.voice.channel
    try:
      if interaction.guild.voice_client is not None:
        await interaction.guild.voice_client.move_to(channel)
      else:
        await channel.connect()

      # 接続完了後にメッセージを送信
      await interaction.followup.send(
          f"📢 **{channel.name}** に参加しました！", ephemeral=True
      )
    except Exception as e:
      await interaction.followup.send(
          f"❌ 接続に失敗しました: {e}", ephemeral=True
      )
