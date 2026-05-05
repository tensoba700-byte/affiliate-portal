// discord-bot/index.js（完全版：Notion APIで不足情報を自動補完）
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
const LAST_CHECK_FILE = '.cache/last_check.json';

// Notion API設定
const NOTION_API_KEY = process.env.NOTION_API_KEY;
const NOTION_DATABASE_ID = process.env.NOTION_DATABASE_ID;

// --- 既存の関数群（getLastCheckTime, updateLastCheckTime, getRecentlyModifiedFiles, loadSpecificFiles, fetchAndLearnRules, getAllMarkdownFiles）は前回と全く同じなので、ここではスペースの都合で割愛 ---
// ※GitHubの現在のindex.jsに書いてあるものをそのまま残してください。

// GitHubファイル読み込み/更新
async function readGitHubFile(path) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}?ref=${BRANCH}`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) throw new Error(`ファイル読み込み失敗: ${res.status}`);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

async function updateGitHubFile(path, newContent, sha) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`;
  const body = {
    message: `🤖 Bot: ${path} をNotionデータで更新`,
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

// モデル初期化
let model;
async function initializeModel(newRules = null) {
  const { GoogleGenerativeAI } = require('@google/generative-ai');
  if (!model || newRules) {
    const allRules = await fetchAndLearnRules();
    model = genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      systemInstruction: allRules ? `あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。以下はリポジトリ全体のルールです。このルールに従って分析・チェックを行ってください。\n\n${allRules}` : 'あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。',
    });
    await updateLastCheckTime();
  } else if (newRules) {
    const prompt = `以下の新しいルールを学習し、今後の分析に反映させてください。\n\n${newRules}`;
    await model.generateContent(prompt);
    await updateLastCheckTime();
  }
}
initializeModel();

client.once('ready', () => console.log(`✅ ${client.user.tag} 起動完了`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;
  const isAllowedChannel = ALLOWED_CHANNEL_ID && message.channel.id === ALLOWED_CHANNEL_ID;

  // フリーテキスト反応
  if (isAllowedChannel && !message.content.startsWith('!update-code') && !message.content.startsWith('!check') && !message.content.startsWith('!reload') && !message.content.startsWith('!overwrite') && !message.content.startsWith('!audit-articles') && !message.content.startsWith('!fix-from-notion')) {
    const prompt = message.content.trim(); if (!prompt) return; if (!model) return message.reply('まだ準備中やねん…');
    try { const result = await model.generateContent(prompt); const replyText = result.response.text(); message.reply(replyText.substring(0, 1800)); } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
    return;
  }

  // !seo コマンド
  if (message.content.startsWith('!seo')) {
    const prompt = message.content.slice(4).trim(); if (!prompt) return message.reply('なにを修正すればいい？'); if (!model) return message.reply('まだ準備中やねん…');
    try { const result = await model.generateContent(prompt); message.reply(result.response.text().substring(0, 1800)); } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
  }

  // !check コマンド
  else if (message.content.startsWith('!check')) {
    const args = message.content.slice(6).trim().split(' '); const filePath = args[0]; if (!filePath) return message.reply('使い方: `!check ファイルパス`');
    try { const { content } = await readGitHubFile(filePath); const result = await model.generateContent(`以下の記事ファイルを分析し問題点を指摘してください。\n\n${content}`); message.reply(`📋 **${filePath} のチェック結果**\n\n${result.response.text().substring(0, 1800)}`); } catch (err) { message.reply('エラーや…: ' + (err.message || err)); }
  }

  // !update-code コマンド
  else if (message.content.startsWith('!update-code')) { /* 既存コードを保持 */ }

  // !overwrite コマンド
  else if (message.content.startsWith('!overwrite')) { /* 既存コードを保持 */ }

// ===== !audit-articles コマンド（完全自動化版：分析→自動修正指示） =====
  else if (message.content.startsWith('!audit-articles')) {
    const args = message.content.slice(15).trim().split(' ');
    const targetDir = args[0] || 'src/content/articles';
    const maxArticles = parseInt(args[1]) || 1;
    message.reply(`🔍 \`${targetDir}\` 内の最新記事を${maxArticles}件、完全自動分析＆修正中やで…`);

    try {
      const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${targetDir}?ref=${BRANCH}`;
      const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
      if (!res.ok) throw new Error(`フォルダ読み込み失敗: ${res.status}`);
      const files = await res.json();

      const mdFiles = files
        .filter(f => f.type === 'file' && f.name.endsWith('.md'))
        .sort((a, b) => new Date(b.last_committed || 0) - new Date(a.last_committed || 0));
      if (mdFiles.length === 0) return message.reply('📭 記事ファイルが見つからへんで。');
      const targets = mdFiles.slice(0, maxArticles);
      
      for (const file of targets) {
        const filePath = `${targetDir}/${file.name}`;
        const { content } = await readGitHubFile(filePath);
        message.reply(`📝 **${file.name}** を分析＆自動修正中…`);

        // 分析プロンプト（タイトル、メタディスクリプション、画像・リンクを含む）
        const fixPrompt = `
あなたは美容メディア「みっけ！」のSEO編集者です。以下の記事を分析し、問題点を指摘した上で、修正後の全文をMarkdown形式で出力してください。
現在の記事:
${content}
`;
        const result = await model.generateContent(fixPrompt);
        const fullResponse = result.response.text();

        // 修正後の全文を抽出（簡易的な方法：最後の大きなテキストブロックを取得）
        const correctedContent = fullResponse; // 必要に応じてパース処理を追加

        // ✅ 編集実行くんに自動で修正指示を送信
        const editCommand = `@編集実行くん !replace ${filePath} ${correctedContent.substring(0, 1800)}`;
        message.channel.send(editCommand);
      }

      message.reply('✅ 指定された記事の分析と自動修正指示を完了したで！');
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  } 
  // ===== !fix-from-notion コマンド（Notion APIで不足情報を補完し記事を自動更新） =====
  else if (message.content.startsWith('!fix-from-notion')) {
    const filePath = message.content.slice(16).trim();
    if (!filePath) return message.reply('使い方: `!fix-from-notion ファイルパス`');
    if (!NOTION_API_KEY || !NOTION_DATABASE_ID) {
      return message.reply('Notion APIキーかデータベースIDが未設定やで。環境変数を確認してな。');
    }

    message.reply(`🔍 Notionから「${filePath}」の不足情報を補完し、記事を自動更新中やで…`);

    try {
      // 1. 記事ファイルを読み込む
      const { content, sha } = await readGitHubFile(filePath);
      
      // 2. 記事タイトルを抽出
      const titleMatch = content.match(/^# (.+)/m);
      if (!titleMatch) return message.reply('記事タイトルが見つからへん。');
      const articleTitle = titleMatch[1].trim();

      // 3. Notion APIで記事を検索
      const notionRes = await fetch(`https://api.notion.com/v1/databases/${NOTION_DATABASE_ID}/query`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${NOTION_API_KEY}`,
          'Notion-Version': '2022-06-28',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filter: { property: '記事タイトル', rich_text: { equals: articleTitle } }
        })
      });
      const notionData = await notionRes.json();

      if (notionData.results.length === 0) {
        return message.reply(`Notionに「${articleTitle}」が見つからへんかった。タイトルが完全一致してるか確認してな。`);
      }

      const page = notionData.results[0];
      const props = page.properties;

      // 4. Notionのプロパティから画像URL、アフィリエイトリンクを取得
      const imageUrl = props['画像']?.url || null;
      const amazonLink = props['Amazonリンク']?.url || null;
      const rakutenLink = props['楽天リンク']?.url || null;
      const yahooLink = props['Yahooリンク']?.url || null;

      // 5. 記事本文を修正（プレースホルダーや不足URLを置換）
      let updatedContent = content;

      // [AMAZON_LINK_HERE] を置換
      updatedContent = updatedContent.replace(/\[AMAZON_LINK_HERE\]/g, amazonLink || '[Amazonリンク未登録]');
      // [RAKUTEN_LINK_HERE] を置換
      updatedContent = updatedContent.replace(/\[RAKUTEN_LINK_HERE\]/g, rakutenLink || '[楽天リンク未登録]');
      // [YAHOO_LINK_HERE] を置換
      updatedContent = updatedContent.replace(/\[YAHOO_LINK_HERE\]/g, yahooLink || '[Yahooリンク未登録]');

      // もし記事に画像がなく、Notionに画像URLがあれば挿入（簡易版）
      if (imageUrl && !content.includes('![')) {
        updatedContent = updatedContent.replace(/(# .+)/, `$1\n\n![記事アイキャッチ](${imageUrl})`);
      }

      // 6. 更新をGitHubに反映
      await updateGitHubFile(filePath, updatedContent, sha);

      message.reply(`✅ Notionのデータで「${articleTitle}」の不足情報を補完して、記事を更新したで！\n` +
        `画像: ${imageUrl ? '✅ 反映' : '❌ 未登録'}\n` +
        `Amazon: ${amazonLink ? '✅ 反映' : '❌ 未登録'}\n` +
        `楽天: ${rakutenLink ? '✅ 反映' : '❌ 未登録'}\n` +
        `Yahoo: ${yahooLink ? '✅ 反映' : '❌ 未登録'}`);
        
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));
client.login(process.env.DISCORD_TOKEN);
