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

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        # Send a startup message if a default channel is known? 
        # For now just log.

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

        # Simple command to check status
        if message.content.startswith('!status') or '!status' in message.content:
            await message.channel.send('Hoshi is active and monitoring.')
            return

        # Log the message to inbox.txt for the cognitive loop to process
        logger.info(f"Received message from {message.author}: {message.content}")
        with open(self.inbox_file, "a") as f:
            f.write(f"DISCORD_USER [{message.author}]: {message.content}\n")
        
        try:
            await message.channel.send(f'Message received, {message.author.display_name}. I will process it soon.')
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")

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
