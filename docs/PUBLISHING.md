# 公開の手順

このリポジトリは、英語の記事（`en/`）を dev.to に、日本語の記事（`articles/`）を Zenn に出すためのものです。
当面は書きためるだけで、公開は宗像さんが「出す」と言ったときだけ行います。

## 最初に1回だけやること（宗像さん）

### 1. dev.to のAPIキー
1. dev.to にログインし、Settings → Extensions → 「DEV Community API Keys」でキーを作る（説明は「ai-engineering-notes」など）。
2. Git Bash ではなく、コマンドプロンプトかPowerShellで次を実行する（キーの値は人に見せない・ファイルに書かない）。
   ```
   setx DEVTO_API_KEY "ここにキー"
   ```
3. 開いているターミナルとClaude Codeを閉じて開き直す（setx は新しく開いた画面から有効になる）。

### 2. Zenn とリポジトリをつなぐ
1. zenn.dev にログインし、ダッシュボードの「GitHubからのデプロイ」（Deploys）を開く。
2. 「リポジトリを連携」で `sunaomunakata/ai-engineering-notes` を選ぶ（ブランチは main）。
3. 以後、main に push すると `articles/` の記事が Zenn に同期される。

注意：Zenn は front matter が `published: true` の記事だけを公開する。`published: false` の記事は下書きとして同期される。
下書きでも、GitHub のリポジトリは公開（public）なので、push した時点で本文は誰でも読める。公開すると決めるまで、記事はリポジトリに入れない。

## 1本を出すときの流れ

1. 下書き（Drive の `drafts/`）で、事実確認と言い回しの点検を済ませ、宗像さんの承認を受ける。
2. 英語版を `en/<slug>.md`、日本語版を `articles/<slug>.md` に置く。
   - 日本語版の front matter は `published: false` のまま始める（新規作成は `npx zenn new:article --published false` でも可）。
3. 点検：
   ```
   python -I tools/check_post.py en/<slug>.md articles/<slug>.md
   python -I tools/wording_lint.py en/<slug>.md articles/<slug>.md
   ```
4. 日本語版：front matter を `published: true` にして、コミットし push する（Zenn に出る）。
5. 英語版：コミットして push し、GitHub に正本のURLができてから dev.to に出す。
   ```
   python -I tools/publish_devto.py en/<slug>.md --dry-run    # 送る内容の確認（何も送らない）
   python -I tools/publish_devto.py en/<slug>.md              # dev.to に下書きとして作る
   python -I tools/publish_devto.py en/<slug>.md --publish    # 公開する（承認の後だけ）
   ```
   - canonical_url が空なら、GitHub のファイルのURL（`.../blob/main/en/<slug>.md`）を入れて送る。
   - 送れたら、front matter に `devto_id` と `devto_url` が書き戻される。これをコミットして push する。
   - `devto_id` があれば、次からは同じ記事の更新になる。
   - 終了コード：0 成功、1 点検・入力の誤り、2 dev.to API の誤り。
6. `published.csv` と `backlog.md` を更新する。

## プレビュー（任意）
`npm install` の後、`npm run preview` で Zenn の見た目をローカルで確かめられる。
