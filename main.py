import os
import discord
import random
from discord.ext import commands
from discord import FFmpegPCMAudio
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MUSIC_VC_ID = 1354365519641313480

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_random_song():
    folder = "songs"
    songs = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".mp3")]
    return random.choice(songs)

async def play_random(vc):
    song = get_random_song()
    source = FFmpegPCMAudio(song)
    vc.play(source, after=lambda e: bot.loop.create_task(play_random(vc)))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

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
            except Exception as e:
                print(f"⚠️ Voice join error: {e}")

    if before.channel and before.channel.id == MUSIC_VC_ID:
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        if vc and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()

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
        await ctx.send("⏭️ Skipped. Playing next...")

@bot.command(name='exit')
async def exit_command(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
keep_alive()
bot.run(TOKEN)
