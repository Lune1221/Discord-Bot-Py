import discord
from discord.ext import commands
from discord import app_commands


# ========================================
# ロールパネル設定
# ========================================

ROLES = {
    123456789012345678: {
        "name": "お知らせ",
        "emoji": "📢",
        "style": discord.ButtonStyle.primary,
    },

    234567890123456789: {
        "name": "ゲーム",
        "emoji": "🎮",
        "style": discord.ButtonStyle.success,
    },

    345678901234567890: {
        "name": "イベント",
        "emoji": "🎉",
        "style": discord.ButtonStyle.danger,
    },
}


# ========================================
# ロールボタン
# ========================================

class RoleButton(discord.ui.Button):

    def __init__(
        self,
        role_id: int,
        name: str,
        emoji: str,
        style: discord.ButtonStyle
    ):
        super().__init__(
            label=name,
            emoji=emoji,
            style=style,
            custom_id=f"role_panel:{role_id}"
        )

        self.role_id = role_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        # サーバー以外では使用不可
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        # ロール取得
        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ 設定されたロールが存在しません。",
                ephemeral=True
            )
            return

        # メンバー取得
        member = interaction.user

        # Botのロールより上なら操作不可
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ このロールはBotが操作できません。\n"
                "Botのロールを対象ロールより上に移動してください。",
                ephemeral=True
            )
            return

        try:

            # ========================================
            # ロールを持っている → 解除
            # ========================================

            if role in member.roles:

                await member.remove_roles(role)

                await interaction.response.send_message(
                    f"🔴 **{role.name}** のロールを解除しました。",
                    ephemeral=True
                )

            # ========================================
            # ロールを持っていない → 付与
            # ========================================

            else:

                await member.add_roles(role)

                await interaction.response.send_message(
                    f"🟢 **{role.name}** のロールを取得しました。",
                    ephemeral=True
                )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにロールを操作する権限がありません。",
                ephemeral=True
            )

        except Exception as e:

            print(
                f"ロール操作エラー: {e}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ ロールの操作中にエラーが発生しました。",
                ephemeral=True
            )


# ========================================
# ロールパネルView
# ========================================

class RolePanelView(discord.ui.View):

    def __init__(self):

        # timeout=None = 永続View
        super().__init__(timeout=None)

        for role_id, config in ROLES.items():

            self.add_item(
                RoleButton(
                    role_id=role_id,
                    name=config["name"],
                    emoji=config["emoji"],
                    style=config["style"]
                )
            )


# ========================================
# Cog
# ========================================

class RolePanel(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot

        # Bot再起動後も既存ボタンを動かす
        self.bot.add_view(RolePanelView())

    # ========================================
    # /rolepanel
    # ========================================

    @app_commands.command(
        name="rolepanel",
        description="ロール取得パネルを設置します"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def rolepanel(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="🎭 ロールパネル",
            description=(
                "取得したいロールのボタンを押してください。\n\n"
                "🟢 ボタンを押す → ロール取得\n"
                "🔴 もう一度押す → ロール解除"
            ),
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text="ロールはいつでも変更できます。"
        )

        await interaction.channel.send(
            embed=embed,
            view=RolePanelView()
        )

        await interaction.response.send_message(
            "✅ ロールパネルを設置しました。",
            ephemeral=True
        )

    # ========================================
    # 権限エラー
    # ========================================

    @rolepanel.error
    async def rolepanel_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):

        if isinstance(
            error,
            app_commands.errors.MissingPermissions
        ):

            await interaction.response.send_message(
                "❌ このコマンドは管理者のみ使用できます。",
                ephemeral=True
            )

        else:

            print(
                f"/rolepanel エラー: {error}",
                flush=True
            )

            await interaction.response.send_message(
                "❌ コマンドの実行中にエラーが発生しました。",
                ephemeral=True
            )


# ========================================
# Cog読み込み
# ========================================

async def setup(bot: commands.Bot):

    await bot.add_cog(
        RolePanel(bot)
    )
