// discord-bot/index.js（キーローテーション対応 + 全機能搭載）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');

// 複数 API キーを読み込み
const API_KEYS = (process.env.GEMINI_API_KEYS || '').split(',').map(k => k.trim()).filter(Boolean);
if (API_KEYS.length === 0) throw new Error('GEMINI_API_KEYS に有効なキーがありません');

let currentKeyIndex = 0;
let genAI = new GoogleGenerativeAI(API_KEYS[currentKeyIndex]);

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';
const ALLOWED_CHANNEL_ID = process.env.ALLOWED_CHANNEL_ID;
const LAST_CHECK_FILE = '.cache/last_check.json';

// --- ルール・モデル管理 ---
let systemInstruction = 'あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。';
let model;

function recreateModel() {
  model = genAI.getGenerativeModel({
    model: 'gemini-2.5-flash',
    systemInstruction: systemInstruction,
  });
  console.log('🔁 モデルを再構築しました');
}

// 前回チェック日時（既存の関数を再利用）
async function readGitHubFile(path) { /* 既存コードと全く同じ */ }
async function updateGitHubFile(path, newContent, sha) { /* 既存コードと全く同じ */ }
async function getLastCheckTime() { /* 既存コードと全く同じ */ }
async function updateLastCheckTime(date = new Date()) { /* 既存コードと全く同じ */ }
async function getRecentlyModifiedFiles(sinceDate) { /* 既存コードと全く同じ */ }
async function loadSpecificFiles(fileList) { /* 既存コードと全く同じ */ }
let initialLoadDone = false;
let allRuleFiles = [];
async function fetchAndLearnRules() { /* 既存コードと全く同じ */ }
async function getAllMarkdownFiles() { /* 既存コードと全く同じ */ }

// 初期モデル構築
async function initializeFirstTime() {
  const allRules = await fetchAndLearnRules();
  systemInstruction = allRules
    ? `あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。以下はリポジトリ全体のルールです。このルールに従って分析・チェックを行ってください。\n\n${allRules}`
    : systemInstruction;
  recreateModel();
  await updateLastCheckTime();
  console.log('✅ 初回モデル準備完了');
}

// 新ルールを追加してモデル再構築
async function addNewRules(newRules) {
  systemInstruction += '\n\n' + newRules;
  recreateModel();
  await updateLastCheckTime();
  console.log('✅ 新ルールを追加しモデルを再構築');
}

// APIキーの自動切り替え
async function switchToNextKey() {
  currentKeyIndex = (currentKeyIndex + 1) % API_KEYS.length;
  genAI = new GoogleGenerativeAI(API_KEYS[currentKeyIndex]);
  console.log(`🔄 APIキーを No.${currentKeyIndex + 1} に切り替え`);
  recreateModel();
}

// リトライ付き生成ラッパー
async function generateContentWithRetry(prompt) {
  for (let attempt = 0; attempt < API_KEYS.length; attempt++) {
    try {
      if (!model) recreateModel();
      const result = await model.generateContent(prompt);
      return result;
    } catch (err) {
      if (err.message.includes('429 Too Many Requests')) {
        console.log(`⚠️ 429 制限、キー切替え (${attempt + 1}/${API_KEYS.length})`);
        await switchToNextKey();
        continue;
      }
      throw err;
    }
  }
  throw new Error('すべての API キーが制限中です');
}

// 起動時に初回モデル作成
initializeFirstTime();

client.once('ready', () => console.log(`✅ ${client.user.tag} 起動完了`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  const isAllowedChannel = ALLOWED_CHANNEL_ID && message.channel.id === ALLOWED_CHANNEL_ID;

  // !reload
  if (message.content.startsWith('!reload')) {
    message.reply('🔄 新着ルールをチェック中...');
    try {
      const lastCheck = await getLastCheckTime();
      const modifiedFiles = await getRecentlyModifiedFiles(lastCheck);
      if (modifiedFiles.length === 0) {
        message.reply('📭 新しいルールファイルは見つからなかったで。');
      } else {
        const newRules = await loadSpecificFiles(modifiedFiles);
        await addNewRules(newRules);
        message.reply(`✅ ${modifiedFiles.length}件の新着ルールを学習したで！\n\`\`\`\n${modifiedFiles.join('\n')}\n\`\`\``);
      }
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
    return;
  }

  // 特定チャンネルでのフリーテキスト反応（コマンドを除外）
  if (isAllowedChannel &&
      !message.content.startsWith('!update-code') &&
      !message.content.startsWith('!check') &&
      !message.content.startsWith('!reload') &&
      !message.content.startsWith('!overwrite') &&
      !message.content.startsWith('!audit-articles') &&
      !message.content.startsWith('!seo')) {
    const prompt = message.content.trim();
    if (!prompt) return;
    try {
      const result = await generateContentWithRetry(prompt);
      message.reply(result.response.text());
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
    return;
  }

  // !seo
  if (message.content.startsWith('!seo')) {
    const prompt = message.content.slice(4).trim();
    if (!prompt) return message.reply('なにを修正すればいい？');
    try {
      const result = await generateContentWithRetry(prompt);
      message.reply(result.response.text());
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }

  // !check
  else if (message.content.startsWith('!check')) {
    const args = message.content.slice(6).trim().split(' ');
    const filePath = args[0];
    if (!filePath) return message.reply('使い方: `!check ファイルパス`');
    try {
      const { content } = await readGitHubFile(filePath);
      const prompt = `以下の記事ファイルを読み込み、ルールに基づいて品質チェックを行い、問題点を指摘してください。\n\n【記事本文】\n${content}`;
      const result = await generateContentWithRetry(prompt);
      message.reply(`📋 **${filePath} のチェック結果**\n\n${result.response.text()}`);
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }

  // !update-code
  else if (message.content.startsWith('!update-code')) {
    if (!GITHUB_TOKEN) return message.reply('GITHUB_TOKENが未設定やで。');
    const args = message.content.slice('!update-code'.length).trim().split(' ');
    const filePath = args[0];
    const instruction = args.slice(1).join(' ');
    if (!filePath || !instruction) return message.reply('使い方: `!update-code ファイル名 修正内容`');
    try {
      const { content: currentCode, sha } = await readGitHubFile(filePath);
      const prompt = `以下のファイルを、与えられた指示に従って修正し、修正後の全文のみを返してください。説明は不要です。\n\n【指示】\n${instruction}\n\n【現在のファイル内容】\n${currentCode}`;
      const result = await generateContentWithRetry(prompt);
      const newCode = result.response.text().trim();
      if (!newCode || newCode === currentCode) return message.reply('修正内容が同じか、生成に失敗したみたいや…');
      await updateGitHubFile(filePath, newCode, sha);
      message.reply(`✅ \`${filePath}\` を更新したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }

  // !overwrite
  else if (message.content.startsWith('!overwrite')) {
    const lines = message.content.split('\n');
    const filePath = lines[0].slice(10).trim();
    const newCode = lines.slice(1).join('\n');
    if (!filePath || !newCode) {
      return message.reply('使い方: `!overwrite ファイルパス` の後に、新しいコード全体を貼り付けてください。');
    }
    try {
      const { sha } = await readGitHubFile(filePath);
      await updateGitHubFile(filePath, newCode, sha);
      message.reply(`✅ \`${filePath}\` を上書き更新したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }

  // !audit-articles
  else if (message.content.startsWith('!audit-articles')) {
    const args = message.content.slice(15).trim().split(' ');
    const targetDir = args[0] || 'src/content/articles';
    const maxArticles = parseInt(args[1]) || 1;
    message.reply(`🔍 \`${targetDir}\` 内の最新記事を${maxArticles}件、画像・リンクも含めて徹底チェック中やで…`);
    try {
      const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${targetDir}?ref=${BRANCH}`;
      const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
      if (!res.ok) throw new Error(`フォルダ読み込み失敗: ${res.status}`);
      const files = await res.json();
      const mdFiles = files.filter(f => f.type === 'file' && f.name.endsWith('.md'))
                           .sort((a, b) => new Date(b.last_committed || 0) - new Date(a.last_committed || 0));
      if (mdFiles.length === 0) return message.reply('📭 記事ファイルが見つからへんで。');
      const targets = mdFiles.slice(0, maxArticles);
      for (const file of targets) {
        const filePath = `${targetDir}/${file.name}`;
        const { content } = await readGitHubFile(filePath);
        message.reply(`📝 **${file.name}** を画像・リンクも含めて徹底分析中…`);
        const fixPrompt = `
あなたは美容メディア「みっけ！」のSEO編集者です。
以下の記事を読み、GENERATION_RULES.md と SEO_RULES.md に厳密に従って、以下の3つを出力してください。
【出力1】問題点の指摘（箇条書き）：
- 画像（![]()）が各商品に適切に貼られているか？alt属性はあるか？
- アフィリエイトリンク（Amazon・楽天・Yahoo）が各商品に3つずつあるか？
- 画像URLが有効か？（404になってないか）
- 商品名と画像のaltテキストが一致しているか？

【出力2】修正後の記事全文（Markdown形式）
- 不足している画像は、商品名から推測される適切な画像URLを補完する
- 不足しているアフィリエイトリンクは、商品名から推測される適切なURLを補完する

【出力3】不足している画像・リンクの一覧（箇条書き）

現在の記事:
${content}
`;
        const result = await generateContentWithRetry(fixPrompt);
        const fullResponse = result.response.text();
        message.reply(`📋 **${file.name} の徹底分析結果**\n\n${fullResponse}`);
        message.reply(`💡 **編集実行くんに渡すコマンド:**\n\`!replace ${filePath} [上記の修正後全文をコピペ]\``);
      }
      message.reply('✅ 指定された記事の画像・リンクチェックが完了したで！');
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }
});

// HTTPサーバー
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
}).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));

client.login(process.env.DISCORD_TOKEN);
