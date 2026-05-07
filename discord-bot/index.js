// discord-bot/index.js（記事直接修正版：分析後、修正案ファイルを作成せず直接上書き）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';
const ALLOWED_CHANNEL_ID = process.env.ALLOWED_CHANNEL_ID;
const ARTICLES_DIR = 'src/content/articles';

async function readGitHubFile(path) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath + '?ref=' + BRANCH;
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) throw new Error('ファイル読み込み失敗: ' + res.status);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

async function updateGitHubFile(path, newContent, sha) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath;
  const body = {
    message: '🤖 Bot: ' + path + ' を更新',
    content: Buffer.from(newContent, 'utf-8').toString('base64'),
    branch: BRANCH, sha,
  };
  const res = await fetch(url, {
    method: 'PUT', headers: { Authorization: 'token ' + GITHUB_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('GitHub APIエラー: ' + res.status);
  return await res.json();
}

let model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

client.once('ready', function() { console.log('✅ ' + client.user.tag + ' 起動完了'); });

client.on('messageCreate', async function(message) {
  if (message.author.bot) return;
  const isAllowedChannel = ALLOWED_CHANNEL_ID && message.channel.id === ALLOWED_CHANNEL_ID;

  // !audit-latest コマンド：最新記事を自動検出して分析・直接修正
  if (isAllowedChannel && message.content.startsWith('!audit-latest')) {
    message.reply('🔍 最新の記事を自動検出して分析・修正中やで…');

    try {
      // 1. 記事ディレクトリから全ファイルを取得
      const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + ARTICLES_DIR + '?ref=' + BRANCH;
      const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
      const files = await res.json();
      const mdFiles = files.filter(f => f.type === 'file' && f.name.endsWith('.md'));

      // 2. FrontmatterのpublishDateでソート
      for (const f of mdFiles) {
        try {
          const { content } = await readGitHubFile(ARTICLES_DIR + '/' + f.name);
          const dateMatch = content.match(/publishDate:\s*(.+)/);
          f.publishDate = dateMatch ? new Date(dateMatch[1]) : new Date(0);
        } catch(e) { f.publishDate = new Date(0); }
      }
      mdFiles.sort((a, b) => b.publishDate - a.publishDate);

      // 3. 最新の記事を直接修正
      const file = mdFiles[0];
      const filePath = ARTICLES_DIR + '/' + file.name;
      const { content, sha } = await readGitHubFile(filePath);

      message.reply('📝 最新記事「' + file.name + '」を分析＆直接修正中…');

      const fixPrompt = 'あなたは「みっけ！」の記事修正担当です。以下の記事を、GENERATION_RULES.md と title-quality.md に厳密に従って修正してください。\n\n【絶対ルール】\n- 商品数は必ず6個に固定。7個の場合は1つ削除する\n- 「👑 第N位」は使用禁止。「商品名」だけを並列で紹介する\n- [AMAZON_LINK_HERE] などのプレースホルダーは、必ず実際のURLに置き換える\n- ASINコードは一切記載しない\n- 各商品に「| 仕様 | 内容 |」形式のスペック表を必ず追加する\n- 冒頭に「本記事はアフィリエイト広告を利用しています」を必ず入れる\n- 禁止ワード（劇的、おすすめ〇選、ランキング、人気など）は絶対に使わない\n- 元の記事にない情報を勝手に創作しない。原文を尊重しつつ、フォーマットだけを修正する\n\n現在の記事:\n' + content;
      
      const result = await model.generateContent(fixPrompt);
      const fixedContent = result.response.text();

      // 4. GitHubの記事を直接上書き
      await updateGitHubFile(filePath, fixedContent, sha);
      message.reply('✅ 最新記事「' + file.name + '」の分析と自動修正が完了したで！');

    } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
  }
});

http.createServer(function(req, res) { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
