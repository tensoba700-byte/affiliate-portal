import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.env.NOTION_DATABASE_ID!;

async function checkSample() {
  try {
    const response = await notion.databases.query({ database_id: databaseId, page_size: 1 });
    console.log('--- SAMPLE ITEM PROPERTIES ---');
    if (response.results.length > 0) {
      const item = response.results[0] as any;
      console.log(JSON.stringify(item.properties, null, 2));
    } else {
      console.log('No results found in database query.');
    }
    console.log('---------------------------');
  } catch (error) {
    console.error('Error querying database:', error);
  }
}

checkSample();
