# Notion Content Generation Rules

This document outlines the rules for automated content generation and database management for the "Mikke!" affiliate portal.

## Database Management

### Publication Workflow
1. **Article Identification**: Articles are identified in Notion's "みっけ！記事管理" database by their **記事タイトル** (Article Title).
2. **Generation & Deployment**: Once an article is processed and pushed to GitHub:
   - The markdown file is saved to `src/content/articles/`.
   - The eyecatch image is saved to `public/eyecatch/`.
3. **Database Cleanup**:
   - **RULE**: Immediately after pushing a new article to GitHub, all product entries associated with that article title MUST be deleted (archived) from the Notion database to maintain a clean workspace and prevent duplicate publications.

---
*Created on 2026-04-13*
