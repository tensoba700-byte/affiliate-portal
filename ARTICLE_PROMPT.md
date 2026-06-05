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
