import discord
import os
import asyncio
import logging
from file_tools.tools import read_file, write_file

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('hoshi_bot')

class HoshiBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inbox_file = "inbox.txt"

    async def poll_outbox(self):
        import json
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
                            channel_id = int(data["channel_id"])
                            msg = data["message"]
                            channel = self.get_channel(channel_id) or await self.fetch_channel(channel_id)
                            if channel:
                                for i in range(0, len(msg), 1900):
                                    await channel.send(msg[i:i+1900])
                        except Exception as e:
                            logger.error(f"Failed to send from outbox: {e}")
            await asyncio.sleep(2)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.loop.create_task(self.poll_outbox())

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

        # Commands
        if '!status' in message.content:
            await message.channel.send('Hoshi is active and monitoring.')
            return
            
        if '!tasks' in message.content:
            import json
            tasks_str = "No tasks found."
            if os.path.exists("tasks.json"):
                try:
                    with open("tasks.json", "r") as f:
                        tasks = json.load(f)
                        if tasks:
                            tasks_str = "\n".join([f"**[{t['status']}]** #{t['id']}: {t['description']}" for t in tasks])
                except Exception:
                    pass
            await message.channel.send(f"**Current Tasks:**\n{tasks_str}")
            return
            
        if '!help' in message.content:
            help_text = (
                "**Hoshi Bot Commands:**\n"
                "`!status` - Check if Hoshi is active.\n"
                "`!tasks` - List current tasks.\n"
                "`!report` - Get the latest full status report.\n"
                "`!research <topic>` - Perform a deep, multi-step research on a topic.\n"
                "`!help` - Show this message.\n"
                "Mention me (@Hoshi) to send a message to my inbox for cognitive processing."
            )
            await message.channel.send(help_text)
            return

        if '!report' in message.content:
            try:
                from file_tools.reporting_tools import generate_status_report
                report = generate_status_report()
                for i in range(0, len(report), 1900):
                    await message.channel.send(f"```markdown\n{report[i:i+1900]}\n```")
            except Exception as e:
                await message.channel.send(f"Failed to generate report: {e}")
            return

        if '!research' in message.content or '!deep_search' in message.content:
            cmd = '!research' if '!research' in message.content else '!deep_search'
            query = message.content.replace(cmd, '').replace(f'<@{self.user.id}>', '').strip()
            if not query:
                await message.channel.send(f"Please provide a research query. Usage: `{cmd} <topic>`")
                return
            
            # Initial feedback
            msg = await message.channel.send(f"🔍 Starting deep research on: **{query}**...\n- Status: Initializing...")
            
            try:
                async with message.channel.typing():
                    from file_tools.research_tools import deep_search
                    
                    # Update status to searching
                    await msg.edit(content=f"🔍 Deep research: **{query}**\n- Status: Searching the web...")
                    
                    # Run deep search in a thread to not block the bot
                    report = await asyncio.to_thread(deep_search, query, max_depth=2, breadths=2)
                    
                    # Final feedback
                    await msg.edit(content=f"🔍 Deep research: **{query}**\n- Status: Complete! Summary sent below.")
                    
                    if len(report) > 1900:
                        # If long, create a snippet and a file
                        snippet = report[:1500] + "...\n\n(Full report attached below)"
                        await message.channel.send(f"### Research Report: {query}\n\n{snippet}")
                        
                        temp_filename = f"research_{int(time.time())}.md"
                        with open(temp_filename, "w") as f:
                            f.write(report)
                        await message.channel.send(file=discord.File(temp_filename))
                        # Cleanup file later or leave it if ephemeral
                    else:
                        await message.channel.send(f"### Research Report: {query}\n\n{report}")
            except Exception as e:
                logger.error(f"Deep search failed: {e}")
                await msg.edit(content=f"❌ Deep research: **{query}**\n- Status: Failed\n- Error: {str(e)[:100]}")
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
