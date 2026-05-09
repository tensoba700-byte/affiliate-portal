// discord-bot/product-bot.js（GitHubルール完全準拠版）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const NOTION_API_KEY = process.env.NOTION_API_KEY;
const NOTION_DATABASE_ID = process.env.NOTION_DATABASE_ID;

// GitHubの生URLから最新ルールを読み込む
const RULES_URL = 'https://raw.githubusercontent.com/tensoba700-byte/affiliate-portal/main/scripts/product_selection_prompt.txt';

let model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

// ルールを動的に取得する関数
async function fetchRules() {
  try {
    const res = await fetch(RULES_URL);
    if (res.ok) return await res.text();
    console.warn('ルール取得失敗、デフォルトで続行');
    return null;
  } catch (e) {
    console.warn('ルール取得エラー: ' + e.message);
    return null;
  }
}

// Notion登録関数
async function addToNotion(product) {
  const props = {};
  if (product.name) props['商品名'] = { title: [{ text: { content: product.name } }] };
  if (product.model) props['製品番号'] = { rich_text: [{ text: { content: product.model } }] };
  if (product.articleTitle) props['記事タイトル'] = { rich_text: [{ text: { content: product.articleTitle } }] };
  if (product.searchName) props['検索商品名'] = { rich_text: [{ text: { content: product.searchName || product.name } }] };
  if (product.reason) props['選定理由'] = { rich_text: [{ text: { content: product.reason } }] };
  if (product.category) props['カテゴリ'] = { select: { name: product.category } };
  if (product.publishTime) props['公開時間'] = { select: { name: product.publishTime } };
  props['ステータス 1'] = { select: { name: '未処理' } };

  const res = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + NOTION_API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
    body: JSON.stringify({ parent: { database_id: NOTION_DATABASE_ID }, properties: props }),
  });
  return res.ok;
}

client.once('ready', () => console.log('✅ 商品選定じみにー 起動完了（GitHubルール完全準拠版）'));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  if (message.content.startsWith('!select-products')) {
    message.reply('📋 GitHubから最新ルールを読み込み、商品を選定中やで…');

    try {
      const rules = await fetchRules();
      if (!rules) return message.reply('ルールの取得に失敗したわ…GitHubのファイルを確認してくれ。');

      const prompt = rules + '\n\n上記のルールに厳密に従い、6つの商品をJSON形式で出力してください。';
      const result = await model.generateContent(prompt);
      const responseText = result.response.text();
      
      const jsonMatch = responseText.match(/\[[\s\S]*\]/);
      if (!jsonMatch) return message.reply('JSONの抽出に失敗したわ…');

      const products = JSON.parse(jsonMatch[0]);
      let successCount = 0;
      for (const product of products) {
        const ok = await addToNotion(product);
        if (ok) successCount++;
      }
      message.reply('✅ ' + successCount + '/' + products.length + '件の商品をNotionに登録したで！');
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
