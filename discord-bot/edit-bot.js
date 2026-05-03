// discord-bot/edit-bot.js
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
const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

async function readGitHubFile(path) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}?ref=${BRANCH}`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) throw new Error(`ファイル読み込みエラー: ${res.status}`);
  const data = await res.json();
  return {
    content: Buffer.from(data.content, 'base64').toString('utf-8'),
    sha: data.sha,
  };
}

async function updateGitHubFile(path, newContent, sha) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`;
  const body = {
    message: `🤖 編集実行くん: ${path} を修正`,
    content: Buffer.from(newContent, 'utf-8').toString('base64'),
    branch: BRANCH,
    sha: sha,
  };
  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`GitHub APIエラー: ${res.status}`);
  return await res.json();
}

client.once('ready', () => console.log(`✅ ${client.user.tag} 起動完了`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  if (message.content.startsWith('!fix')) {
    const args = message.content.slice(4).trim().split(' ');
    const filePath = args[0];
    const instruction = args.slice(1).join(' ');

    if (!filePath || !instruction) {
      return message.reply('使い方: `!fix src/content/articles/記事名.md 修正内容`');
    }

    try {
      const { content: current, sha } = await readGitHubFile(filePath);
      const prompt = `以下の記事ファイルを、与えられた指示に従って修正し、修正後の全文のみを返してください。説明は不要です。\n\n【指示】\n${instruction}\n\n【現在の記事内容】\n${current}`;
      const result = await model.generateContent(prompt);
      const newContent = result.response.text().trim();

      if (!newContent || newContent === current) {
        return message.reply('修正内容が同じか、生成に失敗したみたいや…');
      }

      await updateGitHubFile(filePath, newContent, sha);
      message.reply(`✅ \`${filePath}\` を修正したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('編集実行くん稼働中');
}).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));

client.login(process.env.DISCORD_TOKEN);
