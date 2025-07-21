import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from keep_alive import keep_alive
import yt_dlp

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
current_radio = None

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if after.channel and after.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if not vc or not vc.is_connected():
            try:
                vc = await after.channel.connect()
                await play_radio(vc)
            except Exception as e:
                print(f"⚠️ Auto-join error: {e}")

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
                vc = await message.author.voice.channel.connect()
            await play_radio(vc)

    await bot.process_commands(message)

async def play_radio(vc):
    global current_radio
    if vc.is_playing():
        vc.stop()
    current_radio = FFmpegPCMAudio(RADIO_FILE)
    vc.play(current_radio)

@bot.command()
async def play(ctx, *, search: str = None):
    if not search:
        await ctx.send("❗ Usage: `!play <YouTube URL or search name>`")
        return

    vc = ctx.voice_client
    if not vc:
        if ctx.author.voice:
            vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❗ Join a VC first.")
            return

    if vc.is_playing():
        vc.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'song.%(ext)s',
        'cookiefile': 'cookies.txt'  # ✅ Use cookies for better YouTube access
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=True)
            file_path = ydl.prepare_filename(info)

        vc.play(FFmpegPCMAudio(file_path))
        await ctx.send(f"▶️ Now playing: **{info['title']}**")
    except Exception as e:
        print(f"❌ YouTube error: {e}")
        await ctx.send("❌ Failed to play. This video may be age-restricted or blocked.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")

@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped. Resuming aura.mp3")
        await play_radio(ctx.voice_client)

@bot.command(name="exit")
async def exit_command(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot left the VC")

keep_alive()
bot.run(TOKEN)
