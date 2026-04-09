import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.env.NOTION_DATABASE_ID!;

async function checkFinal() {
  try {
    const response = await notion.databases.retrieve({ database_id: databaseId });
    console.log('--- PROPERTY KEYS ---');
    console.log(Object.keys(response.properties).join(', '));
    console.log('---------------------');
  } catch (error) {
    console.error('Error:', error);
  }
}

checkFinal();
