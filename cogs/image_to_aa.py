import io
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

ASCII_CHARS = ["⠀", "⠄", "⠆", "⠖", "⠶", "⡶", "⣩", "⣪", "⣫", "⣾", "⣿"][::-1]
WIDTH = 60


class ImageToAA(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="aa", description="画像をアスキーアート(AA)に変換します"
  )
  @app_commands.describe(image="変換したい画像ファイルをアップロードしてください")
  async def aa(
      self, interaction: discord.Interaction, image: discord.Attachment
  ):
    # 画像ファイル形式のチェック
    if not image.filename.lower().endswith(
        (".png", ".jpg", ".jpeg", ".webp")
    ):
      await interaction.response.send_message(
          "PNG、JPEG、WEBP形式の画像をアップロードしてください。",
          ephemeral=True,
      )
      return

    # 処理に少し時間がかかるため「考え中...」の表示にする
    await interaction.response.defer()

    try:
      image_bytes = await image.read()
      img = Image.open(io.BytesIO(image_bytes))

      w, h = img.size
      resized_img = img.resize(
          (WIDTH, int((h / w * WIDTH) / 2))
      ).convert("L")
      pixels = [ASCII_CHARS[p // 25] for p in list(resized_img.getdata())]
      aa_text = "\n".join(
          [
              "".join(pixels[i : i + WIDTH])
              for i in range(0, len(pixels), WIDTH)
          ]
      )

      if len(aa_text) > 1900:
        aa_text = aa_text[:1900] + "\n...(文字数制限のため省略)"

      await interaction.followup.send(f"```\n{aa_text}\n```")

    except Exception as e:
      await interaction.followup.send(
          f"❌ 変換中にエラーが発生しました: {e}"
      )


async def setup(bot):
  await bot.add_cog(ImageToAA(bot))
