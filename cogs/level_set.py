import discord
from discord import app_commands
from discord.ext import commands


class LevelRoleGroup(app_commands.Group):
    def __init__(self, bot):
        super().__init__(
            name="level-role",
            description="メッセージ数によるロール報酬を設定します【管理者専用】",
        )
        self.bot = bot

    async def ensure_table(self):
        pool = self.bot.pool

        await pool.execute(
            """
            CREATE TABLE IF NOT EXISTS level_role_rewards (
                guild_id TEXT NOT NULL,
                required_messages BIGINT NOT NULL,
                add_role_id TEXT NOT NULL,
                remove_role_id TEXT,
                notification_mode TEXT NOT NULL DEFAULT 'source',
                notification_channel_id TEXT,
                PRIMARY KEY (guild_id, required_messages)
            )
            """
        )

    @app_commands.command(
        name="set",
        description="メッセージ数到達時のロール報酬を設定します",
    )
    @app_commands.describe(
        messages="このメッセージ数に到達したときに報酬を付与します",
        add_role="到達時に付与するロール",
        remove_role="到達時に削除するロール（任意）",
        notification="通知場所",
        channel="通知先チャンネル（「指定チャンネル」の場合のみ）",
    )
    @app_commands.choices(
        notification=[
            app_commands.Choice(
                name="達成したメッセージのチャンネル",
                value="source",
            ),
            app_commands.Choice(
                name="指定したチャンネル",
                value="channel",
            ),
        ]
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_reward(
        self,
        interaction: discord.Interaction,
        messages: int,
        add_role: discord.Role,
        remove_role: discord.Role | None = None,
        notification: app_commands.Choice[str] | None = None,
        channel: discord.TextChannel | None = None,
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        if messages <= 0:
            await interaction.followup.send(
                "❌ 必要メッセージ数は1以上にしてください。",
                ephemeral=True,
            )
            return

        notification_mode = (
            notification.value
            if notification
            else "source"
        )

        if notification_mode == "channel" and channel is None:
            await interaction.followup.send(
                "❌ 「指定したチャンネル」を選択した場合は、通知先チャンネルを指定してください。",
                ephemeral=True,
            )
            return

        if notification_mode == "source":
            channel = None

        # Bot自身の最高位ロールを取得
        bot_member = interaction.guild.me

        if bot_member is None:
            await interaction.followup.send(
                "❌ Botのサーバー情報を取得できませんでした。",
                ephemeral=True,
            )
            return

        # Botが対象ロールを操作できるか確認
        if add_role >= bot_member.top_role:
            await interaction.followup.send(
                f"❌ {add_role.mention} はBotの最高位ロール以上にあるため、付与できません。",
                ephemeral=True,
            )
            return

        if remove_role is not None:
            if remove_role >= bot_member.top_role:
                await interaction.followup.send(
                    f"❌ {remove_role.mention} はBotの最高位ロール以上にあるため、削除できません。",
                    ephemeral=True,
                )
                return

        if add_role.is_default():
            await interaction.followup.send(
                "❌ @everyone を報酬ロールにすることはできません。",
                ephemeral=True,
            )
            return

        if remove_role is not None and remove_role.is_default():
            await interaction.followup.send(
                "❌ @everyone を削除対象ロールにすることはできません。",
                ephemeral=True,
            )
            return

        if remove_role is not None and add_role.id == remove_role.id:
            await interaction.followup.send(
                "❌ 付与するロールと削除するロールを同じにはできません。",
                ephemeral=True,
            )
            return

        pool = self.bot.pool

        try:
            await self.ensure_table()

            await pool.execute(
                """
                INSERT INTO level_role_rewards (
                    guild_id,
                    required_messages,
                    add_role_id,
                    remove_role_id,
                    notification_mode,
                    notification_channel_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (guild_id, required_messages)
                DO UPDATE SET
                    add_role_id = EXCLUDED.add_role_id,
                    remove_role_id = EXCLUDED.remove_role_id,
                    notification_mode = EXCLUDED.notification_mode,
                    notification_channel_id = EXCLUDED.notification_channel_id
                """,
                str(interaction.guild.id),
                messages,
                str(add_role.id),
                str(remove_role.id) if remove_role else None,
                notification_mode,
                str(channel.id) if channel else None,
            )

            if notification_mode == "source":
                notification_text = "達成したメッセージのチャンネル"
            else:
                notification_text = channel.mention

            remove_text = (
                f"\n削除するロール：{remove_role.mention}"
                if remove_role
                else "\n削除するロール：なし"
            )

            await interaction.followup.send(
                "✅ レベルロール報酬を設定しました。\n\n"
                f"必要メッセージ数：**{messages:,}**\n"
                f"付与するロール：{add_role.mention}"
                f"{remove_text}\n"
                f"通知先：{notification_text}",
                ephemeral=True,
            )

        except Exception as error:
            print("レベルロール設定エラー:", error)

            await interaction.followup.send(
                "❌ レベルロール報酬の保存に失敗しました。",
                ephemeral=True,
            )

    @app_commands.command(
        name="list",
        description="設定されているレベルロール報酬を一覧表示します",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_rewards(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        try:
            await self.ensure_table()

            rows = await self.bot.pool.fetch(
                """
                SELECT
                    required_messages,
                    add_role_id,
                    remove_role_id,
                    notification_mode,
                    notification_channel_id
                FROM level_role_rewards
                WHERE guild_id = $1
                ORDER BY required_messages ASC
                """,
                str(interaction.guild.id),
            )

            if not rows:
                await interaction.followup.send(
                    "現在、レベルロール報酬は設定されていません。",
                    ephemeral=True,
                )
                return

            lines = []

            for row in rows:
                add_role = interaction.guild.get_role(
                    int(row["add_role_id"])
                )

                remove_role = None

                if row["remove_role_id"]:
                    remove_role = interaction.guild.get_role(
                        int(row["remove_role_id"])
                    )

                if row["notification_mode"] == "source":
                    notification = "達成メッセージのチャンネル"
                else:
                    channel = None

                    if row["notification_channel_id"]:
                        channel = interaction.guild.get_channel(
                            int(row["notification_channel_id"])
                        )

                    notification = (
                        channel.mention
                        if channel
                        else "削除済みチャンネル"
                    )

                add_name = (
                    add_role.mention
                    if add_role
                    else "削除済みロール"
                )

                remove_name = (
                    remove_role.mention
                    if remove_role
                    else "なし"
                )

                lines.append(
                    f"**{row['required_messages']:,} メッセージ**\n"
                    f"付与：{add_name}\n"
                    f"削除：{remove_name}\n"
                    f"通知：{notification}"
                )

            embed = discord.Embed(
                title="レベルロール報酬設定",
                description="\n\n".join(lines),
                color=discord.Color.from_str("#3498db"),
            )

            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )

        except Exception as error:
            print("レベルロール一覧エラー:", error)

            await interaction.followup.send(
                "❌ 設定の取得に失敗しました。",
                ephemeral=True,
            )

    @app_commands.command(
        name="remove",
        description="指定したメッセージ数のレベルロール報酬を削除します",
    )
    @app_commands.describe(
        messages="削除する報酬の必要メッセージ数",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_reward(
        self,
        interaction: discord.Interaction,
        messages: int,
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.guild:
            await interaction.followup.send(
                "❌ このコマンドはサーバー内でのみ使用できます。",
                ephemeral=True,
            )
            return

        try:
            await self.ensure_table()

            result = await self.bot.pool.execute(
                """
                DELETE FROM level_role_rewards
                WHERE guild_id = $1
                  AND required_messages = $2
                """,
                str(interaction.guild.id),
                messages,
            )

            if result == "DELETE 0":
                await interaction.followup.send(
                    f"❌ **{messages:,}** メッセージの報酬設定は存在しません。",
                    ephemeral=True,
                )
                return

            await interaction.followup.send(
                f"✅ **{messages:,}** メッセージ到達時の報酬設定を削除しました。",
                ephemeral=True,
            )

        except Exception as error:
            print("レベルロール削除エラー:", error)

            await interaction.followup.send(
                "❌ 設定の削除に失敗しました。",
                ephemeral=True,
            )


class LevelSet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="level-set",
        description="レベリングの通知を送信するチャンネルを設定します【管理者専用】",
    )
    @app_commands.describe(
        channel="通知を送るテキストチャンネルを指定してください"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def level_set(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        await interaction.response.defer()

        guild_id = str(interaction.guild_id)
        pool = self.bot.pool

        try:
            await pool.execute(
                """
                INSERT INTO guild_settings (guild_id, level_channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET level_channel_id = EXCLUDED.level_channel_id
                """,
                guild_id,
                str(channel.id),
            )

            await interaction.followup.send(
                f"✅ レベルアップ通知チャンネルを {channel.mention} に設定しました！"
            )

        except Exception as error:
            print(error)

            await interaction.followup.send(
                "❌ 設定の保存に失敗しました。",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(LevelSet(bot))

    # Slash command group
    bot.tree.add_command(LevelRoleGroup(bot))
