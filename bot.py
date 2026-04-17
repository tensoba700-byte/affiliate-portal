import os
import json
import sys
import asyncio
import discord
from groq import AsyncGroq
from dotenv import load_dotenv
from mcp_client import MCPClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from auto_generator.main import run_auto_trending_pipeline

# .env ファイルの読み込み
load_dotenv()

# Node.js のパスを環境変数に追加 (npx が node を見つけられるようにするため)
os.environ["PATH"] = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin:" + os.environ.get("PATH", "")

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_CHANNEL_ID = os.getenv('TARGET_CHANNEL_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not GROQ_API_KEY:
    print("エラー: GROQ_API_KEY が .env に設定されていません。")
    exit(1)

groq_client = AsyncGroq(api_key=GROQ_API_KEY)
PYTHON_PATH = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"

# --- MCP 設定 ---
ALLOWED_DIR = "/Users/tsukika/Desktop/affiliate-portal"
NPX_PATH = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin/npx"
mcp_client = MCPClient(NPX_PATH, ["-y", "@modelcontextprotocol/server-filesystem", ALLOWED_DIR])
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
    await mcp_client.start()
    
    # 🗓 スケジューラの起動（トレンド自動生成パイプライン: 毎週月曜10時）
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(asyncio.to_thread(run_auto_trending_pipeline)), 'cron', day_of_week='mon', hour=10)
    scheduler.start()
    print("🗓 自動生成スケジューラが起動しました。")
    
    # MCPサーバーからツール一覧を同期
    tools_response = await mcp_client.list_tools()
    mcp_tools_list = tools_response.get("tools", [])
    
    # MCPのJSON Schema形式をOpenAI/Groq互換のfunction formatへ自動マッピング
    for t in mcp_tools_list:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": t['name'],
                "description": t.get('description', ''),
                "parameters": t.get('inputSchema', {})
            }
        })
        
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
    print('Botはメッセージ待機中です...')

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    # トレンド自動収集マニュアル実行
    if message.content.strip() in ["!generate", "記事生成して"]:
        await message.reply("⏳ トレンド自動収集・記事生成パイプラインを手動スタートしました！バックグラウンドで処理を行います。ターミナルのログをご確認ください。")
        asyncio.create_task(asyncio.to_thread(run_auto_trending_pipeline))
        return

    # 【おこげ役割】企画・Notion書き込み
    if message.content.strip() in ["!企画", "!plan"]:
        await message.reply("📋 記事の企画を開始し、Notionに商品情報を書き込みます...")
        cmd = f"{PYTHON_PATH} scripts/test_okoge_sync.py"
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=ALLOWED_DIR)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            await message.reply(f"✅ Notionへの書き込みが完了しました！\n```\n{stdout.decode()[-500:]}\n```")
        else:
            await message.reply(f"❌ 企画実行エラー:\n```\n{stderr.decode()[-500:]}\n```")
        return

    # 【公開フロー】記事生成・GitHubプッシュ
    if message.content.strip() in ["!公開", "!publish"]:
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
    # セッションが存在しなければ初期化
    if channel_id not in chat_histories:
        chat_histories[channel_id] = [
            {"role": "system", "content": f"You are a highly capable assistant (Okoge President) connected to a local filesystem via MCP. You operate articles for 'Mikkestyle'.\n"
                                         f"Workflow:\n"
                                         f"1. Planning (!plan): Plan article & sync products to Notion without URLs using 'scripts/test_okoge_sync.py'.\n"
                                         f"2. Processing: Qclaw (Tate) fills URLs/prices in Notion.\n"
                                         f"3. Publishing (!publish): Fetch from Notion, generate MD with images/prices, and push to GitHub using 'scripts/publish_article.py'.\n"
                                         f"Environment: Use '{PYTHON_PATH}' for python scripts. Allowed dir: '{ALLOWED_DIR}'."}
        ]
        
    history = chat_histories[channel_id]
    history.append({"role": "user", "content": message.content})
    
    # 履歴をローリングウィンドウで制限する
    if len(history) > MAX_HISTORY + 1:
        # systemプロンプトだけ先頭に残し、他をスライシング
        history = [history[0]] + history[-(MAX_HISTORY):]
        chat_histories[channel_id] = history

    try:
        async with message.channel.typing():
            # Groqによる推論ループ（ツール呼び出しが続く限りループ）
            while True:
                response = await groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=history,
                    tools=groq_tools if groq_tools else None,
                    tool_choice="auto" if groq_tools else "none",
                    max_tokens=1024
                )
                
                response_message = response.choices[0].message
                
                # model_dumpを使用して、AIメッセージを辞書化して履歴に反映
                history.append(response_message.model_dump(exclude_unset=True))
                
                # ツール呼び出し判定
                if response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        target_tool = tool_call.function.name
                        try:
                            target_args = json.loads(tool_call.function.arguments)
                            if not isinstance(target_args, dict):
                                target_args = {}
                        except Exception:
                            target_args = {}
                            
                        print(f"MCPツール実行要求: {target_tool} / Args: {target_args}")
                        
                        try:
                            if target_tool == "run_command":
                                cmd = target_args.get("command", "")
                                print(f"ローカルコマンド実行: {cmd}")
                                try:
                                    process = await asyncio.create_subprocess_shell(
                                        cmd,
                                        stdout=asyncio.subprocess.PIPE,
                                        stderr=asyncio.subprocess.PIPE,
                                        cwd=ALLOWED_DIR
                                    )
                                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
                                    out_str = stdout.decode('utf-8', errors='replace')
                                    err_str = stderr.decode('utf-8', errors='replace')
                                    full_output = f"Exit code: {process.returncode}\n"
                                    if out_str: full_output += f"STDOUT:\n{out_str}\n"
                                    if err_str: full_output += f"STDERR:\n{err_str}\n"
                                    
                                    # Limit strictly to 2000 chars to avoid API limit issues
                                    if len(full_output) > 2000:
                                        full_output = "...[truncated]...\n" + full_output[-1900:]
                                        
                                    function_response = "Command executed.\n" + full_output
                                    if not out_str and not err_str:
                                        function_response = f"Command executed with exit code {process.returncode} (No output)"
                                except asyncio.TimeoutError:
                                    process.kill()
                                    function_response = "Command execution timed out after 30 seconds."
                                except Exception as e:
                                    function_response = f"Command execution failed: {e}"
                            else:
                                # 実際にMCPでファイルシステム処理
                                mcp_result = await mcp_client.call_tool(target_tool, target_args)
                                
                                function_response = ""
                                if isinstance(mcp_result, dict) and "content" in mcp_result:
                                    text_results = [c.get("text", "") for c in mcp_result.get("content", []) if c.get("type") == "text"]
                                    function_response = "\n".join(text_results)
                                else:
                                    function_response = str(mcp_result)
                        except Exception as e:
                            print(f"ツール側実行エラー: {e}")
                            function_response = str(e)
                            
                        # 実行結果をhistoryに追加 (role: tool)
                        history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": target_tool,
                            "content": function_response
                        })
                    
                    # 最新のhistoryを使って次のループで結果をGroqに再度送信
                    continue
                else:
                    # ツール不使用、またはツール利用後の最終回答が生成されればループ終了
                    break
                    
            final_text = response_message.content or ""
            if final_text:
                if len(final_text) > 2000:
                    await message.reply(final_text[:1996] + "...")
                else:
                    await message.reply(final_text)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"エラーが発生しました: {e}")
        await message.reply("申し訳ありません、処理中にエラーが発生しました。時間を置いて再度お試しください。")

if __name__ == "__main__":
    if not DISCORD_TOKEN or not TARGET_CHANNEL_ID:
         print("エラー: DISCORD_TOKEN または TARGET_CHANNEL_ID が .env に設定されていません。")
         exit(1)
         
    client.run(DISCORD_TOKEN)
