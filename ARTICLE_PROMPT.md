## 基本方針
- 情報源はstockpile_data.jsonのみ
- factsにない情報追加禁止・推測禁止・外部検索禁止・コピー禁止
- 評価表現禁止（最強・神・圧倒的・超おすすめ等）

## 記事タイプ別構成
ranking_article：FAQ最大3問
comparison_article：FAQ最大5問
single_product_article：FAQ最大2問

## 順位付け
- stockpile_data.jsonの順序を維持
- 独自評価による順位変更禁止

## 選び方
- CATEGORY_CONFIG.yamlのselection_pointsを使用
- factsで説明できる観点のみ採用
- 新しい観点を追加しない

## 商品説明
- factsのみ使用・200〜400文字・商品名を1回以上含める

## Pros
- factsから直接言える内容のみ・2〜3項目・1項目1文

## Cons
- factsから客観的に導ける場合のみ・1〜2項目
- 導けない場合は「該当情報なし」

## おすすめの人
- recommended_forをそのまま使用・推測で追加しない

## FAQ生成ルール
- FAQ_TEMPLATES.yamlのseed_questionsを参照
- factsで回答可能な質問のみ採用
- 回答できない質問は出力しない
- FAQは1〜3問（無理に3問埋めない）
- 新しい情報の追加禁止

## まとめ
- 200〜300文字・商品全体の傾向を整理・新しい情報追加禁止

## JSON出力ルール（article_draft.json）

記事生成時は必ず以下のJSONスキーマでarticle_draft.jsonに保存する。

{
  "meta": {
    "title": "記事タイトル",
    "excerpt": "80〜150文字のメタディスクリプション"
  },
  "content": {
    "intro": "200〜400文字の導入文",
    "summary": "200〜300文字のまとめ文"
  },
  "products": [
    {
      "name": "商品名",
      "description": "200〜400文字の商品説明",
      "analysis": {
        "pros": ["メリット1", "メリット2"],
        "cons": ["デメリット1"],
        "recommended_for": ["乾燥肌"]
      }
    }
  ],
  "ui": {
    "points": ["選び方1", "選び方2", "選び方3"],
    "faq": [
      {"question": "Q", "answer": "A"}
    ]
  }
}

## 生成時の必須ルール
- meta.titleが存在すること
- content.introが200〜400文字
- content.summaryが200〜300文字
- productsが1〜6件・name重複禁止
- analysis.pros/cons/recommended_forは全て配列（null禁止）
- ui.faqが1〜3件・question/answerは空文字禁止
- meta.excerptが80〜150文字
