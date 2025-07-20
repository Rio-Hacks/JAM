import discord
from discord.ext import commands, tasks
import asyncio
import yt_dlp
import os
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1331178993390718999  # Optional: add for optimization
MUSIC_VC_ID = 1354365519641313480
PHONK_MP3_URL = "https://github.com/Rio-Hacks/JAM/raw/main/AURA%20%3D%20%E2%99%BE%EF%B8%8F%20_%20VIRAL%20AURA%20MUSIC%20PLAYLIST%202025%20%F0%9F%94%A5%201%20HOUR.mp3"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

vc_client = None
current_vc = None
radio_mode = True

async def play_url(vc, url):
    global radio_mode
    radio_mode = False
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
    vc.play(discord.FFmpegPCMAudio(filename), after=lambda e: asyncio.run_coroutine_threadsafe(start_radio(vc), bot.loop))

async def start_radio(vc):
    global radio_mode
    if vc.is_playing():
        vc.stop()
    radio_mode = True
    vc.play(discord.FFmpegPCMAudio(PHONK_MP3_URL), after=lambda e: asyncio.run_coroutine_threadsafe(start_radio(vc), bot.loop))

async def join_and_play(vc_channel):
    global vc_client, current_vc
    if vc_client and vc_client.is_connected():
        await vc_client.move_to(vc_channel)
    else:
        vc_client = await vc_channel.connect()
    current_vc = vc_channel
    await start_radio(vc_client)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready: {bot.user}")
    check_empty_vc.start()

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == MUSIC_VC_ID and not member.bot:
        if not any(m for m in after.channel.members if not m.bot):
            return
        await join_and_play(after.channel)

@tasks.loop(seconds=15)
async def check_empty_vc():
    global vc_client
    if vc_client and vc_client.channel:
        if len([m for m in vc_client.channel.members if not m.bot]) == 0:
            await vc_client.disconnect()
            print("👋 Left VC as it was empty.")

@bot.event
async def on_message(message):
    global vc_client
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        if message.author.voice and message.author.voice.channel:
            await join_and_play(message.author.voice.channel)

    await bot.process_commands(message)

@bot.command()
async def play(ctx, *, search: str):
    vc = ctx.author.voice.channel

    # If already connected, reuse it
    if ctx.voice_client:
        voice = ctx.voice_client
    else:
        voice = await vc.connect()

    # Stop aura.mp3 or anything currently playing
    if voice.is_playing():
        voice.stop()

    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        'quiet': True
    }

    ffmpeg_opts = {
        'options': '-vn'
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        url2 = info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_opts)
        voice.play(source)
        await ctx.send(f"🎵 Now playing: {info.get('title')}")


@bot.command()
async def pause(ctx):
    if vc_client and vc_client.is_playing():
        vc_client.pause()
        await ctx.send("⏸️ Paused.")

@bot.command()
async def resume(ctx):
    if vc_client and vc_client.is_paused():
        vc_client.resume()
        await ctx.send("▶️ Resumed.")

@bot.command()
async def skip(ctx):
    if vc_client:
        vc_client.stop()
        await ctx.send("⏭️ Skipped.")

@bot.command()
async def exit(ctx):
    if vc_client:
        await vc_client.disconnect()
        await ctx.send("👋 Left the voice channel.")

keep_alive()
bot.run(TOKEN)
