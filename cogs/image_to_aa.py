import io
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

# 点字ブロック風の文字マップ（濃い順）
ASCII_CHARS = ["⠀", "⠄", "⠆", "⠖", "⠶", "⡶", "⣩", "⣪", "⣫", "⣾", "⣿"][::-1]


class ImageToAA(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(
      name="aa", description="画像をアスキーアート(AA)に変換します"
  )
  @app_commands.describe(
      image="変換したい画像ファイルをアップロードしてください",
      mode="スマホなどで崩れにくいように横幅を選べます（デフォルト: 標準）",
  )
  @app_commands.choices(
      mode=[
          app_commands.Choice(name="標準 (幅60)", value=60),
          app_commands.Choice(name="スマホ向け・細め (幅35)", value=35),
      ]
  )
  async def aa(
      self,
      interaction: discord.Interaction,
      image: discord.Attachment,
      mode: int = 60,  # デフォルトの横幅は60
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

      width = mode
      w, h = img.size
      # アスペクト比を維持しつつ、文字の縦横比を考慮してリサイズ
      resized_img = img.resize(
          (width, int((h / w * width) / 2))
      ).convert("L")
      
      pixels = [ASCII_CHARS[p // 25] for p in list(resized_img.getdata())]
      aa_text = "\n".join(
          [
              "".join(pixels[i : i + width])
              for i in range(0, len(pixels), width)
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
