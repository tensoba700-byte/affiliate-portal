import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function updateProductUrls(pageId: string, name: string, amazon: string, rakuten: string, yahoo: string) {
  const res = await fetch(`https://api.notion.com/v1/pages/${pageId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${process.env.NOTION_API_KEY}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      properties: {
        'Amazon参考URL': { url: amazon || null },
        '楽天参考URL': { url: rakuten || null },
        'Yahoo参考URL': { url: yahoo || null },
      }
    })
  });
  const data = await res.json();
  if (data.id) {
    console.log(`✅ Updated: ${name}`);
  } else {
    console.error(`❌ Failed: ${name}`, JSON.stringify(data));
  }
}

const products = [
  // Sony WH-1000XM5 (4件)
  {
    id: '33dddb45-8772-8160-bd33-feb25cc9060d',
    name: 'Sony WH-1000XM5',
    amazon: 'https://www.amazon.co.jp/dp/B09Z2QYYD1',
    rakuten: 'https://item.rakuten.co.jp/sokutei/4548736132566/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Sony+WH-1000XM5',
  },
  {
    id: '33dddb45-8772-8163-b70a-c0672c586675',
    name: 'Sony WH-1000XM5 (2)',
    amazon: 'https://www.amazon.co.jp/dp/B09Z2QYYD1',
    rakuten: 'https://item.rakuten.co.jp/sokutei/4548736132566/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Sony+WH-1000XM5',
  },
  {
    id: '33dddb45-8772-81a3-b131-e93e80ffeb2e',
    name: 'Sony WH-1000XM5 (3)',
    amazon: 'https://www.amazon.co.jp/dp/B09Z2QYYD1',
    rakuten: 'https://item.rakuten.co.jp/sokutei/4548736132566/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Sony+WH-1000XM5',
  },
  {
    id: '33dddb45-8772-81b7-973f-ef617ea519c2',
    name: 'Sony WH-1000XM5 (4)',
    amazon: 'https://www.amazon.co.jp/dp/B09Z2QYYD1',
    rakuten: 'https://item.rakuten.co.jp/sokutei/4548736132566/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Sony+WH-1000XM5',
  },
  // Logitech MX Master 3S (2件)
  {
    id: '33dddb45-8772-81d0-8a44-e933db9394f3',
    name: 'Logitech MX Master 3S (1)',
    amazon: 'https://www.amazon.co.jp/dp/B09RV9NKG4',
    rakuten: 'https://item.rakuten.co.jp/logicool/mx2300gr/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Logicool+MX+Master+3S',
  },
  {
    id: '33dddb45-8772-81fa-b2ad-f53633f89936',
    name: 'Logitech MX Master 3S (2)',
    amazon: 'https://www.amazon.co.jp/dp/B09RV9NKG4',
    rakuten: 'https://item.rakuten.co.jp/logicool/mx2300gr/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Logicool+MX+Master+3S',
  },
  // Apple Watch Series 10 (4件)
  {
    id: '33dddb45-8772-815b-8f33-fd66975a8f71',
    name: 'Apple Watch Series 10 42mm (1)',
    amazon: 'https://www.amazon.co.jp/dp/B0DGJWSHJ5',
    rakuten: 'https://search.rakuten.co.jp/search/mall/Apple+Watch+Series+10+42mm/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Apple+Watch+Series+10+42mm',
  },
  {
    id: '33dddb45-8772-8194-a482-f8ff3ff5a953',
    name: 'Apple Watch Series 10 42mm (2)',
    amazon: 'https://www.amazon.co.jp/dp/B0DGJWSHJ5',
    rakuten: 'https://search.rakuten.co.jp/search/mall/Apple+Watch+Series+10+42mm/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Apple+Watch+Series+10+42mm',
  },
  {
    id: '33dddb45-8772-81a5-a6b4-e032120215d3',
    name: 'Apple Watch Series 10 (1)',
    amazon: 'https://www.amazon.co.jp/dp/B0DGJWSHJ5',
    rakuten: 'https://search.rakuten.co.jp/search/mall/Apple+Watch+Series+10/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Apple+Watch+Series+10',
  },
  {
    id: '33dddb45-8772-81f0-a5a9-c76c40274709',
    name: 'Apple Watch Series 10 (2)',
    amazon: 'https://www.amazon.co.jp/dp/B0DGJWSHJ5',
    rakuten: 'https://search.rakuten.co.jp/search/mall/Apple+Watch+Series+10/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Apple+Watch+Series+10',
  },
  // HHKB (2件)
  {
    id: '33dddb45-8772-81af-825a-e09606d91540',
    name: 'HHKB Professional HYBRID Type-S (1)',
    amazon: 'https://www.amazon.co.jp/dp/B082TXN9R8',
    rakuten: 'https://item.rakuten.co.jp/pfudirect/hhkb_hybrid_s_jpn_b/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=HHKB+Professional+HYBRID+Type-S',
  },
  {
    id: '33dddb45-8772-81ee-8897-cbdc36432abd',
    name: 'HHKB Professional HYBRID Type-S (2)',
    amazon: 'https://www.amazon.co.jp/dp/B082TXN9R8',
    rakuten: 'https://item.rakuten.co.jp/pfudirect/hhkb_hybrid_s_jpn_b/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=HHKB+Professional+HYBRID+Type-S',
  },
  // Anker Nano II 65W (3件)
  {
    id: '33dddb45-8772-814a-ae76-db0593189cc1',
    name: 'Anker Nano II 65W (1)',
    amazon: 'https://www.amazon.co.jp/dp/B091KKG869',
    rakuten: 'https://item.rakuten.co.jp/anker/a2663/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Anker+Nano+II+65W',
  },
  {
    id: '33dddb45-8772-8178-8e78-c89ee716e30a',
    name: 'Anker Nano II 65W (2)',
    amazon: 'https://www.amazon.co.jp/dp/B091KKG869',
    rakuten: 'https://item.rakuten.co.jp/anker/a2663/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Anker+Nano+II+65W',
  },
  {
    id: '33dddb45-8772-81f9-b9fd-ec7a59ad2c6f',
    name: 'Anker Nano II 65W (3)',
    amazon: 'https://www.amazon.co.jp/dp/B091KKG869',
    rakuten: 'https://item.rakuten.co.jp/anker/a2663/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=Anker+Nano+II+65W',
  },
  // BenQ ScreenBar Halo (2件)
  {
    id: '33dddb45-8772-819a-ac4d-f21b825e44ee',
    name: 'BenQ ScreenBar Halo (1)',
    amazon: 'https://www.amazon.co.jp/dp/B09J53T73J',
    rakuten: 'https://item.rakuten.co.jp/benq-store/screenbar-halo/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=BenQ+ScreenBar+Halo',
  },
  {
    id: '33dddb45-8772-81ca-914a-cdc336c5090c',
    name: 'BenQ ScreenBar Halo (2)',
    amazon: 'https://www.amazon.co.jp/dp/B09J53T73J',
    rakuten: 'https://item.rakuten.co.jp/benq-store/screenbar-halo/',
    yahoo: 'https://shopping.yahoo.co.jp/search?p=BenQ+ScreenBar+Halo',
  },
];

async function main() {
  console.log(`Updating ${products.length} Notion records with clean URLs...`);
  for (const p of products) {
    await updateProductUrls(p.id, p.name, p.amazon, p.rakuten, p.yahoo);
    await new Promise(r => setTimeout(r, 300)); // Rate limit
  }
  console.log('All done!');
}

main();
