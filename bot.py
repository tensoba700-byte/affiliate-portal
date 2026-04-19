import os
import json
import sys
import asyncio
import discord
import google.generativeai as genai
from dotenv import load_dotenv
from mcp_client import MCPClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Note: auto_generator.main might be in the project root, ensure PYTHONPATH is correct
# We assume the bot is run from a location where it can import its modules.
import copy

def clean_schema(schema):
    """Gemini API はスキーマ内の '$schema' や 'additionalProperties' などのフィールドを認めていないため再帰的に削除する"""
    if not isinstance(schema, dict):
        return schema
    
    # Gemini でサポートされている主要なフィールド
    ALLOWED_KEYS = {
        "type", "format", "description", "nullable", "enum", 
        "items", "properties", "required", "default"
    }
    
    # サポートされているキーのみを抽出
    new_schema = {k: v for k, v in schema.items() if k in ALLOWED_KEYS}
    
    # properties を再帰的にクリーンアップ
    if "properties" in new_schema:
        new_schema["properties"] = {
            k: clean_schema(v) for k, v in new_schema["properties"].items()
        }
    
    # items を再帰的にクリーンアップ
    if "items" in new_schema:
        new_schema["items"] = clean_schema(new_schema["items"])
        
    return new_schema

# .env.local と .env の読み込み
load_dotenv("/Users/tsukika/Desktop/affiliate-portal/.env.local")
load_dotenv("/Users/tsukika/.gemini/antigravity/scratch/discord-bot/.env")

# Node.js のパスを環境変数に追加
os.environ["PATH"] = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin:" + os.environ.get("PATH", "")

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = os.getenv('TARGET_CHANNEL_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("エラー: GEMINI_API_KEY が .env.local に設定されていません。")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
PYTHON_PATH = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"

# --- MCP 設定 ---
ALLOWED_DIR = "/Users/tsukika/Desktop/affiliate-portal"
NPX_PATH = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin/npx"
mcp_client = MCPClient(NPX_PATH, ["-y", "@modelcontextprotocol/server-filesystem", ALLOWED_DIR])

# 手動でツール定義を管理（Gemini用）
gemini_tools = []

chat_histories = {}
MAX_HISTORY = 15

# Discord BotのIntent
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    global gemini_tools
    print("MCPファイルシステムを起動中...")
    await mcp_client.start()
    
    # tools一覧取得とGemini形式への変換
    tools_response = await mcp_client.list_tools()
    mcp_tools = tools_response.get("tools", [])
    
    tools_defs = []
    for t in mcp_tools:
        tools_defs.append({
            "name": t['name'],
            "description": t.get('description', ''),
            "parameters": clean_schema(t.get('inputSchema', {}))
        })
    
    # run_command を追加
    tools_defs.append({
        "name": "run_command",
        "description": f"Run a shell command on the host Mac inside {ALLOWED_DIR}.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."}
            },
            "required": ["command"]
        }
    })
    
    gemini_tools = tools_defs
    print(f'ログインしました: {client.user}')
    print(f'Gemini 2.0 Flash 搭載完了。ボットは待機中です...')

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    # 特殊コマンド
    if message.content.strip() in ["!generate", "記事生成して"]:
        await message.reply("⏳ トレンド自動収集・記事生成パイプラインを開始！")
        # 直接実行せずシェル経由にすることで依存関係を隔離
        cmd = f"cd {ALLOWED_DIR} && {PYTHON_PATH} -m auto_generator.main"
        asyncio.create_task(asyncio.create_subprocess_shell(cmd))
        return

    if message.content.strip() in ["!公開", "!publish"]:
        await message.reply("🚀 記事生成 & GitHubプッシュを開始...")
        cmd = f"cd {ALLOWED_DIR} && {PYTHON_PATH} scripts/publish_article.py"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            await message.reply(f"✅ 公開完了!\n```\n{stdout.decode()[-500:]}\n```")
        else:
            await message.reply(f"❌ エラー:\n```\n{stderr.decode()[-500:]}\n```")
        return

    if str(message.channel.id) != TARGET_CHANNEL_ID:
        return

    channel_id = message.channel.id
    if channel_id not in chat_histories:
        chat_histories[channel_id] = []
        
    history = chat_histories[channel_id]
    history.append({"role": "user", "parts": [message.content]})
    
    if len(history) > MAX_HISTORY * 2:
        history = history[-MAX_HISTORY*2:]
        chat_histories[channel_id] = history

    try:
        async with message.channel.typing():
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                system_instruction=f"You are 'Okoge President' at Mikkestyle. Operate via MCP tools. Python: {PYTHON_PATH}. Dir: {ALLOWED_DIR}."
            )
            chat = model.start_chat(history=[h for h in history[:-1]])
            
            # 手動ツールループ
            current_content = message.content
            while True:
                response = chat.send_message(current_content, tools=gemini_tools if gemini_tools else None)
                
                # ツール呼び出し確認
                if response.candidates[0].content.parts and response.candidates[0].content.parts[0].function_call:
                    fc = response.candidates[0].content.parts[0].function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args)
                    
                    print(f"Geminiツール要求: {tool_name}")
                    
                    try:
                        if tool_name == "run_command":
                            cmd = tool_args.get("command", "")
                            process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=ALLOWED_DIR)
                            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
                            result_text = f"Exit: {process.returncode}\n{stdout.decode('utf-8', errors='replace')}\n{stderr.decode('utf-8', errors='replace')}"
                        else:
                            mcp_res = await mcp_client.call_tool(tool_name, tool_args)
                            result_text = "\n".join([c.get("text", "") for c in mcp_res.get("content", []) if c.get("type") == "text"])
                    except Exception as e:
                        result_text = f"Error: {e}"
                    
                    tool_response_part = genai.types.PartDict(function_response=genai.types.FunctionResponse(name=tool_name, response={'result': result_text}))
                    current_content = [tool_response_part]
                    continue
                else:
                    final_text = response.text
                    break
            
            chat_histories[channel_id] = chat.history
            if final_text:
                await message.reply(final_text[:2000])

    except Exception as e:
        print(f"エラー: {e}")
        await message.reply(f"エラーが発生しました: {str(e)[:200]}")

if __name__ == "__main__":
    if not DISCORD_TOKEN or not TARGET_CHANNEL_ID:
         print("エラー設定不足")
         exit(1)
    client.run(DISCORD_TOKEN)
