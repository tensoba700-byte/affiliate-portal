// discord-bot/product-bot.js（起動時に最新ルール読み込み + 会話機能）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const NOTION_API_KEY = process.env.NOTION_API_KEY;
const NOTION_DATABASE_ID = process.env.NOTION_DATABASE_ID;

const RULES_URL = 'https://raw.githubusercontent.com/tensoba700-byte/affiliate-portal/main/scripts/product_selection_prompt.txt';

// 会話で変更できる「動的なルール」を保存する場所
let customInstructions = '';

async function fetchRules() {
  try { const res = await fetch(RULES_URL); return res.ok ? await res.text() : null; } catch (e) { return null; }
}

async function addToNotion(products) {
  const VALID_CATEGORIES = ['ガジェット', '家電', '日用品', '食品・飲料', '美容・健康', '美容・スキンケア', '本・学習', 'その他', 'ガジェット・家電', '美容', '健康食品', '生活雑貨', 'インテリア', '便利グッズ', 'ライフスタイル雑貨', 'キッチンツール', 'モバイルアクセサリー', 'ヘルスケアガジェット'];
  let success = 0;
  for (const p of products) {
    const props = {};
    if (p.name) props['商品名'] = { title: [{ text: { content: p.name } }] };
    if (p.model) props['製品番号'] = { rich_text: [{ text: { content: p.model } }] };
    if (p.articleTitle) props['記事タイトル'] = { rich_text: [{ text: { content: p.articleTitle } }] };
    if (p.searchName) props['検索商品名'] = { rich_text: [{ text: { content: p.searchName || p.name } }] };
    if (p.reason) props['選定理由'] = { rich_text: [{ text: { content: p.reason } }] };
    if (p.category && VALID_CATEGORIES.includes(p.category)) props['カテゴリ'] = { select: { name: p.category } };
    if (p.publishTime) props['公開時間'] = { select: { name: p.publishTime } };
    props['ステータス 1'] = { select: { name: '未処理' } };
    const res = await fetch('https://api.notion.com/v1/pages', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + NOTION_API_KEY, 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent: { database_id: NOTION_DATABASE_ID }, properties: props }),
    });
    if (res.ok) success++;
  }
  return success;
}

let model;
(async () => {
  const rules = await fetchRules();
  model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash', systemInstruction: rules || '' });
  console.log('✅ GitHubの最新ルールを読み込みました');
})();

client.once('ready', () => console.log('✅ 商品選定じみにー 起動完了'));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  const prompt = message.content.trim();
  if (!prompt) return;

  if (prompt.includes('これからは') || prompt.includes('今後は')) {
    customInstructions = prompt;
    message.reply('✅ 覚えたで！次からその通りに動くわ。\n覚えた内容: ' + customInstructions);
    return;
  }
  if (prompt.includes('今のルール') || prompt.includes('覚えてること')) {
    message.reply(customInstructions ? '今の追加ルールはこれやで: ' + customInstructions : 'まだ特別なルールは覚えてへんで！');
    return;
  }

  const selectionKeywords = ['選定して', '選んで', '選定お願い', '選定実行', '商品を選定して', '商品を選んでくれ'];
  const shouldSelect = selectionKeywords.some(k => prompt.includes(k));

  if (shouldSelect) {
    message.reply('📋 GitHubの最新ルールで商品を選定中やで…');
    try {
      const rules = await fetchRules();
      if (!rules) return message.reply('ルールの取得に失敗したわ…');

      const fullPrompt = rules + '\n\n' + (customInstructions ? '【追加指示】\n' + customInstructions + '\n\n' : '') + '上記のルールに従って、6商品を以下のJSON形式で出力してください。\n[\n  {\n    "name": "商品名",\n    "model": "型番",\n    "articleTitle": "記事タイトル",\n    "searchName": "検索商品名",\n    "reason": "選定理由",\n    "category": "カテゴリ",\n    "publishTime": "朝 or 夜"\n  }\n]';
      
      const result = await model.generateContent(fullPrompt);
      const jsonMatch = result.response.text().match(/\[[\s\S]*\]/);
      if (!jsonMatch) return message.reply('JSONの抽出に失敗したわ…');

      const products = JSON.parse(jsonMatch[0]);
      message.reply('✅ テスト選定が完了したで！\n' + JSON.stringify(products, null, 2).substring(0, 1800));
    } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
    return;
  }

  try {
    const contextPrompt = (customInstructions ? '【現在の追加指示】\n' + customInstructions + '\n\n' : '') + '【ユーザーからのメッセージ】\n' + prompt;
    const result = await model.generateContent(contextPrompt);
    message.reply(result.response.text().substring(0, 1800));
  } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
