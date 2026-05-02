// discord-bot/index.js
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

// Discordクライアントの作成
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// Gemini APIの初期化
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// GitHub設定
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';

// ✅ 特定チャンネル（このチャンネルでは !seo なしで反応）
const ALLOWED_CHANNEL_ID = process.env.ALLOWED_CHANNEL_ID;

// 記事執筆ルールのURL（GENERATION_RULES.md）
const RULES_URL = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}/GENERATION_RULES.md`;

// ルールを取得する関数
async function fetchRules() {
  try {
    const res = await fetch(RULES_URL);
    return res.ok ? await res.text() : null;
  } catch {
    return null;
  }
}

// GitHubのファイルを読み込む関数
async function readGitHubFile(path) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}?ref=${BRANCH}`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) throw new Error(`ファイル読み込み失敗: ${res.status}`);
  const data = await res.json();
  return {
    content: Buffer.from(data.content, 'base64').toString('utf-8'),
    sha: data.sha,
  };
}

// GitHubのファイルを更新する関数
async function updateGitHubFile(path, newContent, sha) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`;
  const body = {
    message: `🤖 Bot: ${path} を更新`,
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

// モデル初期化
let model;
(async () => {
  const rules = await fetchRules();
  model = genAI.getGenerativeModel({
    model: 'gemini-2.5-flash',
    systemInstruction: rules
      ? `あなたは美容メディア「みっけ！」のSEO編集者です。以下の執筆ルールに厳密に従ってください:\n\n${rules}`
      : 'あなたは美容メディア「みっけ！」のSEO編集者です。',
  });
  console.log('✅ ルール読み込み完了');
})();

// Discordイベント
client.once('ready', () => console.log(`Logged in as ${client.user.tag}!`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  const isAllowedChannel = ALLOWED_CHANNEL_ID && message.channel.id === ALLOWED_CHANNEL_ID;

  // ===== 特定チャンネルでは !seo なしでも反応 =====
  if (isAllowedChannel && !message.content.startsWith('!update-code')) {
    const prompt = message.content.trim();
    if (!prompt) return;
    if (!model) return message.reply('まだ準備中やねん…ちょっと待ってな〜');

    try {
      const result = await model.generateContent(prompt);
      const reply = result.response.text();
      message.reply(reply);
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
    return;
  }

  // ===== !seo コマンド（他のチャンネル用） =====
  if (message.content.startsWith('!seo')) {
    const prompt = message.content.slice(4).trim();
    if (!prompt) return message.reply('なにを修正すればいい？');
    if (!model) return message.reply('まだ準備中やねん…ちょっと待ってな〜');

    try {
      const result = await model.generateContent(prompt);
      const reply = result.response.text();
      message.reply(reply);
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }

  // ===== !update-code コマンド =====
  else if (message.content.startsWith('!update-code')) {
    if (!GITHUB_TOKEN) return message.reply('GITHUB_TOKENが未設定やで。');

    const args = message.content.slice('!update-code'.length).trim().split(' ');
    const filePath = args[0];
    const instruction = args.slice(1).join(' ');

    if (!filePath || !instruction) {
      return message.reply('使い方: `!update-code ファイル名 修正内容`');
    }

    try {
      const { content: currentCode, sha } = await readGitHubFile(filePath);
      const prompt = `以下のファイルを、与えられた指示に従って修正し、修正後の全文のみを返してください。説明は不要です。\n\n【指示】\n${instruction}\n\n【現在のファイル内容】\n${currentCode}`;
      const result = await model.generateContent(prompt);
      const newCode = result.response.text().trim();

      if (!newCode || newCode === currentCode) {
        return message.reply('修正内容が同じか、生成に失敗したみたいや…');
      }

      await updateGitHubFile(filePath, newCode, sha);
      message.reply(`✅ \`${filePath}\` を更新したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});

// HTTPサーバー
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
}).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));

// Discordログイン
client.login(process.env.DISCORD_TOKEN);
