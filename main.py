import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from keep_alive import keep_alive
import yt_dlp
import asyncio

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1331178993390718999
MUSIC_VC_ID = 1354365519641313480

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

RADIO_FILE = "https://github.com/Rio-Hacks/JAM/raw/main/AURA%20%3D%20%E2%99%BE%EF%B8%8F%20_%20VIRAL%20AURA%20MUSIC%20PLAYLIST%202025%20%F0%9F%94%A5%201%20HOUR.mp3"
radio_playing = False

# --- Utility to play audio with error handling ---
def play_audio(vc, source):
    if vc.is_playing():
        vc.stop()
    vc.play(
        FFmpegPCMAudio(source),
        after=lambda e: print(f"[AUDIO ERROR] {e}") if e else None
    )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    # Auto join and play radio in specific VC
    if after.channel and after.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if not vc or not vc.is_connected():
            try:
                vc = await after.channel.connect(timeout=10.0)
                play_audio(vc, RADIO_FILE)
            except asyncio.TimeoutError:
                print("❌ Timeout joining VC")

    # Auto leave when no one is left
    if before.channel and before.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if vc and len(vc.channel.members) == 1:
            await vc.disconnect()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        if message.author.voice and message.author.voice.channel:
            vc = discord.utils.get(bot.voice_clients, guild=message.guild)
            if vc and vc.channel != message.author.voice.channel:
                await vc.move_to(message.author.voice.channel)
            elif not vc:
                try:
                    vc = await message.author.voice.channel.connect(timeout=10.0)
                except asyncio.TimeoutError:
                    print("❌ Timeout joining VC")
                    return
            play_audio(vc, RADIO_FILE)

    await bot.process_commands(message)

@bot.command()
async def play(ctx, *, search):
    vc = ctx.voice_client
    if not vc:
        if ctx.author.voice:
            try:
                vc = await ctx.author.voice.channel.connect(timeout=10.0)
            except asyncio.TimeoutError:
                await ctx.send("❌ Timeout connecting to VC")
                return
        else:
            await ctx.send("⚠️ Join a VC first.")
            return

    if vc.is_playing():
        vc.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'song.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=True)
            file_path = ydl.prepare_filename(info)
        play_audio(vc, file_path)
    except Exception as e:
        print(f"[YT ERROR] {e}")
        await ctx.send("❌ Failed to play the YouTube video.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()

@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        play_audio(ctx.voice_client, RADIO_FILE)

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

keep_alive()
bot.run(TOKEN)
