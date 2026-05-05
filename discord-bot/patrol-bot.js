// discord-bot/patrol-bot.js（巡回じみにー）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';

async function readGitHubFile(path) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${encodedPath}?ref=${BRANCH}`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) throw new Error(`ファイル読み込み失敗: ${res.status}`);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

async function getAllMarkdownFiles() {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/git/trees/${BRANCH}?recursive=1`;
  const res = await fetch(url, { headers: { Authorization: `token ${GITHUB_TOKEN}` } });
  if (!res.ok) return [];
  const data = await res.json();
  return (data.tree || [])
    .filter(item => item.type === 'blob' && item.path.endsWith('.md') && !item.path.startsWith('node_modules') && !item.path.startsWith('.git') && item.size <= 200 * 1024)
    .map(item => item.path);
}

client.once('ready', () => console.log(`✅ ${client.user.tag} 起動完了`));

client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  if (message.content.startsWith('!check-all-articles')) {
    message.reply('🔍 全記事を自動巡回中やで…');
    try {
      const allFiles = await getAllMarkdownFiles();
      const articleFiles = allFiles.filter(f => f.startsWith('src/content/articles/') && f.endsWith('.md'));
      if (articleFiles.length === 0) return message.reply('記事ファイルが見つからへんで。');
      message.reply(`${articleFiles.length}件の記事をチェックするで！');

      const problemFiles = [];
      for (const filePath of articleFiles) {
        const { content } = await readGitHubFile(filePath);
        const titleMatch = content.match(/^title: (.+)/m);
        const title = titleMatch ? titleMatch[1] : filePath;
        const hasPlaceholder = content.includes('[AMAZON_LINK_HERE]') || content.includes('[RAKUTEN_LINK_HERE]') || content.includes('[YAHOO_LINK_HERE]');
        const hasPR = content.includes('本記事はアフィリエイト広告');
        const imageCount = (content.match(/!\[.*?\]\(.*?\)/g) || []).length;

        let report = `📄 **${title}**\n`;
        if (hasPlaceholder) report += '⚠️ リンクプレースホルダーが残ってるで！\n';
        if (!hasPR) report += '⚠️ PR表記がないで！\n';
        if (imageCount < 1) report += '⚠️ 画像が1枚もないで！\n';
        if (!hasPlaceholder && hasPR && imageCount >= 1) report += '✅ 問題なさそうや！\n';
        else problemFiles.push({ filePath, title, hasPlaceholder, hasPR, imageCount });

        message.reply(report);
      }

      if (problemFiles.length > 0) {
        let summary = `🚨 **巡回じみにーからの報告やで！**\n以下の${problemFiles.length}件の記事に問題があるみたいや…\n\n`;
        for (const pf of problemFiles) {
          summary += `📄 **${pf.title}** → \`${pf.filePath}\`\n`;
          if (pf.hasPlaceholder) summary += '　⚠️ リンクプレースホルダー残存\n';
          if (!pf.hasPR) summary += '　⚠️ PR表記なし\n';
          if (pf.imageCount < 1) summary += '　⚠️ 画像なし\n';
        }
        message.channel.send(`@編集実行くん ${summary}`);
      }

      message.reply('✅ 全記事の巡回が完了したで！');
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }
});

http.createServer((req, res) => { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000, () => console.log('HTTP server is listening'));
client.login(process.env.DISCORD_TOKEN);
