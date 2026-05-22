import os
os.environ["PATH"] = "/Users/tsukika/.nvm/versions/node/v24.14.1/bin:" + os.environ.get("PATH", "")
import asyncio
import threading
import time
import re
import schedule
import discord
import google.generativeai as genai
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(ROOT_DIR, '.env.local'))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

TARO_DISCORD_TOKEN = os.getenv('TARO_DISCORD_TOKEN')
TARO_ALLOWED_USER_ID = int(os.getenv('TARO_ALLOWED_USER_ID', '0'))
TARO_DM_CHANNEL_ID = 1499225821477343284
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TARO_DISCORD_TOKEN:
    print("エラー: TARO_DISCORD_TOKEN が設定されていません。")
    exit(1)

if not TARO_ALLOWED_USER_ID:
    print("エラー: TARO_ALLOWED_USER_ID が設定されていません。")
    exit(1)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("エラー: GEMINI_API_KEY が設定されていません。")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
_loop = None


# --- 24時間眠らないためのダミーHTTPサーバー ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("アンチグラビティ Bot は正常に稼働しています！".encode('utf-8'))

    def log_message(self, format, *args):
        # ログ肥大化を防ぐためにリクエストログは出力しない
        return


def _run_dummy_server():
    """Render.comなどのポート監視に答えるための超軽量サーバー"""
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    print(f"ダミーHTTPサーバー起動完了: ポート {port}")
    server.serve_forever()


def _run_self_ping():
    """14分に1回自分自身にHTTPアクセスを送信して、Renderの自動スリープを防ぐ"""
    # 起動してから3分間は待機する
    time.sleep(180)
    
    external_url = os.getenv("RENDER_EXTERNAL_URL")
    if not external_url:
        print("[Ping] RENDER_EXTERNAL_URL が未設定のため、セルフPingをスキップします。")
        return
        
    print(f"[Ping] 自動スリープ防止セルフPingを開始します。対象: {external_url}")
    while True:
        try:
            time.sleep(840)  # 14分 (840秒) 待機
            req = urllib.request.Request(external_url, headers={'User-Agent': 'AntiGravitySelfPing'})
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"[Ping] セルフアクセス成功 (ステータス: {response.status})")
        except Exception as e:
            print(f"[Ping] セルフアクセスエラー: {e}")


async def run_gemini_chat(prompt: str) -> str:
    """Gemini APIを使用して会話応答を生成する (無料)"""
    try:
        # gemini-2.5-flash を使用 (高速・高性能かつ無料枠対象)
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        system_instruction = (
            "あなたは太郎さんのアフィリエイト・ブログ支援を行う自律型AIアシスタント『アンチグラビティ』です。\n"
            "優しく、丁寧で、太郎さんをサポートすることに情熱を注いでいます。\n"
            "太郎さんからの質問や雑談、ブログに関する相談に親切に答えてください。\n"
            "もしブログの競合URL（httpまたはhttpsから始まるリンク）が送られてきた場合は、自動的に記事の執筆プロセスを開始します。"
        )
        
        response = await asyncio.to_thread(
            model.generate_content,
            contents=[system_instruction, prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Geminiでの応答生成中にエラーが発生しました: {e}"


async def run_article_generation(url: str, working_dir: str = ROOT_DIR, timeout: int = 900) -> str:
    """scripts/generate_from_competitor.py をサブプロセスで実行して記事を生成する"""
    try:
        # 実行パスの自動特定 (Render上とローカル環境両対応)
        # Render等ではシステムグローバルの python3、ローカルでは仮想環境の python3 を優先する
        python_bin = "python3"
        local_venv = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"
        if os.path.exists(local_venv):
            python_bin = local_venv
            
        script_path = os.path.join(working_dir, 'scripts', 'generate_from_competitor.py')
        
        proc = await asyncio.create_subprocess_exec(
            python_bin,
            script_path,
            url,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode('utf-8', errors='replace').strip()
        error = stderr.decode('utf-8', errors='replace').strip()

        print(f"[Bot] 記事生成プロセス出力:\n{output}")
        if error:
            print(f"[Bot] 記事生成プロセスエラー:\n{error}")

        if proc.returncode != 0:
            return f"❌ 記事生成プロセスが失敗しました (コード: {proc.returncode})。\nエラー内容:\n```\n{error[:1500]}\n```"

        success_match = re.search(r'🎉 成功！新しい記事が作成されました：\n(/articles/\S+)', output)
        if success_match:
            slug_url = success_match.group(1)
            
            # GITHUB_TOKEN が設定されている場合、リモート環境とみなし自動的に GitHub に Push する
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                try:
                    print("[Bot] リモート環境を検知しました。GitHubへのプッシュを開始します...")
                    
                    # Gitの初期ユーザー設定 (コミットエラー防止)
                    await (await asyncio.create_subprocess_exec('git', 'config', 'user.name', 'Render Bot', cwd=working_dir)).wait()
                    await (await asyncio.create_subprocess_exec('git', 'config', 'user.email', 'bot@render.com', cwd=working_dir)).wait()
                    
                    # 1. Add
                    await (await asyncio.create_subprocess_exec('git', 'add', '.', cwd=working_dir)).wait()
                    
                    # 2. Commit
                    commit_proc = await asyncio.create_subprocess_exec(
                        'git', 'commit', '-m', f'chore: auto-publish article from Discord Bot [{slug_url}] [skip ci]',
                        cwd=working_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await commit_proc.communicate()
                    
                    # 3. Push (トークンを埋め込んだHTTPS URLで認証をパスする)
                    push_url = f"https://{github_token}@github.com/tensoba700-byte/affiliate-portal.git"
                    push_proc = await asyncio.create_subprocess_exec(
                        'git', 'push', push_url, 'main',
                        cwd=working_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    push_stdout, push_stderr = await push_proc.communicate()
                    
                    if push_proc.returncode != 0:
                        print(f"[Bot] Push失敗: {push_stderr.decode('utf-8', errors='replace')}")
                        return f"🎉 **記事生成自体は成功しました！** (パス: `{slug_url}`)\n⚠️ しかし、GitHubへの自動同期プッシュに失敗しました。"
                        
                    print("[Bot] GitHubへの自動同期プッシュが正常に完了しました！")
                    return f"🎉 **アフィリエイト記事の自動生成が完了しました！**\n\n生成された記事パス: `{slug_url}`\n記事ファイルとアイキャッチ画像が作成され、GitHubへの自動同期プッシュまで完了しました！\n数分以内に本番サイトに反映されます。"
                
                except Exception as git_err:
                    print(f"[Bot] Git同期エラー: {git_err}")
                    return f"🎉 **記事生成自体は成功しました！** (パス: `{slug_url}`)\n⚠️ しかし、GitHubとの同期操作中にエラーが発生しました: {git_err}"
            
            return f"🎉 **アフィリエイト記事の自動生成が完了しました！**\n\n生成された記事パス: `{slug_url}`\nリポジトリ内にMarkdownファイルとアイキャッチ画像が正常に保存されました！"
        
        return f"🎉 記事生成が完了した可能性がありますが、結果の確認に失敗しました。\n標準出力:\n```\n{output[-1000:]}\n```"

    except asyncio.TimeoutError:
        return f"❌ タイムアウト: 記事生成処理に {timeout // 60} 分以上かかりました。"
    except Exception as e:
        return f"❌ 処理実行中に予期しないエラーが発生しました: {e}"


def split_message(text: str, limit: int = 1900) -> list[str]:
    """Discordの2000文字制限に合わせてメッセージを分割する"""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def run_scheduled_publishing():
    """毎日22:00にNotionの未処理商品を処理し、完了した記事を自動で1つパブリッシュする"""
    # ※リモート（Render等）では、本家の GitHub Actions が自動で朝夜パブリッシュしてくれるため、
    # 重複起動による同時書き込みコンフリクトを防ぐため、GITHUB_TOKEN がある場合はスケジュール実行をスキップします。
    if os.getenv("GITHUB_TOKEN"):
        print("[スケジュール] リモート環境のため、自動パブリッシュは GitHub Actions 側に一任し、本タスクはスキップします。")
        return

    print("[スケジュール] Notion의 未処理商品の情報取得を開始します...")
    
    python_bin = "python3"
    local_venv = "/Users/tsukika/.gemini/antigravity/scratch/discord-bot/venv/bin/python3"
    if os.path.exists(local_venv):
        python_bin = local_venv
    
    # 1. 未処理商品のURLや画像を自動取得
    try:
        proc1 = await asyncio.create_subprocess_exec(
            python_bin,
            os.path.join(ROOT_DIR, 'scripts', 'process_unprocessed.py'),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT_DIR
        )
        stdout1, stderr1 = await proc1.communicate()
        print(f"[スケジュール] process_unprocessed出力:\n{stdout1.decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[スケジュール] process_unprocessedエラー: {e}")
        
    # 2. 完了した記事をパブリッシュ
    print("[スケジュール] 完了した記事の自動生成と投稿を開始します...")
    try:
        proc2 = await asyncio.create_subprocess_exec(
            python_bin,
            os.path.join(ROOT_DIR, 'scripts', 'auto_publish_batch.py'),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT_DIR
        )
        stdout2, stderr2 = await proc2.communicate()
        output2 = stdout2.decode('utf-8', errors='replace')
        print(f"[スケジュール] auto_publish_batch出力:\n{output2}")
        
        # 太郎さんへのDMまたは通知チャンネルへの報告
        channel = client.get_channel(TARO_DM_CHANNEL_ID)
        if channel is None:
            try:
                channel = await client.fetch_channel(TARO_DM_CHANNEL_ID)
            except Exception:
                channel = None
                
        if channel:
            if "Article generated successfully" in output2:
                # 成功
                slug_match = re.search(r'Article generated successfully: (\S+)', output2)
                slug = slug_match.group(1) if slug_match else "不明"
                await channel.send(f"📅 **【毎日22:00 自動公開スケジュール】**\nNotion から完了した記事を自動生成して公開しました！\nURL slug: `/articles/{slug}`")
            elif "Nothing to publish" in output2 or "No articles found" in output2:
                # 投稿なし
                await channel.send("📅 **【毎日22:00 自動公開スケジュール】**\nNotion に公開待ちの「完了」ステータスの記事がありませんでした。")
            else:
                # 失敗などのエラー
                await channel.send(f"📅 **【毎日22:00 自動公開スケジュール】**\n記事の自動公開処理が実行されましたが、公開待ちの記事がないかエラーが発生した可能性があります。\nログ:\n```\n{output2[-1000:]}\n```")
    except Exception as e:
        print(f"[スケジュール] auto_publish_batchエラー: {e}")


def _scheduled_job():
    """scheduleライブラリから呼び出されるエントリポイント（同期）"""
    if _loop is None:
        print("エラー: イベントループが初期化されていません。")
        return
    asyncio.run_coroutine_threadsafe(run_scheduled_publishing(), _loop)


def _run_scheduler():
    """スケジューラーをバックグラウンドスレッドで実行する"""
    schedule.every().day.at("22:00").do(_scheduled_job)
    print("スケジューラー起動: 毎日 22:00 にNotionの処理と自動記事作成を自動実行します。")
    while True:
        schedule.run_pending()
        time.sleep(30)


@client.event
async def on_ready():
    global _loop
    _loop = asyncio.get_event_loop()
    print(f"たろさん専用Bot起動: {client.user} (ID: {client.user.id})")
    print(f"許可ユーザーID: {TARO_ALLOWED_USER_ID}")

    # ローカル環境の場合のみ、22:00 のローカルスケジューラーを回す
    # (Renderリモート上では GitHub Actions があるためスキップ)
    if not os.getenv("GITHUB_TOKEN"):
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
        # URLが含まれているか判定
        url_match = re.search(r'https?://[^\s]+', prompt)
        if url_match:
            url = url_match.group(0)
            await message.reply(f"🔍 競合URLを検出しました：<{url}>\nGeminiによる自動執筆とリサーチ（アフィリエイトURLと画像自動検索）を開始します。しばらくお待ちください...")
            result = await run_article_generation(url)
        else:
            # 通常のおしゃべりは Gemini API で実行 (完全無料)
            result = await run_gemini_chat(prompt)

    await message.remove_reaction('⏳', client.user)

    chunks = split_message(result)
    for i, chunk in enumerate(chunks):
        if i == 0:
            await message.reply(chunk)
        else:
            await message.channel.send(chunk)


if __name__ == "__main__":
    # Render.com等のポート監視に答えるための軽量HTTPサーバーを別スレッドで立ち上げる
    dummy_thread = threading.Thread(target=_run_dummy_server, daemon=True)
    dummy_thread.start()
    
    # 24時間自動スリープを防ぐセルフPingスレッドを立ち上げる
    ping_thread = threading.Thread(target=_run_self_ping, daemon=True)
    ping_thread.start()

    # Discord Bot を起動
    client.run(TARO_DISCORD_TOKEN)
