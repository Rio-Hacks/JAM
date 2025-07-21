import os
import random
from pathlib import Path
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1331178993390718999
MUSIC_VC_ID = 1354365519641313480
SONGS_FOLDER = Path("songs")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_random_song():
    songs = list(SONGS_FOLDER.glob("*.mp3"))
    return random.choice(songs) if songs else None

async def play_random(vc):
    song = get_random_song()
    if song:
        source = FFmpegPCMAudio(str(song))
        vc.play(source, after=lambda e: bot.loop.create_task(play_random(vc)))
        print(f"🎵 Now playing: {song.name}")
    else:
        print("⚠️ No MP3 songs found in songs folder.")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    guild = bot.get_guild(GUILD_ID)
    if guild:
        channel = guild.get_channel(MUSIC_VC_ID)
        if channel:
            if not discord.utils.get(bot.voice_clients, guild=guild):
                try:
                    vc = await channel.connect()
                    await play_random(vc)
                except discord.ClientException:
                    print("⚠️ Already connected or error on connect.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if after.channel and after.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if not vc or not vc.is_connected():
            try:
                vc = await after.channel.connect()
                await play_random(vc)
            except discord.ClientException:
                print("⚠️ Error joining VC.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Music paused.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Music resumed.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipping to next...")

@bot.command(name='exit')
async def exit_command(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot left the VC.")

keep_alive()
bot.run(TOKEN)
