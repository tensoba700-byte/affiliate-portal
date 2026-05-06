// discord-bot/edit-bot.js（メンション自動反応版）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';

async function readGitHubFile(path) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${encodedPath}?ref=${BRANCH}`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) throw new Error(`読み込み失敗: ${res.status}`);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

async function replaceGitHubFile(path, newContent, sha) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${encodedPath}`;
  const body = {
    message: `🤖 編集実行くん: ${path} を更新`,
    content: Buffer.from(newContent, 'utf-8').toString('base64'),
    branch: BRANCH, sha,
  };
  const res = await fetch(url, {
    method: 'PUT', headers: { Authorization: `token ${GITHUB_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`GitHub APIエラー: ${res.status}`);
  return await res.json();
}

client.once('ready', () => {
  console.log(`✅ ${client.user.tag} 起動完了`);
});

client.on('messageCreate', async (message) => {
  // Bot自身のメッセージは無視
  if (message.author.bot) return;

  // 自分へのメンションがあるかチェック
  const isMentioned = message.mentions.has(client.user);

  // !replace コマンド
  if (message.content.startsWith('!replace') || isMentioned) {
    let args;
    if (message.content.startsWith('!replace')) {
      args = message.content.slice(8).trim().split(' ');
    } else {
      // メンションされた場合、メンション部分を除去して解析
      const cleanContent = message.content.replace(/<@!?\d+>/, '').trim();
      args = cleanContent.split(' ');
    }

    const filePath = args[0];
    const newContent = args.slice(1).join(' ');

    if (!filePath || !newContent) {
      return message.reply('使い方: `@編集実行くん ファイルパス 新しい内容` または `!replace ファイルパス 新しい内容`');
    }

    try {
      const { sha } = await readGitHubFile(filePath);
      await replaceGitHubFile(filePath, newContent, sha);
      message.reply(`✅ \`${filePath}\` を更新したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));
client.login(process.env.DISCORD_TOKEN);
