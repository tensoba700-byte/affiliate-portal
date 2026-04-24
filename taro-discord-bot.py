import os
import asyncio
import threading
import time
import schedule
import discord
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(ROOT_DIR, 'scripts', 'product_selection_prompt.txt')

load_dotenv(os.path.join(ROOT_DIR, '.env.local'))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

TARO_DISCORD_TOKEN = os.getenv('TARO_DISCORD_TOKEN')
TARO_ALLOWED_USER_ID = int(os.getenv('TARO_ALLOWED_USER_ID', '0'))
TARO_DM_CHANNEL_ID = 1496037309500620820

if not TARO_DISCORD_TOKEN:
    print("エラー: TARO_DISCORD_TOKEN が設定されていません。")
    exit(1)

if not TARO_ALLOWED_USER_ID:
    print("エラー: TARO_ALLOWED_USER_ID が設定されていません。")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
_loop: asyncio.AbstractEventLoop | None = None


async def run_claude_code(prompt: str, working_dir: str = ROOT_DIR, timeout: int = 600) -> str:
    """Claude Codeをサブプロセスで実行して結果を返す"""
    try:
        env = {k: v for k, v in os.environ.items() if k != 'ANTHROPIC_API_KEY'}
        proc = await asyncio.create_subprocess_exec(
            'claude',
            '--print',
            '--dangerously-skip-permissions',
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode('utf-8', errors='replace').strip()
        error = stderr.decode('utf-8', errors='replace').strip()

        if proc.returncode != 0 and error:
            return f"エラーが発生しました:\n```\n{error[:1800]}\n```"

        if not output:
            return "（出力なし）"

        return output

    except asyncio.TimeoutError:
        return f"タイムアウト: 処理に{timeout // 60}分以上かかりました。"
    except FileNotFoundError:
        return "エラー: `claude` コマンドが見つかりません。Claude Codeがインストールされているか確認してください。"
    except Exception as e:
        return f"予期しないエラー: {e}"


def split_message(text: str, limit: int = 1900) -> list[str]:
    """Discordの2000文字制限に合わせてメッセージを分割する"""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def run_scheduled_product_selection():
    """商品選定プロンプトを読み込み、Claude Codeを2回連続で実行する"""
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt = f.read()
    except FileNotFoundError:
        print(f"エラー: {PROMPT_FILE} が見つかりません。スケジュール実行をスキップします。")
        return

    channel = client.get_channel(TARO_DM_CHANNEL_ID)
    if channel is None:
        try:
            channel = await client.fetch_channel(TARO_DM_CHANNEL_ID)
        except Exception:
            channel = None

    print("[スケジュール] 1記事目の選定を開始します...")
    await run_claude_code(prompt, timeout=600)
    print("[スケジュール] 1記事目の選定が完了しました。")

    print("[スケジュール] 2記事目の選定を開始します...")
    await run_claude_code(prompt, timeout=600)
    print("[スケジュール] 2記事目の選定が完了しました。")


def _scheduled_job():
    """scheduleライブラリから呼び出されるエントリポイント（同期）"""
    if _loop is None:
        print("エラー: イベントループが初期化されていません。")
        return
    asyncio.run_coroutine_threadsafe(run_scheduled_product_selection(), _loop)


def _run_scheduler():
    """スケジューラーをバックグラウンドスレッドで実行する"""
    schedule.every().day.at("22:00").do(_scheduled_job)
    print("スケジューラー起動: 毎日 22:00 に商品選定を自動実行します。")
    while True:
        schedule.run_pending()
        time.sleep(30)


@client.event
async def on_ready():
    global _loop
    _loop = asyncio.get_event_loop()
    print(f"たろさん専用Bot起動: {client.user} (ID: {client.user.id})")
    print(f"許可ユーザーID: {TARO_ALLOWED_USER_ID}")

    scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    scheduler_thread.start()


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.author.id != TARO_ALLOWED_USER_ID:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = client.user in message.mentions

    if not is_dm and not is_mentioned:
        return

    prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
    if not prompt:
        await message.reply("メッセージを入力してください。")
        return

    await message.add_reaction('⏳')

    async with message.channel.typing():
        result = await run_claude_code(prompt)

    await message.remove_reaction('⏳', client.user)

    chunks = split_message(result)
    for i, chunk in enumerate(chunks):
        if i == 0:
            await message.reply(chunk)
        else:
            await message.channel.send(chunk)


client.run(TARO_DISCORD_TOKEN)
