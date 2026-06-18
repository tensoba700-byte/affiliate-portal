# Gemini使用状況 監査レポート（変更なし・報告のみ）

調査日: 2026-06-18
対象: リポジトリ全体の `genai` / `GenerativeModel` / `generate_content` 呼び出し箇所

---

## A. 5ファイルの詳細分類

### 1. `discord-bot/index.js` — ★最重大の違反

`!audit-latest` コマンド（48-86行目）が、`validate_article_draft.py` の検証パイプラインを完全にバイパスして記事本文を直接書き換えている。

```js
const fixPrompt = '...商品数は必ず6個に固定...「👑 第N位」は使用禁止...
スペック表を必ず追加する...禁止ワード（劇的、おすすめ〇選、ランキング、人気など）は絶対に使わない...
現在の記事:\n' + content;

const result = await model.generateContent(fixPrompt);
const fixedContent = result.response.text();
await updateGitHubFile(filePath, fixedContent, sha); // ← 検証なしで直接GitHub上書き
```

- ARTICLE_PROMPT.mdではなく独自の `GENERATION_RULES.md` / `title-quality.md` という別ルールを参照しており、現行のARTICLE_PROMPT.mdと内容が同期していない可能性がある。
- 生成後、`validate_article_draft.py` を一切通さず `main` ブランチへ直接PUT。文字数チェック・禁止語チェック・口語チェックが効かない。
- **本文の全面書き換え＝禁止されている使い方。**

### 2. `taro-discord-bot.py` — 直push経路

`run_article_generation()`（109-196行目）：`scripts/generate_from_competitor.py` を呼び、`GITHUB_TOKEN` が設定されていればその場で `git add/commit/push` を**直接mainブランチへ**実行。レビューや `publish_article.py` 経由のフローを経ない。

- Gemini自体はここでは直接呼ばれておらず、`generate_from_competitor.py`（未調査）に処理を委譲している。違反の有無はそのスクリプト次第だが、**「Discordから直接mainに自動push」という経路自体がリスク**。
- `run_scheduled_publishing()` は `GITHUB_TOKEN` がある場合スキップされ、ない場合は存在しない `auto_publish_batch.py` を呼んで失敗する（既報告の通り死んだコード）。

### 3. `bot.py` — チャット/オーケストレーション用途、Gemini使用は許容範囲

`genai.GenerativeModel(model_name='gemini-3-flash-preview', ...)` はMCPツール呼び出し付きの汎用チャットループ（最大10ターン）。`!generate` / `記事生成して` は `python -m auto_generator.main` を、`!公開` / `!publish` は `scripts/publish_article.py` を**サブプロセスで呼ぶだけ**で、Gemini自身が本文を書いていない。違反なし（ただし `auto_generator.main` は内容未確認）。

### 4. `discord-bot/product-bot.js` — 商品選定のみ、違反なし

`product_selection_prompt.txt`（ARTICLE_PROMPT.mdとは別ファイル）をsystemInstructionに使用。出力は `name/model/articleTitle/reason/category/publishTime` 等のJSONで、記事本文ではなく**商品選定情報**。`addToNotion()` はコード内にあるが、メッセージハンドラからは呼ばれておらず未使用（デッドコード）。汎用チャット転送機能（90-94行目）は本文生成には繋がらない。

---

## B. `scripts/cron_column_pipeline.py` 調査結果

### 1. 作成日

```
ba22d40 2026-06-12 16:43:34 +0900  feat: generate weekly columns and setup pipeline
```

唯一のコミット＝作成と同時に初回実行された形跡（後述）。

### 2. Geminiプロンプトの内容 — 明確な違反

- `select_themes()`：テーマ案14本を生成（創作・グレーゾーン）
- `get_facts_for_theme()`：競合記事から事実抽出（197行目まで準拠）だが、**事実が取れない場合のフォールバック**（200-226行目）でGemini自身の知識から事実を「生成」している（外部ソースなしの創作＝抽出ではない）
- **`generate_column_draft()`（246-271行目）— 本文を直接Geminiに書かせている：**

```python
prompt = f"""あなたは、仕事も趣味も忙しい美容オタク女子ライターです。
親しみやすく崩したブログ口調で、読者に寄り添うように美容知識コラムを執筆してください。
...
{facts_str}
...
出力するJSONは、以下のスキーマ構造に100%適合させてください。
{schema_content}
"""
model = genai.GenerativeModel("models/gemini-2.5-pro")
```

- **`fix_draft_with_gemini()`（299-336行目）もバリデーション失敗時に本文を再生成** — `cron_article_pipeline_master.py`（削除済み）と同じ「Geminiに本文を書かせる→バリデータでリトライ」構造で、**同種の違反**。

### 3. 呼び出し経路 — どこからも呼ばれていない

リポジトリ全体を `cron_column_pipeline` で検索したが、Discord bot・GitHub Actions workflow（`auto-publish.yml` はNote.com投稿用で無関係）・他スクリプトのいずれからも参照ゼロ。crontab設定ファイルもリポジトリ内に存在しない（このサンドボックスの `crontab -l` はおこげの実機とは無関係なので確認不可、という限界は継続）。

### 4. 公開済みコラム記事 — 16件中15件が1回のバッチ実行

```
b1d25e0  2026-06-12 08:52  col-june-uv-care.md          (別コミット、機能追加の一部)
ba22d40  2026-06-12 16:43  col-aging-care-when-to-start.md
                            col-booster-how-to-use.md
                            col-cleanser-how-to-foam.md
                            col-cleansing-balm-emulsification.md
                            col-cleansing-gel-how-to.md
                            col-cleansing-oil-frictionless.md
                            col-face-cream-how-to-choose.md
                            col-hair-treatment-time.md
                            col-lip-serum-difference.md
                            col-mens-skincare-basic.md
                            col-night-skincare-sleep.md
                            col-redness-sensitive-skin.md
                            col-skin-barrier-care.md
                            col-toner-application-method.md
                            col-year-round-uv-care.md
                            （15件、1コミットにまとめてpush）
```

### 結論

`cron_column_pipeline.py` は名前に反して定期実行（cron）として組み込まれた形跡がなく、2026-06-12に**1回ローカルで手動実行され、15本のコラムを一括生成・push**した形跡のみ。本文生成は `cron_article_pipeline_master.py` と同じ「Geminiに直接本文を書かせる」違反構造を持っている。

---

**本レポート作成時点で変更は一切行っていません（report only）。**
