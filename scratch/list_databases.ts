import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });

async function main() {
  try {
    const response = await notion.search({});
    console.log(`Found ${response.results.length} objects:`);
    for (const obj of response.results as any[]) {
      if (obj.object !== 'database') continue;
      console.log(`- Title: ${obj.title?.[0]?.plain_text || 'Untitled'} | ID: ${obj.id}`);
      console.log('  Properties:', Object.keys(obj.properties).join(', '));
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
