const http = require('http');const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

client.once('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  if (!message.content.startsWith('!seo')) return;

  const prompt = message.content.slice(4).trim();
  if (!prompt) return message.reply('なにを修正すればいい？');

  try {
    const result = await model.generateContent(prompt);
    const reply = result.response.text();
    message.reply(reply);
  } catch (err) {
    console.error(err);
    message.reply('エラーが発生したよ…');
  }
});
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
});
server.listen(process.env.PORT || 3000, () => {
  console.log('HTTP server is listening');
});
client.login(process.env.DISCORD_TOKEN);
