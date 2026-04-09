import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function listAllItems() {
  const res = await fetch(`https://api.notion.com/v1/databases/${process.env.NOTION_DATABASE_ID}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.NOTION_API_KEY}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ page_size: 100 })
  });
  const data = await res.json();
  if (data.results) {
    const products = data.results.map((page: any) => ({
      id: page.id,
      name: page.properties['商品名']?.title[0]?.plain_text || 'Unknown',
      amazon: page.properties['Amazon参考URL']?.url || '',
      rakuten: page.properties['楽天参考URL']?.url || '',
      yahoo: page.properties['Yahoo参考URL']?.url || '',
    }));
    console.log(JSON.stringify(products, null, 2));
  } else {
    console.error('Error fetching items:', data);
  }
}

listAllItems();
