// discord-bot/index.js（.cache/last_check.json 差分読み込み型）
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

// 前回チェック日時を読み込む
async function getLastCheckTime() {
  try {
    const { content } = await readGitHubFile(LAST_CHECK_FILE);
    const data = JSON.parse(content);
    return new Date(data.last_check);
  } catch {
    return new Date('2020-01-01T00:00:00Z');
  }
}

// 前回チェック日時を更新する
async function updateLastCheckTime(date = new Date()) {
  const json = { last_check: date.toISOString() };
  const { sha } = await readGitHubFile(LAST_CHECK_FILE);
  await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${LAST_CHECK_FILE}`, {
    method: 'PUT',
    headers: { Authorization: `token ${GITHUB_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: '🤖 Bot: 最終チェック日時を更新',
      content: Buffer.from(JSON.stringify(json, null, 2), 'utf-8').toString('base64'),
      branch: BRANCH, sha,
    }),
  });
}

// GitHubのコミット履歴から、指定日時以降に更新された.mdファイルを取得
async function getRecentlyModifiedFiles(sinceDate) {
  const files = new Set();
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/commits?since=${sinceDate.toISOString()}&per_page=100`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) return [];
  const commits = await res.json();
  
  for (const commit of commits) {
    const detailRes = await fetch(commit.url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
    if (!detailRes.ok) continue;
    const detail = await detailRes.json();
    const changedFiles = (detail.files || []).map(f => f.filename).filter(f => f.endsWith('.md'));
    changedFiles.forEach(f => files.add(f));
  }
  return [...files];
}

// 指定された.mdファイルだけを読み込んで結合
async function loadSpecificFiles(fileList) {
  const results = [];
  for (const file of fileList) {
    try {
      const fileUrl = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}/${file}`;
      const res = await fetch(fileUrl);
      if (res.ok) {
        const text = await res.text();
        results.push(`# ${file}\n${text}`);
      }
    } catch (e) { console.warn(`⚠️ ${file} の取得に失敗`); }
  }
  return results.join('\n\n---\n\n');
}

// 初回起動時は全ファイル、それ以降は差分だけ読み込む
let initialLoadDone = false;
let allRuleFiles = [];

async function fetchAndLearnRules() {
  const lastCheck = await getLastCheckTime();
  
  if (!initialLoadDone) {
    // 初回起動時：全ファイルを読み込む
    allRuleFiles = await getAllMarkdownFiles();
    const rules = await loadSpecificFiles(allRuleFiles);
    initialLoadDone = true;
    console.log(`✅ 初回：${allRuleFiles.length} 件の .md ファイルを読み込みました`);
    return rules;
  } else {
    // 2回目以降：差分ファイルだけを読み込む
    const modifiedFiles = await getRecentlyModifiedFiles(lastCheck);
    if (modifiedFiles.length === 0) {
      console.log('📭 新着ファイルなし');
      return null; // 学習不要
    }
    
    // 新しいファイルがあれば、一覧に追加し、学習データも返す
    const newFiles = modifiedFiles.filter(f => !allRuleFiles.includes(f));
    allRuleFiles = [...new Set([...allRuleFiles, ...modifiedFiles])];
    
    const newRules = await loadSpecificFiles(modifiedFiles);
    console.log(`🆕 ${modifiedFiles.length} 件の新着/更新ファイルを追加学習`);
    return newRules;
  }
}

// リポジトリ全体の.mdファイル一覧を取得（初回用）
async function getAllMarkdownFiles() {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/trees/${BRANCH}?recursive=1`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) return [];
  const data = await res.json();
  return (data.tree || [])
    .filter(item => 
      item.type === 'blob' && 
      item.path.endsWith('.md') &&
      !item.path.startsWith('node_modules') &&
      !item.path.startsWith('.git') &&
      item.size <= 200 * 1024 // 200KB制限
    )
    .map(item => item.path);
}

// --- 既存の関数 ---
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
    message: `🤖 Bot: ${path} を更新`,
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

// モデル管理
let model;
async function initializeModel(newRules = null) {
  if (!model || newRules) {
    // 初回起動時、または新ルールがある場合
    const allRules = await fetchAndLearnRules();
    model = genAI.getGenerativeModel({
      model: 'gemini-2.5-flash',
      systemInstruction: allRules
        ? `あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。以下はリポジトリ全体のルールです。このルールに従って分析・チェックを行ってください。\n\n${allRules}`
        : 'あなたは美容メディア「みっけ！」のSEO対策部門・分析担当です。',
    });
    await updateLastCheckTime();
  } else if (newRules) {
    // 既存モデルに新ルールを追加で教える
    const prompt = `以下の新しいルールを学習し、今後の分析に反映させてください。\n\n${newRules}`;
    await model.generateContent(prompt);
    await updateLastCheckTime();
  }
  console.log('✅ モデル準備完了');
}
initializeModel();

client.once('ready', () => console.log(`✅ ${client.user.tag} 起動完了`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  const isAllowedChannel = ALLOWED_CHANNEL_ID && message.channel.id === ALLOWED_CHANNEL_ID;

  // !reload コマンド（差分ルール再読み込み）
  if (message.content.startsWith('!reload')) {
    message.reply('🔄 新着ルールをチェック中...');
    try {
      const lastCheck = await getLastCheckTime();
      const modifiedFiles = await getRecentlyModifiedFiles(lastCheck);
      
      if (modifiedFiles.length === 0) {
        message.reply('📭 新しいルールファイルは見つからなかったで。');
      } else {
        const newRules = await loadSpecificFiles(modifiedFiles);
        await initializeModel(newRules);
        message.reply(`✅ ${modifiedFiles.length}件の新着ルールを学習したで！\n\`\`\`\n${modifiedFiles.join('\n')}\n\`\`\``);
      }
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
    return;
  }

  // 特定チャンネルではコマンドなしで反応
  if (isAllowedChannel && !message.content.startsWith('!update-code') && !message.content.startsWith('!check') && !message.content.startsWith('!reload')) {
    const prompt = message.content.trim();
    if (!prompt) return;
    if (!model) return message.reply('まだ準備中やねん…ちょっと待ってな〜');
    try {
      const result = await model.generateContent(prompt);
      message.reply(result.response.text());
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
    return;
  }

  // !seo コマンド
  if (message.content.startsWith('!seo')) {
    const prompt = message.content.slice(4).trim();
    if (!prompt) return message.reply('なにを修正すればいい？');
    if (!model) return message.reply('まだ準備中やねん…ちょっと待ってな〜');
    try {
      const result = await model.generateContent(prompt);
      message.reply(result.response.text());
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }

  // !check コマンド（記事の品質チェック）
  else if (message.content.startsWith('!check')) {
    const args = message.content.slice(6).trim().split(' ');
    const filePath = args[0];
    if (!filePath) return message.reply('使い方: `!check ファイルパス`');
    try {
      const { content } = await readGitHubFile(filePath);
      const result = await model.generateContent(`以下の記事ファイルを読み込み、ルールに基づいて品質チェックを行い、問題点を指摘してください。\n\n【記事本文】\n${content}`);
      message.reply(`📋 **${filePath} のチェック結果**\n\n${result.response.text()}`);
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }

  // !update-code コマンド
  else if (message.content.startsWith('!update-code')) {
    if (!GITHUB_TOKEN) return message.reply('GITHUB_TOKENが未設定やで。');
    const args = message.content.slice('!update-code'.length).trim().split(' ');
    const filePath = args[0];
    const instruction = args.slice(1).join(' ');
    if (!filePath || !instruction) return message.reply('使い方: `!update-code ファイル名 修正内容`');
    try {
      const { content: currentCode, sha } = await readGitHubFile(filePath);
      const prompt = `以下のファイルを、与えられた指示に従って修正し、修正後の全文のみを返してください。説明は不要です。\n\n【指示】\n${instruction}\n\n【現在のファイル内容】\n${currentCode}`;
      const result = await model.generateContent(prompt);
      const newCode = result.response.text().trim();
      if (!newCode || newCode === currentCode) return message.reply('修正内容が同じか、生成に失敗したみたいや…');
      await updateGitHubFile(filePath, newCode, sha);
      message.reply(`✅ \`${filePath}\` を更新したで！`);
    } catch (err) {
      message.reply('エラーや…: ' + (err.message || err));
    }
  }
});
  // ===== !overwrite コマンド（ファイル全体を上書き） =====
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

  // ===== !audit-articles コマンド（記事を自動巡回して画像・リンクチェック） =====
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

      const mdFiles = files
        .filter(f => f.type === 'file' && f.name.endsWith('.md'))
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

【出力1】問題点の指摘（箇条書き）。特に以下を重点的にチェック：
- 画像（![]()）が各商品に適

// HTTPサーバー
http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Bot is running!');
}).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));

client.login(process.env.DISCORD_TOKEN);
