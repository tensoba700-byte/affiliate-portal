// GitHubにカスタム指示を保存する関数
async function saveCustomInstructions(instructions) {
  const path = 'scripts/custom_instructions.txt';
  const url = 'https://api.github.com/repos/tensoba700-byte/affiliate-portal/contents/' + path;
  
  try {
    // 既存のファイルがあるか確認
    const checkRes = await fetch(url, { headers: { Authorization: 'token ' + process.env.GITHUB_TOKEN } });
    let sha = null;
    if (checkRes.ok) {
      const data = await checkRes.json();
      sha = data.sha;
    }

    const body = {
      message: '🤖 Bot: カスタム指示を更新',
      content: Buffer.from(instructions, 'utf-8').toString('base64'),
      branch: 'main',
    };
    if (sha) body.sha = sha;

    await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': 'token ' + process.env.GITHUB_TOKEN,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    return true;
  } catch (e) {
    console.error('カスタム指示の保存に失敗:', e.message);
    return false;
  }
}
