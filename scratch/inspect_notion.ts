import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.env.NOTION_DATABASE_ID!;

async function main() {
  try {
    const response = await notion.databases.query({
      database_id: databaseId,
      filter: {
        or: [
          {
            property: 'Name',
            title: {
              contains: '3Dアートペン',
            },
          },
          {
            property: 'Name',
            title: {
              contains: '日常に心地よさを',
            },
          },
        ]
      }
    });

    console.log(`Found ${response.results.length} pages`);
    for (const page of response.results as any[]) {
      console.log('--- Page ---');
      console.log('ID:', page.id);
      console.log('Status:', page.properties['ステータス 1']?.select?.name);
      console.log('Name:', page.properties['Name']?.title?.[0]?.plain_text);
      console.log('URL:', page.properties['URL']?.url);
    }
  } catch (error) {
    console.error('Error querying Notion:', error);
  }
}

main();
