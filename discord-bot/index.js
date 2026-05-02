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

// Gemini APIの設定
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
// ✅ 修正：無料枠で使える正しいモデル名を指定
const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

// Botが起動した時のイベント
client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

// メッセージを受け取った時のイベント
client.on('messageCreate', async (message) => {
  // Bot自身のメッセージは無視
  if (message.author.bot) return;
  // 「!seo」で始まるメッセージだけ反応
  if (!message.content.startsWith('!seo')) return;

  // 指示を取り出す（「!seo」の後ろを取得）
  const prompt = message.content.slice(4).trim();
  if (!prompt) return message.reply('なにを修正すればいい？');

  try {
    // Geminiに質問を送信
    const result = await model.generateContent(prompt);
    const reply = result.response.text();
    // 結果を返信
    message.reply(reply);
  } catch (err) {
    console.error(err);
    // ✅ 修正：エラーの詳細を表示（問題の特定がラクになる）
    message.reply('エラーが発生したよ...: ' + (err.message || err));
  }
});

// Renderの無料プラン（Web Service）で動かすための簡易HTTPサーバー
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
});
server.listen(process.env.PORT || 3000, () => {
  console.log('HTTP server is listening');
});

// Discordへログイン
client.login(process.env.DISCORD_TOKEN);
