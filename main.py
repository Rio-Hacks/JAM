import os
import discord
from discord.ext import commands
import asyncio
import yt_dlp
from keep_alive import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

PHONK_PLAYLIST = [
    "https://youtu.be/2dZwhUV898A?si=nbslaEOKRRGtMCVw",
    "https://youtu.be/VZufD5Y4KfQ?si=cuumX54scE42VPzO",
    "https://youtu.be/Y_FnFdvKkV8?si=t9AN9fyN_OOj3VOu"
]

current_song = None
song_queue = asyncio.Queue()
is_radio_mode = True

async def join_and_play(vc_channel):
    global is_radio_mode
    if bot.voice_clients:
        vc = bot.voice_clients[0]
        if vc.channel.id != vc_channel.id:
            await vc.move_to(vc_channel)
    else:
        vc = await vc_channel.connect()

    await start_radio(vc)

async def start_radio(vc):
    global is_radio_mode
    is_radio_mode = True
    while is_radio_mode and vc.is_connected():
        for url in PHONK_PLAYLIST:
            if not is_radio_mode:
                return
            await play_url(vc, url)
            while vc.is_playing():
                await asyncio.sleep(1)

async def play_url(vc, url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
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

    vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: print("⏭️ Finished."))

@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions and message.author.voice and message.author.voice.channel:
        await join_and_play(message.author.voice.channel)
        await message.channel.send("🎶 Bot summoned and started playing Phonk radio!")

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    vc = discord.utils.get(bot.voice_clients, guild=member.guild)
    if vc and vc.channel and len(vc.channel.members) == 1:
        await vc.disconnect()
        print("👋 Disconnected because VC is empty.")

@bot.command()
async def play(ctx, *, search):
    global is_radio_mode
    is_radio_mode = False
    vc = ctx.author.voice.channel
    if not ctx.voice_client:
        await vc.connect()
    else:
        await ctx.voice_client.move_to(vc)

    ydl_opts = {'quiet': True, 'format': 'bestaudio', 'default_search': 'ytsearch', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        url = info['entries'][0]['webpage_url'] if 'entries' in info else info['webpage_url']

    await ctx.send(f"🎵 Playing: {url}")
    await play_url(ctx.voice_client, url)
    while ctx.voice_client.is_playing():
        await asyncio.sleep(1)
    await start_radio(ctx.voice_client)  # Resume radio

@bot.command()
async def stop(ctx):
    global is_radio_mode
    is_radio_mode = False
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Stopped and left the VC.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")

keep_alive()
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
