import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function findDb() {
  try {
    const response = await notion.search({
      query: 'みっけ！記事管理',
      filter: { property: 'object', value: 'database' },
    });
    console.log('--- SEARCH SEARCH ---');
    if (response.results.length > 0) {
      const db = response.results[0] as any;
      console.log('DB ID:', db.id);
      console.log('Properties keys:', Object.keys(db.properties));
      console.log('Detailed Properties:', JSON.stringify(db.properties, null, 2));
    } else {
      console.log('Database not found in search.');
    }
  } catch (error) {
    console.error('Search error:', error);
  }
}

findDb();
