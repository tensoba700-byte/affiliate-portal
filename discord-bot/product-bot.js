// discord-bot/product-bot.js（Claude互換プロンプト完全版）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const NOTION_API_KEY = process.env.NOTION_API_KEY;
const NOTION_DATABASE_ID = process.env.NOTION_DATABASE_ID;

let model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

// Notionに商品を登録する関数
async function addToNotion(product) {
  const res = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + NOTION_API_KEY,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      parent: { database_id: NOTION_DATABASE_ID },
      properties: {
        '商品名': { title: [{ text: { content: product.name } }] },
        '製品番号': { rich_text: [{ text: { content: product.model || '' } }] },
        '記事タイトル': { rich_text: [{ text: { content: product.articleTitle || '' } }] },
        '検索商品名': { rich_text: [{ text: { content: product.searchName || product.name } }] },
        '選定理由': { rich_text: [{ text: { content: product.reason || '' } }] },
        'カテゴリ': { select: { name: product.category || '未分類' } },
        '公開時間': { select: { name: product.publishTime || '朝' } },
        'ステータス 1': { select: { name: '未処理' } },
      },
    }),
  });
  return res.ok;
}

// 商品選定のプロンプト（Claudeの完全版をベースに、GeminiのWebSearch指示に最適化）
const SELECTION_PROMPT = `あなたは「みっけ！」の商品選定担当AIです。以下の手順に厳密に従って、6つの商品を選定してください。

## Step 1：記事タイトルを1つ決める
- ジャンル・性格・モード・深度・視点の組み合わせを自律決定する
- 品質基準を満たすタイトルを1つ生成する

## Step 2：そのタイトルのテーマに沿った商品を6件選定する
- 全商品がStep 1のタイトルテーマと一致していること
- Amazon・楽天両方で購入可能な商品のみ
- ありきたりメーカーを除外すること

## Step 3：商品の実在確認
各商品について、ブラウザ検索で以下のURLを確認し、商品が実在するか検証する：
- Amazon：https://www.amazon.co.jp/dp/[ASIN]?tag=mikkestyle-22
- 楽天：item.rakuten.co.jp の商品ページ
- Yahoo!：store.shopping.yahoo.co.jp の商品ページ

## Step 4：出力フォーマット
以下のJSON形式で出力してください。
[
  {
    "name": "商品名",
    "maker": "メーカー名",
    "model": "型番",
    "category": "カテゴリ",
    "articleTitle": "記事タイトル",
    "searchName": "検索商品名",
    "reason": "選定理由",
    "publishTime": "朝 or 夜",
    "price": 価格,
    "rakuten_url": "楽天アフィリエイトURL",
    "amazon_url": "AmazonアフィリエイトURL",
    "yahoo_url": "YahooアフィリエイトURL",
    "image_url": "楽天の商品画像URL"
  }
]`;

client.once('ready', () => console.log('✅ 商品選定じみにー 起動完了（Claude互換完全版）'));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  if (message.content.startsWith('!select-products')) {
    message.reply('🔍 Claudeと同じロジックで商品を選定中やで…');

    try {
      const result = await model.generateContent(SELECTION_PROMPT);
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
