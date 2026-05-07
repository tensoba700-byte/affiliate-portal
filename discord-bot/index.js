// discord-bot/index.js（FrontmatterのpublishDateソート対応版）
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

// GitHubファイル読み込み/更新/作成（日本語パス対応）
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

async function createGitHubFile(path, content) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath;
  const body = {
    message: '🤖 Bot: ' + path + ' を作成',
    content: Buffer.from(content, 'utf-8').toString('base64'),
    branch: BRANCH,
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

  // !audit-articles コマンド
  if (isAllowedChannel && message.content.startsWith('!audit-articles')) {
    const args = message.content.slice(15).trim().split(' ');
    const targetDir = args[0] || 'src/content/articles';
    message.reply('🔍 ' + targetDir + ' の記事をAI分析し、修正案ファイルを作成中やで…');

    try {
      const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + targetDir + '?ref=' + BRANCH;
      const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
      const files = await res.json();
      const mdFiles = files.filter(f => f.type === 'file' && f.name.endsWith('.md'));

      // ✅ FrontmatterのpublishDateでソートする
      for (const f of mdFiles) {
        try {
          const { content } = await readGitHubFile(targetDir + '/' + f.name);
          const dateMatch = content.match(/publishDate:\s*(.+)/);
          f.publishDate = dateMatch ? new Date(dateMatch[1]) : new Date(0);
        } catch(e) { f.publishDate = new Date(0); }
      }
      mdFiles.sort((a, b) => b.publishDate - a.publishDate);

      if (mdFiles.length === 0) return message.reply('📭 記事が見つからんかった。');

      const file = mdFiles[0];
      const filePath = targetDir + '/' + file.name;
      const { content } = await readGitHubFile(filePath);

      const fixPrompt = '以下の記事を、美容メディア「みっけ！」のルールに厳密に従って修正し、修正後の全文（Markdown形式）だけを返してや。\n現在の記事:\n' + content;
      const result = await model.generateContent(fixPrompt);
      const fixedContent = result.response.text();

      // 修正案ファイルを作成
      const fixFilePath = filePath.replace('.md', '-fix.md');
      await createGitHubFile(fixFilePath, fixedContent);

      // 編集実行くんに簡略指示を送信
      message.channel.send('@編集実行くん !apply-fix ' + filePath + ' ' + fixFilePath);
      message.reply('✅ 修正案ファイル `' + fixFilePath + '` を作成し、編集実行くんに修正指示を送ったで！');

    } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
  }
});

http.createServer(function(req, res) { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
