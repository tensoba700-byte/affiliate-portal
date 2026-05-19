# GA4 (Google Analytics 4) Data Integration Report

本レポートは、Antigravityで行われたGA4データ連携の設定内容、解決された不具合、および今後の利用手順を他モデル（Claude等）と共有できるように整理したドキュメントです。

---

## 📋 1. 設定ステータス

* **接続状態**: **連携完了（接続テスト成功）**
* **GA4 プロパティID**: `532508021`
* **GA4 測定ID**: `G-6SXHM8M2BJ`
* **対象サイト**: `https://mikke-style.com`
* **認証サービスアカウント**: `ga4-reader@gen-lang-client-0234162974.iam.gserviceaccount.com`

---

## 🛠️ 2. 実施した内容と解決した不具合

### ① 認証情報のセキュリティ保護と設定
* **秘密鍵の保存**: 
  Google CloudからダウンロードしたJSONキーを [credentials/ga4-key.json](file:///Users/tsukika/Desktop/affiliate-portal/credentials/ga4-key.json) としてローカルに安全に保存しました。
* **情報漏洩対策**: 
  セキュリティ保護のため、[.gitignore](file:///Users/tsukika/Desktop/affiliate-portal/.gitignore) の末尾に以下を追記し、キーファイルがGitHubにプッシュされないよう除外しました。
  ```gitignore
  # credentials
  /credentials/
  ```
* **環境変数の登録**: 
  [/.env.local](file:///Users/tsukika/Desktop/affiliate-portal/.env.local) に以下の環境変数を設定しました。
  ```env
  GA4_PROPERTY_ID=532508021
  GA4_CREDENTIALS_PATH=credentials/ga4-key.json
  ```

### ② GA4管理画面UIの制限による登録エラーの回避（突破）
* **問題点**: 
  GA4のアクセス管理画面UIからサービスアカウントを追加しようとすると、「このメールアドレスは Google アカウントと一致しません」エラーで登録できない（UI側の制限）。
* **解決策**: 
  Google公式の **OAuth 2.0 Playground** を経由し、Google Analytics Admin APIの `accessBindings` リソースを使用して直接プロパティにアクセス権限を書き込み、強制登録を成功させました。
  * **HTTP Method**: `POST`
  * **Endpoint**: `https://analyticsadmin.googleapis.com/v1alpha/properties/532508021/accessBindings`
  * **Request Body**:
    ```json
    {
      "user": "ga4-reader@gen-lang-client-0234162974.iam.gserviceaccount.com",
      "roles": ["predefinedRoles/viewer"]
    }
    ```

### ③ Google Analytics Data API の有効化
* 新しいGoogle Cloudプロジェクト（`gen-lang-client-0234162974`）内の **Google Analytics Data API** を有効化し、API経由でのメトリクス読み取りを許可しました。

---

## 💻 3. 実装したデータ取得スクリプト

GA4 Data APIを利用して、過去30日間の「ページパス」「ページビュー数 (PVs)」「アクティブユーザー数 (Users)」「直帰率 (Bounce Rate)」を取得・表示するPythonスクリプトを [scripts/fetch_ga4_data.py](file:///Users/tsukika/Desktop/affiliate-portal/scripts/fetch_ga4_data.py) に作成しました。

### **実行に必要な外部ライブラリ (インストール済み)**:
* `google-analytics-data`
* `python-dotenv`

---

## 🚀 4. スクリプトの実行方法と実行結果

### **実行手順**:
ターミナルを開き、プロジェクトのルートディレクトリに移動したうえでスクリプトを実行します。

```bash
cd ~/Desktop/affiliate-portal
python3 scripts/fetch_ga4_data.py
```

### **実際の取得データ（テスト実行結果）**:
```plain
🔄 Connecting to GA4 Property: 532508021...

📊 --- GA4 Traffic & User Engagement Report (Last 30 Days) ---
Page Path                                                    | PVs        | Users      | Bounce Rate 
----------------------------------------------------------------------------------------------------
/                                                            | 243        | 50         | 45.7%       
/articles/20260418-skincare-spring                           | 24         | 3          | 0.0%        
/articles                                                    | 22         | 3          | 5.3%        
/articles/20260507-浴室を一日の終わりの聖域にバスタイムケアグッズ6選                 | 16         | 4          | 0.0%        
/search                                                      | 15         | 3          | 0.0%        
/articles/20260420-春の新生活にぴったりのインテリアアイテム                      | 11         | 2          | 0.0%        
/articles/20260419-ps5-apple-a19-hikaku                      | 8          | 2          | 40.0%       
/articles/20260516-夜の静寂に活字が溶ける電子書籍リーダーeインクデバ                 | 5          | 2          | 0.0%        
...
Total rows fetched: 50
```

---

## 💡 5. 今後の展開（自動改善のアイデア）

GA4のリアルタイムなアクセス・ユーザー定着率のデータがプログラム上で取得できるようになったため、以下の自動化が容易に実装可能です。

1. **アクセス数に応じた自動リライト提案**:
   PV数が一定値を超えているが、直帰率が高い（例えば70%以上）の記事を自動検出し、記事冒頭のコンテンツやアイキャッチの差し替えリストを作成する。
2. **広告成果の最適化**:
   PVが上がっているにもかかわらず、アフィリエイトリンクのクリック率（別ログ）が低い記事を特定して、ボタンの配置やマイクロコピーを改善する提案を行う。
3. **人気記事のダッシュボード表示**:
   WordPressやフロントエンド側にGA4の人気ページデータを渡し、「よく読まれているおすすめ記事」を自動ランキング表示する。
