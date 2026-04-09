import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function updateProductUrls(pageId: string, amazon: string, rakuten: string, yahoo: string) {
  const res = await fetch(`https://api.notion.com/v1/pages/${pageId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${process.env.NOTION_API_KEY}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      properties: {
        'Amazon参考URL': { url: amazon || null },
        '楽天参考URL': { url: rakuten || null },
        'Yahoo参考URL': { url: yahoo || null },
      }
    })
  });
  const data = await res.json();
  if (data.id) {
    console.log(`✅ Updated Notion: ${pageId}`);
  } else {
    console.error(`❌ Failed to update Notion: ${pageId}`, data);
  }
}

const args = process.argv.slice(2);
if (args.length === 4) {
  updateProductUrls(args[0], args[1], args[2], args[3]);
} else {
  console.log('Usage: npx tsx update-notion.ts <pageId> <amazon> <rakuten> <yahoo>');
}
