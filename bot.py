import os
import json
import sys
import asyncio
import discord
from groq import AsyncGroq
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Update path to include the root for SCRIPTS/API calls if needed
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot"

# .env ファイルの読み込み (.env.local を優先)
if os.path.exists(os.path.join(ROOT_DIR, '.env.local')):
    load_dotenv(os.path.join(ROOT_DIR, '.env.local'))
load_dotenv(os.path.join(ROOT_DIR, '.env'))
# Also load scratch env for keys that might be missing in root
load_dotenv(os.path.join(SCRATCH_DIR, '.env'))

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = os.getenv('TARGET_CHANNEL_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
PYTHON_PATH = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"

if not GROQ_API_KEY:
    print("エラー: GROQ_API_KEY が設定されていません。")
    exit(1)

groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# --- MCP 設定 ---
ALLOWED_DIR = ROOT_DIR
# Import MCPClient from the same directory or scratch (keeping logic for now)
sys.path.append(SCRATCH_DIR)
from mcp_client import MCPClient

mcp_client = MCPClient("npx", ["-y", "@modelcontextprotocol/server-filesystem", ALLOWED_DIR])
groq_tools = []

chat_histories = {}
MAX_HISTORY = 20

# Discord BotのIntent
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    global groq_tools
    print("MCPファイルシステムを起動中...")
    try:
        await mcp_client.start()
        # MCPサーバーからツール一覧を同期
        tools_response = await mcp_client.list_tools()
        mcp_tools_list = tools_response.get("tools", [])
        for t in mcp_tools_list:
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": t['name'],
                    "description": t.get('description', ''),
                    "parameters": t.get('inputSchema', {})
                }
            })
    except Exception as e:
        print(f"MCP Start Error: {e}")
    
    # 🗓 スケジューラは必要に応じて設定
    
    groq_tools.append({
        "type": "function",
        "function": {
            "name": "run_command",
            "description": f"Run a shell command on the host Mac inside the {ALLOWED_DIR} directory. Max execution time is 30 seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    })
        
    print(f'ログインしました: {client.user}')
    print(f'監視中のチャンネルID: {TARGET_CHANNEL_ID}')
    print('Botは「おこげ社長」として待機中です...')

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    msg_content = message.content.strip()

    # 1. 「記事書いて」or「!企画」-> 企画・Notion書き込み
    if msg_content in ["記事書いて", "!企画", "!plan"]:
        await message.reply("📋 記事の企画を開始し、Notionに商品情報を書き込みます...")
        cmd = f"{PYTHON_PATH} scripts/test_okoge_sync.py"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=ALLOWED_DIR)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            await message.reply(f"✅ Notionへの書き込みが完了しました！\n```\n{stdout.decode()[-500:]}\n```")
        else:
            await message.reply(f"❌ 企画実行エラー:\n```\n{stderr.decode()[-500:]}\n```")
        return

    # 2. 「公開して」or「!公開」-> 記事生成・GitHubプッシュ
    if msg_content in ["公開して", "!公開", "!publish"]:
        await message.reply("🚀 Notionからデータを取得し、記事を生成してGitHubにプッシュします...")
        cmd = f"{PYTHON_PATH} scripts/publish_article.py"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=ALLOWED_DIR)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            await message.reply(f"✅ 記事の公開（GitHubプッシュ）が完了しました！\n```\n{stdout.decode()[-500:]}\n```")
        else:
            await message.reply(f"❌ 公開実行エラー:\n```\n{stderr.decode()[-500:]}\n```")
        return

    if str(message.channel.id) != TARGET_CHANNEL_ID:
        return

    channel_id = message.channel.id
    if channel_id not in chat_histories:
        chat_histories[channel_id] = [
            {"role": "system", "content": f"You are the 'Okoge President' (おこげ社長), an AI automation agent for 'Mikkestyle'.\n"
                                         f"Capabilities:\n"
                                         f"- Planning: Use `scripts/test_okoge_sync.py` for planning.\n"
                                         f"- Publishing: Use `scripts/publish_article.py` for publishing.\n"
                                         f"- Fixing (修正して): Research files, modify code using MCP, and run `git push` to deploy.\n"
                                         f"- Checking (確認して): Explore the directory and report site status.\n"
                                         f"Environment: Use '{PYTHON_PATH}' for python. Absolute path: '{ALLOWED_DIR}'."}
        ]
        
    history = chat_histories[channel_id]
    history.append({"role": "user", "content": message.content})
    
    if len(history) > MAX_HISTORY + 1:
        history = [history[0]] + history[-(MAX_HISTORY):]
        chat_histories[channel_id] = history

    try:
        async with message.channel.typing():
            while True:
                response = await groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=history,
                    tools=groq_tools if groq_tools else None,
                    tool_choice="auto" if groq_tools else "none",
                    max_tokens=1024
                )
                
                response_message = response.choices[0].message
                history.append(response_message.model_dump(exclude_unset=True))
                
                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        target_tool = tool_call.function.name
                        try:
                            target_args = json.loads(tool_call.function.arguments)
                        except Exception:
                            target_args = {}
                            
                        if target_tool == "run_command":
                            cmd = target_args.get("command", "")
                            process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=ALLOWED_DIR)
                            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                            function_response = f"STDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
                        else:
                            mcp_result = await mcp_client.call_tool(target_tool, target_args)
                            function_response = str(mcp_result)
                            
                        history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": target_tool,
                            "content": function_response
                        })
                    continue
                else:
                    break
                    
            final_text = response_message.content or ""
            if final_text:
                await message.reply(final_text[:2000])

    except Exception as e:
        print(f"Error: {e}")
        await message.reply("エラーが発生しました。")

if __name__ == "__main__":
    client.run(DISCORD_TOKEN)