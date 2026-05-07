// discord-bot/patrol-bot.js（鮮度チェック機能付き版）
const http = require('http');
const { Client, GatewayIntentBits } = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent],
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const REPO_OWNER = 'tensoba700-byte';
const REPO_NAME = 'affiliate-portal';
const BRANCH = 'main';

// ファイル読み込み
async function readGitHubFile(path) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath + '?ref=' + BRANCH;
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) throw new Error('ファイル読み込み失敗: ' + res.status);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

// 全.mdファイル一覧を取得
async function getAllMarkdownFiles() {
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/git/trees/' + BRANCH + '?recursive=1';
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) return [];
  const data = await res.json();
  return (data.tree || [])
    .filter(item => item.type === 'blob' && item.path.endsWith('.md') && !item.path.startsWith('node_modules') && !item.path.startsWith('.git') && item.size <= 200 * 1024)
    .map(item => item.path);
}

// ファイルの最終コミット日時を取得
async function getLastCommitDate(path) {
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/commits?path=' + encodeURIComponent(path) + '&per_page=1';
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) return null;
  const commits = await res.json();
  if (commits.length === 0) return null;
  return new Date(commits[0].commit.committer.date);
}

client.once('ready', function() { console.log('✅ ' + client.user.tag + ' 起動完了（鮮度チェック機能付き）'); });

client.on('messageCreate', async function(message) {
  if (message.author.bot) return;

  if (message.content.startsWith('!check-all-articles')) {
    message.reply('🔍 全記事を自動巡回中やで…（鮮度チェック付き）');
    try {
      const allFiles = await getAllMarkdownFiles();
      const articleFiles = allFiles.filter(f => f.startsWith('src/content/articles/') && f.endsWith('.md'));
      if (articleFiles.length === 0) return message.reply('記事ファイルが見つからへんで。');
      
      message.reply(articleFiles.length + '件の記事をチェックするで！');

      const problemFiles = [];
      for (const filePath of articleFiles) {
        const { content } = await readGitHubFile(filePath);
        const titleMatch = content.match(/^title: (.+)/m);
        const title = titleMatch ? titleMatch[1] : filePath;
        
        // 基本チェック（リンク・PR・画像）
        const hasPlaceholder = content.includes('[AMAZON_LINK_HERE]') || content.includes('[RAKUTEN_LINK_HERE]') || content.includes('[YAHOO_LINK_HERE]');
        const hasPR = content.includes('本記事はアフィリエイト広告');
        const imageCount = (content.match(/!\[.*?\]\(.*?\)/g) || []).length;

        // 鮮度チェック（最終コミット日時）
        const lastCommitDate = await getLastCommitDate(filePath);
        let daysSinceUpdate = null;
        if (lastCommitDate) {
          daysSinceUpdate = Math.floor((Date.now() - lastCommitDate.getTime()) / (1000 * 60 * 60 * 24));
        }

        let report = '📄 **' + title + '**\n';
        if (hasPlaceholder) report += '⚠️ リンクプレースホルダーが残ってるで！\n';
        if (!hasPR) report += '⚠️ PR表記がないで！\n';
        if (imageCount < 1) report += '⚠️ 画像が1枚もないで！\n';
        
        // 鮮度チェックの結果を追加（7日以上更新がない場合）
        if (daysSinceUpdate !== null && daysSinceUpdate > 7) {
          report += '⏰ 最終更新から' + daysSinceUpdate + '日経過してるで！\n';
          report += '　💡 改善アイデア：公開日の更新、関連記事へのリンク追加、タイトルの見直し、アイキャッチ画像の変更など\n';
        }

        if (!hasPlaceholder && hasPR && imageCount >= 1 && (daysSinceUpdate === null || daysSinceUpdate <= 7)) {
          report += '✅ 問題なさそうや！\n';
        } else {
          problemFiles.push({ filePath, title, hasPlaceholder, hasPR, imageCount, daysSinceUpdate });
        }

        message.reply(report);
      }

      // 問題があるファイルがあれば、編集実行くんに自動報告
      if (problemFiles.length > 0) {
        let summary = '🚨 **巡回じみにーからの報告やで！**\n以下の' + problemFiles.length + '件の記事に問題があるみたいや…\n\n';
        for (const pf of problemFiles) {
          summary += '📄 **' + pf.title + '** → `' + pf.filePath + '`\n';
          if (pf.hasPlaceholder) summary += '　⚠️ リンクプレースホルダー残存\n';
          if (!pf.hasPR) summary += '　⚠️ PR表記なし\n';
          if (pf.imageCount < 1) summary += '　⚠️ 画像なし\n';
          if (pf.daysSinceUpdate !== null && pf.daysSinceUpdate > 7) summary += '　⏰ ' + pf.daysSinceUpdate + '日未更新\n';
        }
        message.channel.send('@編集実行くん ' + summary);
      }

      message.reply('✅ 全記事の巡回（鮮度チェック付き）が完了したで！');
    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }
});

http.createServer(function(req, res) { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000, function() { console.log('HTTP server is listening'); });
client.login(process.env.DISCORD_TOKEN);
