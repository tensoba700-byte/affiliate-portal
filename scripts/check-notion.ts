import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const databaseId = process.env.NOTION_DATABASE_ID!;

async function checkStructure() {
  try {
    const response = await notion.databases.retrieve({ database_id: databaseId }) as any;
    console.log('--- FULL DATABASE RESPONSE ---');
    console.log(JSON.stringify(response, null, 2));
    if (response.properties) {
      console.log('Properties keys:', Object.keys(response.properties));
    } else {
      console.log('No properties found in response. Is this a database ID?');
    }
    console.log('---------------------------');
  } catch (error) {
    console.error('Error retrieving database structure:', error);
  }
}

checkStructure();
