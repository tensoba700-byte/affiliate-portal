# Notion Content Generation Rules

This document outlines the rules for automated content generation and database management for the "Mikke!" affiliate portal.

## Database Management

### Publication Workflow
1. **Article Identification**: Articles are identified in Notion's "みっけ！記事管理" database by their **記事タイトル** (Article Title).
2. **Generation & Deployment**: Once an article is processed and pushed to GitHub:
   - The markdown file is saved to `src/content/articles/`.
   - The eyecatch image is saved to `public/eyecatch/`.

## Article Planning & Creation Workflow

Follow these steps when planning and creating new article entries in Notion:

### 1. Trend Analysis
- Read the last 7 days of 「AI新聞」 (AI Newspaper) in Notion to identify current trends before deciding on a theme.

### 2. Determine Theme & Target
- Decide on a specific theme and target audience.
- *Example*: 「忙しいママ向け時短家電」, 「一人暮らし向けガジェット」.

### 3. Product Research & Verification
- Research 5-7 products that fit the chosen theme.
- **Genre Consistency**: All products must belong to the same genre.
- **Accurate Naming**: Write the name precisely as `[Manufacturer] [Product Name] [Model Number]`.
  - *Example*: 「パナソニック ヘアードライヤー ナノケア EH-NA0J」
  - If the model number is unknown, use `[Manufacturer] [Product Name]`.
- **Verification**: Always perform a web search to confirm the product exists and the name/model number is accurate before writing to Notion.

### 4. Finalize Title & Register to Notion
- Determine the article title **only after** the product list is finalized.
- Register the following properties in the 「みっけ！記事管理」 database:
  - **記事タイトル** (Article Title)
  - **商品名** (Accurate Product Name)
  - **カテゴリ** (Category)
  - **ステータス 1** (Status): Set to **未処理** (Unprocessed).

---
*Updated on 2026-04-14*
