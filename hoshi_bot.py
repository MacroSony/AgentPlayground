import discord
from discord import app_commands
import os
import asyncio
import logging
import time
import json
from file_tools.tools import read_file, write_file

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('hoshi_bot')

class HoshiBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.inbox_file = "inbox.txt"

    async def setup_hook(self):
        # Register commands
        
        @self.tree.command(name="status", description="Check if Hoshi is active")
        async def status_cmd(interaction: discord.Interaction):
            await interaction.response.send_message('Hoshi is active and monitoring.')

        @self.tree.command(name="tasks", description="List current tasks")
        async def tasks_cmd(interaction: discord.Interaction):
            tasks_str = "No tasks found."
            if os.path.exists("tasks.json"):
                try:
                    with open("tasks.json", "r") as f:
                        tasks = json.load(f)
                        if tasks:
                            tasks_str = "\n".join([f"**[{t['status']}]** #{t['id']}: {t['description']}" for t in tasks])
                except Exception:
                    pass
            await interaction.response.send_message(f"**Current Tasks:**\n{tasks_str}")

        @self.tree.command(name="usage", description="Check API usage")
        async def usage_cmd(interaction: discord.Interaction):
            try:
                from file_tools.tools import get_usage
                usage = get_usage()
                await interaction.response.send_message(f"**API Usage:**\n{usage}")
            except Exception as e:
                await interaction.response.send_message(f"Failed to get usage: {e}")

        @self.tree.command(name="report", description="Get the latest full status report")
        async def report_cmd(interaction: discord.Interaction):
            try:
                await interaction.response.defer()
                from file_tools.reporting_tools import generate_status_report
                report = generate_status_report()
                if len(report) > 1900:
                    await interaction.followup.send(f"```markdown\n{report[:1900]}\n```")
                    for i in range(1900, len(report), 1900):
                        await interaction.channel.send(f"```markdown\n{report[i:i+1900]}\n```")
                else:
                    await interaction.followup.send(f"```markdown\n{report}\n```")
            except Exception as e:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"Failed to generate report: {e}")
                else:
                    await interaction.followup.send(f"Failed to generate report: {e}")

        @self.tree.command(name="switch", description="Switch model tier and restart")
        @app_commands.describe(tier="The model tier to switch to")
        @app_commands.choices(tier=[
            app_commands.Choice(name="Flash", value="flash"),
            app_commands.Choice(name="Pro", value="pro")
        ])
        async def switch_cmd(interaction: discord.Interaction, tier: app_commands.Choice[str]):
            try:
                val = tier.value
                model_name = "gemini-3-flash-preview" if val == 'flash' else "gemini-3.1-pro-preview"
                with open("active_model.txt", "w") as f:
                    f.write(model_name)
                with open("restart_signal.txt", "w") as f:
                    f.write(f"Model switch to {val} by Discord user {interaction.user}")
                await interaction.response.send_message(f"🔄 Switching to **{val.upper()}** model. Restarting agent...")
            except Exception as e:
                await interaction.response.send_message(f"Failed to switch model: {e}")

        @self.tree.command(name="restart", description="Restart the agent loop")
        async def restart_cmd(interaction: discord.Interaction):
            try:
                with open("restart_signal.txt", "w") as f:
                    f.write(f"Restart requested by Discord user {interaction.user}")
                await interaction.response.send_message("🔄 Restarting agent...")
            except Exception as e:
                await interaction.response.send_message(f"Failed to trigger restart: {e}")

        @self.tree.command(name="research", description="Perform a deep, multi-step research on a topic")
        @app_commands.describe(topic="The research query")
        async def research_cmd(interaction: discord.Interaction, topic: str):
            await interaction.response.send_message(f"🔍 Starting deep research on: **{topic}**...\n- Status: Initializing...")
            msg = await interaction.original_response()
            
            try:
                from file_tools.research_tools import deep_search
                await interaction.edit_original_response(content=f"🔍 Deep research: **{topic}**\n- Status: Searching the web...")
                report = await asyncio.to_thread(deep_search, topic, max_depth=2, breadths=2)
                await interaction.edit_original_response(content=f"🔍 Deep research: **{topic}**\n- Status: Complete! Summary sent below.")
                
                if len(report) > 1900:
                    snippet = report[:1500] + "...\n\n(Full report attached below)"
                    await interaction.followup.send(f"### Research Report: {topic}\n\n{snippet}")
                    temp_filename = f"research_{int(time.time())}.md"
                    with open(temp_filename, "w") as f:
                        f.write(report)
                    await interaction.followup.send(file=discord.File(temp_filename))
                else:
                    await interaction.followup.send(f"### Research Report: {topic}\n\n{report}")
            except Exception as e:
                logger.error(f"Deep search failed: {e}")
                await interaction.edit_original_response(content=f"❌ Deep research: **{topic}**\n- Status: Failed\n- Error: {str(e)[:100]}")

        self.loop.create_task(self.poll_outbox())
        await self.tree.sync()

    async def poll_outbox(self):
        last_pos = 0
        outbox_file = "discord_outbox.txt"
        if os.path.exists(outbox_file):
            last_pos = os.path.getsize(outbox_file)
            
        while not self.is_closed():
            if os.path.exists(outbox_file):
                current_size = os.path.getsize(outbox_file)
                if current_size > last_pos:
                    with open(outbox_file, "r") as f:
                        f.seek(last_pos)
                        lines = f.readlines()
                    last_pos = current_size
                    for line in lines:
                        if not line.strip(): continue
                        try:
                            data = json.loads(line)
                            channel_id_raw = data.get("channel_id")
                            if str(channel_id_raw).lower() == "none" or not channel_id_raw:
                                channel_id = None
                            else:
                                channel_id = int(channel_id_raw)
                            msg = data["message"]
                            
                            if channel_id:
                                channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                                if channel:
                                    for i in range(0, len(msg), 1900):
                                        await channel.send(msg[i:i+1900])
                            else:
                                logger.warning(f"Skipping outbox message due to missing channel ID: {msg[:50]}...")
                        except Exception as e:
                            logger.error(f"Failed to send from outbox: {e}")
            await asyncio.sleep(2)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return

        # Filtering: Only listen to direct @ mentions or responses to her previous messages
        is_mentioned = self.user.mentioned_in(message)
        is_reply_to_me = False
        if message.reference and message.reference.message_id:
             try:
                 referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                 if referenced_msg.author == self.user:
                     is_reply_to_me = True
             except Exception:
                 pass
        
        if not (is_mentioned or is_reply_to_me):
            return

        # Log the message to inbox.txt for the cognitive loop to process
        logger.info(f"Received message from {message.author} in {message.channel.id}: {message.content}")
        with open(self.inbox_file, "a") as f:
            f.write(f"DISCORD_USER [{message.author}] (Channel: {message.channel.id}): {message.content}\n")
        
        try:
            # Acknowledge with a reaction instead of a message to avoid spam
            await message.add_reaction('✅')
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")

async def main():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = HoshiBot(intents=intents)
    async with client:
        await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())
