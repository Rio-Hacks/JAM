import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
from keep_alive import keep_alive  # Optional: For Replit-like uptime pings

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MUSIC_VC_ID = 1354365519641313480
RADIO_FILE = "https://github.com/Rio-Hacks/JAM/raw/main/AURA%20%3D%20%E2%99%BE%EF%B8%8F%20_%20VIRAL%20AURA%20MUSIC%20PLAYLIST%202025%20%F0%9F%94%A5%201%20HOUR.mp3"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
                print(f"[AutoJoin Error] {e}")

    # Leave if music VC is empty (no humans)
    if before.channel and before.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if vc and len([m for m in vc.channel.members if not m.bot]) == 0:
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
    if vc.is_playing():
        vc.stop()
    vc.play(FFmpegPCMAudio(RADIO_FILE))

@bot.command()
async def play(ctx, *, search: str = None):
    if not search:
        await ctx.send("❗ Usage: `!play <YouTube link or song name>`")
        return

    vc = ctx.voice_client
    if not vc:
        if ctx.author.voice:
            vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.send("⚠️ You must join a voice channel first.")
            return

    if vc.is_playing():
        vc.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'song.%(ext)s',
        'cookiefile': 'cookies.txt'  # ✅ Loads cookies from your uploaded file
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if not search.startswith("http"):
                search = f"ytsearch:{search}"
            info = ydl.extract_info(search, download=True)
            file_path = ydl.prepare_filename(info)

        vc.play(FFmpegPCMAudio(file_path))
        await ctx.send(f"🎶 Now playing: **{info.get('title', 'Unknown')}**")

    except Exception as e:
        print(f"[YT Error] {e}")
        await ctx.send("❌ Failed to play from YouTube. Try a different song or check your cookies.txt.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await play_radio(ctx.voice_client)
        await ctx.send("⏭️ Skipped. Resuming radio.")

@bot.command(name='exit')
async def exit_command(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot has left the voice channel.")

# Optional: Replit-like keep-alive ping service (only if you're using UptimeRobot)
keep_alive()

bot.run(TOKEN)
