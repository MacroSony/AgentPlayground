import discord
import os
import asyncio
from file_tools.tools import read_file, write_file

class HoshiBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inbox_file = "inbox.txt"

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return

        # Simple command to check status
        if message.content.startswith('!status'):
            await message.channel.send('Hoshi is active and monitoring.')
            return

        # Log the message to inbox.txt for the cognitive loop to process
        with open(self.inbox_file, "a") as f:
            f.write(f"DISCORD_USER [{message.author}]: {message.content}\n")
        
        await message.channel.send(f'Message received, {message.author.display_name}. I will process it soon.')

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
