# Notion Content Generation Rules

This document outlines the rules for automated content generation and database management for the "Mikke!" affiliate portal.

## Database Management

### Publication Workflow
1. **Article Identification**: Articles are identified in Notion's "みっけ！記事管理" database by their **記事タイトル** (Article Title).
2. **Generation & Deployment**: Once an article is processed and pushed to GitHub:
   - The markdown file is saved to `src/content/articles/`.
   - The eyecatch image is saved to `public/eyecatch/`.

## Article Planning & Creation Workflow

### 1. Trend Analysis
- Identify current trends before deciding on a theme.

### 2. Determine Theme & Target
- Decide on a specific theme and target audience.
- *Example*: 「忙しいママ向け時短家電」, 「一人暮らし向けガジェット」.

### 3. Product Research & Verification
- Research 5-7 products that fit the chosen theme.
- **Accurate Naming**: Write the name precisely as `[Manufacturer] [Product Name] [Model Number]`.

## Article Content & Style Rules (Updated 2026-05-17)

### 1. Writing Style (Brand Voice)
- **Format**: **Parallel Selection** (Parallel list). **DO NOT use rankings** or "1st Place", "2nd Place", etc.
- **Product Count**: **Exactly 6 items**. (商品数は必ず**6個**に固定してください。)
- **Tone**: Professional yet friendly. Neutral and reliable.
- **Persona**: NO persona (remove "Okoge"). No first-person experience or anecdotes.
- **Language Constraints**:
    - **Forbidden Words**: 「マジで」, 「ヤバい」, 「神アイテム」, 「最高」, 「究極」, etc.
    - **Emojification**: Limit emoji usage to **1-2 emojis per product** across headings and description. Do not over-decorate.
- **Product Descriptions**:
    - **Length**: **1000+ characters** per product. Describe features, usability, and benefits in detail.
    - **Paragraph Breaks**: Divide the description into paragraphs of **2-3 sentences each**, inserting a blank line (`\n\n`) between them for mobile readability.
    - **Recommended for**: Provide a 3-point bulleted list of why this product is recommended for specific users.

### 2. Layout & Formatting
- **PR Disclosure**: Include a PR disclosure (`<p class="pr-disclosure">※本記事はアフィリエイト広告を含みます。</p>`) at the **very bottom of the summary section** (## 💬 まとめ), NOT at the top.
- **Headings**: Use `### 🌸 [Product Name]` format for product sections.
- **Buttons**: Use the following button text:
    - `Amazonで価格を見る`
    - `楽天市場で価格を見る`
    - `Yahoo!で価格を見る`
- **Exclusions**:
    - NO star ratings.
    - NO comparison tables.
    - NO pros/cons boxes.

### 3. Eyecatch Design Rules
- **Canvas Size**: 1200 x 630 px.
- **Background**: Solid White.
- **Layout**: Grid-based arrangement of product images.
- **Typography**: Large, centered title with 65% opacity white box.

### 4. Affiliate Links
- 記事生成時にAmazon・楽天・YahooのURLは必ずNotionから読み取った値をそのまま使って。
- 絶対に自分でURLを生成・変更しない。
- Notionの値：
    - Amazon Affiliate URL → そのままAmazonボタンのリンクに使う
    - Rakuten Affiliate URL → そのまま楽天ボタンのリンクに使う
    - Yahoo Affiliate URL → そのままYahooボタンのリンクに使う

---
*Updated on 2026-05-01*