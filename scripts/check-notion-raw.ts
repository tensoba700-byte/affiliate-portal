import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function getStructure() {
  const res = await fetch(`https://api.notion.com/v1/databases/${process.env.NOTION_DATABASE_ID}`, {
    headers: {
      'Authorization': `Bearer ${process.env.NOTION_API_KEY}`,
      'Notion-Version': '2022-06-28'
    }
  });
  const data = await res.json();
  console.log('--- DATABASE STRUCTURE ---');
  if (data.properties) {
    console.log(Object.keys(data.properties));
    console.log(JSON.stringify(data.properties, null, 2));
  } else {
    console.log('Error:', data);
  }
}

getStructure();
