import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const token = process.env.NOTION_API_KEY;
const databaseId = process.env.NOTION_DATABASE_ID;

async function clearAllAsins() {
  if (!token || !databaseId) {
    console.error('Missing env vars');
    return;
  }

  console.log('Fetching records from Notion via API...');
  const res = await fetch(`https://api.notion.com/v1/databases/${databaseId}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    }
  });

  const data = await res.json();
  if (!data.results) {
    console.error('Failed to fetch:', data);
    return;
  }

  console.log(`Clearing ASIN for ${data.results.length} records...`);
  for (const page of data.results) {
    const updateRes = await fetch(`https://api.notion.com/v1/pages/${page.id}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        properties: {
          'ASIN': {
            rich_text: [],
          },
        },
      })
    });

    if (updateRes.ok) {
      console.log(`✅ Cleared ASIN for: ${page.id}`);
    } else {
      const err = await updateRes.json();
      console.error(`❌ Failed: ${page.id}`, err);
    }
    // Rate limit
    await new Promise(r => setTimeout(r, 334));
  }
  console.log('All ASINs cleared!');
}

clearAllAsins().catch(console.error);
