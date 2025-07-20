import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Use environment variable or paste your token here

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

VC_CHANNEL_ID = 1354365519641313480  # 🔁 Replace with your voice channel ID

phonk_playlist = [
    "https://youtu.be/2dZwhUV898A?si=nbslaEOKRRGtMCVw",
    "https://youtu.be/VZufD5Y4KfQ?si=cuumX54scE42VPzO",
    "https://youtu.be/Y_FnFdvKkV8?si=t9AN9fyN_OOj3VOu",
]

async def play_phonk(vc):
    while True:
        for url in phonk_playlist:
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'noplaylist': True,
                    'default_search': 'auto',
                    'outtmpl': 'song.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

                if vc.is_playing():
                    vc.stop()

                vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print("🎵 Next..."))
                while vc.is_playing():
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Error playing {url}: {e}")
        await asyncio.sleep(2)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    vc = discord.utils.get(bot.get_all_channels(), id=VC_CHANNEL_ID)
    if after.channel == vc:
        try:
            voice_client = await vc.connect()
        except discord.ClientException:
            voice_client = discord.utils.get(bot.voice_clients, guild=vc.guild)

        if not voice_client.is_playing():
            await play_phonk(voice_client)

bot.run(TOKEN)
