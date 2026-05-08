// discord-bot/product-bot.js（デバッグログ強化版）
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

async function addToNotion(product) {
  const body = {
    parent: { database_id: NOTION_DATABASE_ID },
    properties: {
      '商品名': { title: [{ text: { content: product.name || '不明' } }] },
      'カテゴリ': { select: { name: product.category || '未分類' } },
      'ステータス 1': { select: { name: '未処理' } },
    },
  };
  console.log('📤 Notion登録リクエスト:', JSON.stringify(body, null, 2));
  const res = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + NOTION_API_KEY,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const resText = await res.text();
  console.log('📥 Notionレスポンス:', res.status, resText.substring(0, 300));
  return res.ok;
}

const SELECTION_PROMPT = `あなたは「みっけ！」の商品選定担当AIです。以下の手順に厳密に従って、6つの商品を選定してください。

## Step 1：記事タイトルを1つ決める
- ジャンル・性格・モード・深度・視点の組み合わせを自律決定する
- 品質基準を満たすタイトルを1つ生成する

## Step 2：そのタイトルのテーマに沿った商品を6件選定する
- 全商品がStep 1のタイトルテーマと一致していること
- Amazon・楽天両方で購入可能な商品のみ
- ありきたりメーカーを除外すること

## Step 3：出力フォーマット（最重要）
以下のJSON形式だけを出力してください。説明やコメントは一切不要です。
[
  {
    "name": "商品名",
    "category": "カテゴリ"
  }
]`;

client.once('ready', () => console.log('✅ 商品選定じみにー 起動完了（デバッグモード）'));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  if (message.content.startsWith('!select-products')) {
    message.reply('🔍 商品を選定中やで…（デバッグモード）');

    try {
      console.log('🚀 Gemini API呼び出し開始');
      const result = await model.generateContent(SELECTION_PROMPT);
      const responseText = result.response.text();
      console.log('📝 Geminiレスポンス全文:\n' + responseText.substring(0, 1000));

      const jsonMatch = responseText.match(/\[[\s\S]*\]/);
      if (!jsonMatch) {
        console.log('❌ JSON抽出失敗');
        return message.reply('JSONの抽出に失敗したわ…ログを確認してくれ。');
      }

      console.log('🔍 JSON候補:', jsonMatch[0].substring(0, 500));
      const products = JSON.parse(jsonMatch[0]);
      console.log('✅ パース成功: ' + products.length + '件の商品');

      let successCount = 0;
      for (const product of products) {
        console.log('📤 Notion登録中: ' + (product.name || '名前なし'));
        const ok = await addToNotion(product);
        if (ok) successCount++;
        else console.log('❌ Notion登録失敗: ' + (product.name || '名前なし'));
      }

      message.reply('✅ ' + successCount + '/' + products.length + '件の商品をNotionに登録したで！');
    } catch (err) {
      console.log('❌ 全体エラー: ' + (err.message || err));
      console.log('❌ スタックトレース: ' + (err.stack || 'なし'));
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
