# 引き継ぎ書

最終更新：2026-04-29

別セッションから引き継ぐ場合、このドキュメントと `REQUIREMENTS.md` を最初に読んでください。

---

## これまでの経緯

### きっかけ
オーナーが MakeAI_CEO mana 氏のXポスト（https://x.com/MakeAI_CEO/status/2045357049060753490）を見て興味を持った。Claude Code に参考動画を渡せば似たようなショート動画を作れるという内容。

会社からこのシステムを作るよう依頼された。

### 検討の流れ

1. **Hyperframesの記事を読んだ**
   - X記事を Playwright + Cookie認証で全文取得
   - `/Users/kosukeitamoto/projects/john/memory/howto/hyperframes_guide.md` に保存済み
   - HTML→動画化のフレームワーク

2. **テスト動画を作った**
   - `/Users/kosukeitamoto/projects/john/my-first/` に5秒のテストアニメ
   - GSAP + Hyperframes で動作確認済み

3. **「筋トレ.mp4」みたいな動画作れる？という相談**
   - 結論：プロンプト一発では無理、地道な工数とガチャが必要
   - image-to-video AI（Sora 2 / Veo 3 / Kling 2.1 / Seedance / Hailuo）を比較
   - fal.ai が便利な統一API窓口だと判明

4. **会社の人への説明文を作成**
   - 「結論：完全再現は厳しいけど、地道に作れば可能」という方向で
   - 「全く同じで」進める方針が確定

5. **要件定義（このドキュメントの直前のステップ）**
   - パターンA（完全自動・品質妥協）を選択
   - 「全く同じ」方針で著作権リスク承知のうえ進行
   - video-clone プロジェクトとして john ディレクトリから分離

---

## 現在の状態

### 完了済み
- ✅ プロジェクトディレクトリ作成（`/Users/kosukeitamoto/projects/video-clone/`）
- ✅ 要件定義書（`REQUIREMENTS.md`）
- ✅ CLAUDE.md（プロジェクト指示書）
- ✅ HANDOVER.md（このドキュメント）
- ✅ git init & GitHub公開リポジトリ作成（https://github.com/iittaa/video-clone）
- ✅ .gitignore 作成
- ✅ 全未決事項を確定（2026-04-29）
  - 動画生成AI: Seedance 1.5 Pro（fal.ai）
  - キャラ一貫性: B（ゆるく頑張る）
  - 失敗判定: A（全部出す）
  - 量: 月30本生成（約$100/月）
  - BGM: フリー素材から選択

### 未着手
- ⬜ pyproject.toml（uv で初期化）
- ⬜ .env.example テンプレート
- ⬜ 開発環境のセットアップ（venv作成）
- ⬜ APIキー取得（OpenAI / fal.ai）
- ⬜ 実装開始

---

## 次にやること（候補）

優先度高い順：

### 1. プロジェクト初期化（実施中）
- 言語：Python（uv で管理）
- pyproject.toml 作成
- `.env.example` 作成
- 仮想環境セットアップ

### 2. APIキー取得（オーナー作業）
- OpenAI（GPT-4 Vision、GPT Image 2.0、Whisper、TTS）
- fal.ai（動画生成AI窓口）

### 3. Phase 1 実装着手
- yt-dlp で動画ダウンロード
- 動画解析パートから着手

---

## オーナーの好み・ルール

### 話し方
- タメ口でOK、敬語不要
- 絵文字使う、「。」で終わらせない

### 出力
- 結論ファースト
- 箇条書き中心
- 長文は `pbcopy` で自動クリップボード送信
- 丸付き数字（①②③）は使わない

### プロジェクト分離
- このプロジェクト（video-clone）には秘書系のmemoryは作らない
- 秘書ジョンの memory は `/Users/kosukeitamoto/projects/john/` 側

---

## 関連ファイル一覧

### このディレクトリ
- `REQUIREMENTS.md` — 要件定義書（必読）
- `CLAUDE.md` — Claude向けプロジェクト指示書

### john プロジェクト側
- `/Users/kosukeitamoto/projects/john/CLAUDE.md` — ジョン本体の設定
- `/Users/kosukeitamoto/projects/john/memory/howto/hyperframes_guide.md` — Hyperframes記事全文
- `/Users/kosukeitamoto/projects/john/memory/decisions/video_clone_system_risk.md` — 「全く同じ」方針の決定経緯
- `/Users/kosukeitamoto/projects/john/my-first/index.html` — Hyperframesテスト動画
- `/Users/kosukeitamoto/projects/john/my-first/john-online.mp4` — レンダリング済みテスト動画

### 参考リソース
- 元ポスト：https://x.com/MakeAI_CEO/status/2045357049060753490
- 参考動画例：`/Users/kosukeitamoto/Desktop/筋トレ.mp4`（オーナーのデスクトップ）

---

## セッション開始時のチェックリスト

新しいセッションを開始したら：

1. このファイル（HANDOVER.md）を読む
2. CLAUDE.md を読む
3. REQUIREMENTS.md を読む
4. オーナーに「video-cloneセッション開始しました！次は何やる？」と挨拶
5. 上記の「次にやること」から進める
