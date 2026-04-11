import { Client } from '@notionhq/client';

let notionClient: Client | null = null;

function getNotionClient() {
  if (!notionClient) {
    notionClient = new Client({
      auth: process.env.NOTION_API_KEY,
    });
  }
  return notionClient;
}

const getDatabaseId = () => process.env.NOTION_DATABASE_ID!;

export interface NotionProductData {
  articleTitle: string;
  name: string;
  category: string;
  amazonUrl: string;
  rakutenUrl: string;
  yahooUrl: string;
  status: string;
}

/**
 * Notionの「みっけ！記事管理」データベースに新しい商品レコードを追加します。
 */
export async function addProductToNotion(data: NotionProductData) {
  try {
    const response = await getNotionClient().pages.create({
      parent: { database_id: getDatabaseId() },
      properties: {
        '記事タイトル': {
          rich_text: [
            {
              text: {
                content: data.articleTitle,
              },
            },
          ],
        },
        '商品名': {
          title: [
            {
              text: {
                content: data.name,
              },
            },
          ],
        },
        /* ASINは使用しない
        'ASIN': {
          rich_text: [
            {
              text: {
                content: '',
              },
            },
          ],
        },
        */
        'カテゴリ': {
          select: {
            name: data.category || '未分類',
          },
        },
        'ステータス 1': {
          select: {
            name: '未処理',
          },
        },
      },
    });
    return response;
  } catch (error) {
    console.error(`Notion sync error for "${data.name}":`, error);
    throw error;
  }
}
