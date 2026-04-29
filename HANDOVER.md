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
- ✅ プロジェクト初期化（uv + Python 3.12、依存パッケージ追加）
- ✅ APIキー設定（OpenAI / fal.ai を `.env` にローカル保存、gitignore済み）
- ✅ Phase 1 実装完了（download / transcribe / analyze）
- ✅ Phase 2 実装完了（generate-character / generate-clip / synthesize）
- ✅ Phase 3 実装完了（compose、HyperFrames経由）

### 動作確認済み（2026-04-29時点）
- ✅ transcribe（筋トレ.mp4 → 約1円）
- ✅ analyze（GPT-4o low detail、約2円）
- ✅ generate-character（gpt-image-1 low、約2円）
- ✅ synthesize（gpt-4o-mini-tts + nova、1円未満）

### 動作確認未実施
- ⏳ generate-clip（fal.ai 残高ゼロでロック中、要チャージ）
- ⏳ compose（クリップ生成後の通しテスト）

### 未着手
- ⬜ パイプライン統合コマンド（`clone <URL>` で全工程実行）
- ⬜ BGM パート（フリー素材選定・取得・合成）

---

## 既知の注意点

### fal.ai の残高
- 2026-04-29時点でアカウント残高ゼロ → ロック状態
- 解除には https://fal.ai/dashboard/billing でチャージ
- 5秒1本=$0.26、テスト最低$5、本格運用月$78想定

### `.env` の優先度
- ローカル環境に既存の `OPENAI_API_KEY` があると競合する
- `load_dotenv(override=True)` で `.env` 優先になるよう実装済み

### ffprobe 不在対応
- システムに ffmpeg はあるが ffprobe が無い環境向けに、ffmpeg stderr から動画長を正規表現で取得する実装にしている

---

## CLI コマンド一覧

```
uv run main.py download <URL>                       # yt-dlp で動画DL
uv run main.py transcribe <video_path>              # Whisper 書き起こし
uv run main.py analyze <video_path> [--transcript]  # GPT-4o 構成解析
uv run main.py generate-character <analysis_json>   # GPT Image でキャラ画像
uv run main.py generate-clip <analysis_json> -i N   # Seedance で1カット生成
uv run main.py synthesize <transcript_json>         # TTS でナレーション
uv run main.py compose <analysis_json>              # HyperFrames で最終合成
```

### 標準出力先
- `cache/videos/<id>.mp4` — DL動画
- `cache/transcripts/<stem>.json` — 書き起こし
- `cache/analysis/<stem>.json` — 構成解析
- `cache/images/<stem>/character.png` — キャラ画像
- `cache/clips/<stem>/NNN.mp4` — カット動画
- `cache/audio/<stem>/voiceover.mp3` — ナレーション
- `cache/compositions/<stem>/index.html` — HyperFrames composition
- `output/<stem>.mp4` — 最終MP4

---

## 次にやること（候補）

優先度高い順：

### 1. fal.ai 課金 → 動画クリップ生成テスト（オーナー作業）
- https://fal.ai/dashboard/billing で最低 $5 チャージ
- `uv run main.py generate-clip cache/analysis/筋トレ.json -i 0` で1カット生成テスト
- 5秒1本=約40円

### 2. パイプライン統合コマンド `clone <URL>` 追加
- download → transcribe → analyze → generate-character → generate-clip × N → synthesize → compose を1コマンドで実行
- 「URL入れたらボタン1つで動画完成」の要件達成
- main.py に追加するだけ、各機能は既に実装済み

### 3. 全カット生成 → compose で初の通しテスト
- 解析結果10カット分の generate-clip を実行（合計約400円）
- compose で繋ぎ合わせ → output/筋トレ.mp4 が初のクローン動画
- 失敗動画は判定なし全部出す（要件A）

### 4. 細部の調整
- TTS の声・話し方を品質見て切替（gpt-4o-mini-tts → ElevenLabs 等）
- BGM パート（フリー素材選定）
- カット間トランジションの改善（現状は0.3秒クロスフェード）
- キャラ一貫性の昇格（B → C / Reference Image運用、必要なら）

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
