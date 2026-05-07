// discord-bot/patrol-bot.js（巡回じみにーが直接GitHubを更新する完全版）
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
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath + '?ref=' + BRANCH;
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) throw new Error('ファイル読み込み失敗: ' + res.status);
  const data = await res.json();
  return { content: Buffer.from(data.content, 'base64').toString('utf-8'), sha: data.sha };
}

// GitHubのファイルを更新する関数（巡回じみにーに追加！）
async function updateGitHubFile(path, newContent, sha) {
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/contents/' + encodedPath;
  const body = {
    message: '🤖 巡回じみにー: 関連記事を最新化 - ' + path,
    content: Buffer.from(newContent, 'utf-8').toString('base64'),
    branch: BRANCH, sha,
  };
  const res = await fetch(url, {
    method: 'PUT', headers: { Authorization: 'token ' + GITHUB_TOKEN, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('GitHub APIエラー: ' + res.status);
  return await res.json();
}

async function getAllMarkdownFiles() {
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/git/trees/' + BRANCH + '?recursive=1';
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) return [];
  const data = await res.json();
  return (data.tree || []).filter(item => item.type === 'blob' && item.path.endsWith('.md') && !item.path.startsWith('node_modules') && !item.path.startsWith('.git') && item.size <= 200 * 1024).map(item => item.path);
}

async function getLastCommitDate(path) {
  const url = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME + '/commits?path=' + encodeURIComponent(path) + '&per_page=1';
  const res = await fetch(url, { headers: { Authorization: 'token ' + GITHUB_TOKEN } });
  if (!res.ok) return null;
  const commits = await res.json();
  return commits.length > 0 ? new Date(commits[0].commit.committer.date) : null;
}

function extractCategory(content) {
  const match = content.match(/category:\s*(.+)/);
  return match ? match[1].trim().replace(/['"]/g, '') : '未分類';
}

client.once('ready', function() { console.log('✅ ' + client.user.tag + ' 起動完了（巡回じみにー直接更新版）'); });

client.on('messageCreate', async function(message) {
  if (message.author.bot) return;

  if (message.content.startsWith('!check-all-articles')) {
    message.reply('🔍 全記事を巡回し、古い記事の「合わせて見たい記事」を自動更新中やで…');
    try {
      const allFiles = await getAllMarkdownFiles();
      const articleFiles = allFiles.filter(f => f.startsWith('src/content/articles/') && f.endsWith('.md'));
      if (articleFiles.length === 0) return message.reply('記事ファイルが見つからへんで。');
      
      message.reply(articleFiles.length + '件の記事をチェックするで！');
      let updatedCount = 0;

      for (const filePath of articleFiles) {
        const { content, sha } = await readGitHubFile(filePath);
        const titleMatch = content.match(/^title: (.+)/m);
        const title = titleMatch ? titleMatch[1] : filePath;
        const category = extractCategory(content);
        const lastCommitDate = await getLastCommitDate(filePath);
        let daysSinceUpdate = null;
        if (lastCommitDate) daysSinceUpdate = Math.floor((Date.now() - lastCommitDate.getTime()) / (1000 * 60 * 60 * 24));

        if (daysSinceUpdate !== null && daysSinceUpdate > 7) {
          // 同じカテゴリの最新記事を最大3つ探す
          const relatedArticles = [];
          for (const otherFile of articleFiles) {
            if (otherFile === filePath) continue;
            try {
              const { content: otherContent } = await readGitHubFile(otherFile);
              const otherCategory = extractCategory(otherContent);
              const otherPublishDateMatch = otherContent.match(/publishDate:\s*(.+)/);
              const otherPublishDate = otherPublishDateMatch ? new Date(otherPublishDateMatch[1]) : new Date(0);
              const otherTitleMatch = otherContent.match(/^title: (.+)/m);
              const otherTitle = otherTitleMatch ? otherTitleMatch[1] : otherFile;
              if (otherCategory === category) {
                relatedArticles.push({ title: otherTitle, date: otherPublishDate, link: otherFile.replace('src/content/articles/', '/articles/').replace('.md', '') });
              }
            } catch(e) {}
          }
          relatedArticles.sort((a, b) => b.date - a.date);
          const topRelated = relatedArticles.slice(0, 3);
          
          if (topRelated.length > 0) {
            // 新しい「合わせて見たい記事」の候補リンクを作成
            let newRelatedLinks = '\n## あわせて見たい記事\n';
            for (const ra of topRelated) {
              newRelatedLinks += '- [' + ra.title + '](' + ra.link + ')\n';
            }
            
            // 記事内の「あわせて見たい記事」セクションを置き換え
            let updatedContent = content;
            // すでに「あわせて見たい記事」があれば置き換え、なければ末尾に追加
            if (content.includes('あわせて見たい記事')) {
              updatedContent = content.replace(/## あわせて見たい記事[\s\S]*?(?=\n##|\n*$)/, newRelatedLinks.trim());
            } else {
              updatedContent = content.trimEnd() + '\n\n' + newRelatedLinks.trim();
            }
            
            await updateGitHubFile(filePath, updatedContent, sha);
            message.reply('✅ **' + title + '**（' + daysSinceUpdate + '日経過）の関連記事を最新化したで！');
            updatedCount++;
          }
        }
      }
      message.reply('🎉 ' + updatedCount + '件の記事の「合わせて見たい記事」を最新化したで！');

    } catch (err) {
      message.reply('エラーが発生したよ…: ' + (err.message || err));
    }
  }
});

http.createServer(function(req, res) { res.writeHead(200, { 'Content-Type': 'text/plain' }); res.end('Bot is running!'); }).listen(process.env.PORT || 3000);
client.login(process.env.DISCORD_TOKEN);
