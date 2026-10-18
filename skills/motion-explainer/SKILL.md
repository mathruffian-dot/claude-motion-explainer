---
name: motion-explainer
description: 用自然語言做「原理解說動畫影片」的端到端流程（HyperFrames + 中文旁白 + 字幕 + 三色主題 + 自我審查），產出可直接上課投影或上傳 YouTube 的 MP4。只要使用者要做解說動畫、科普動畫、原理動畫、教學動畫、explainer video、motion graphics 解說片，或說「上網查資料做一支解說 X 的動畫」，就一定要使用此技能。觸發情境包含：「做一個解說動畫」、「做科普影片」、「把這個原理做成動畫」、「做一支 90 秒的教學動畫」、「explain X as an animated video」。
---

# Motion explainer — 從一句話到一支解說動畫

這個技能把「上網查資料 → 寫腳本 → 中文旁白 → 一格一格做動畫 → 字幕 → 配色 → 自我審查 → 輸出 MP4」串成一條固定流程。它站在三個東西的肩膀上：

- **HyperFrames**（HeyGen 開源，HTML + GSAP 輸出 MP4）與它的官方 skills，特別是 `/hyperframes` 入口和 `/faceless-explainer` 工作流。**做法以官方為準。**
- 本 repo 的 **`motion-design`**（品味規則：緩動、節奏、停留、中文排版）與 **`review-loop`**（contact sheet 自我審查）。**好不好看以這兩個為準。**
- 本資料夾 `scripts/` 的工具：把官方流程沒處理好的中文旁白、字幕、字型一致性和三色主題補起來。

`references/lessons.md` 是實戰踩過的坑，**動工前必讀**，每一條都在第一支片裡真的發生過。

**路徑代號**：下面的指令都在專案資料夾裡執行，工具用代號指向技能資料夾。開工前先找出實際位置：

| 代號 | 是什麼 | 常見位置 |
|---|---|---|
| `<me>` | 本技能資料夾 | `~/.claude/skills/motion-explainer`（Claude Code）、`~/.agents/skills/motion-explainer`（Codex） |
| `<fe>` | HyperFrames 官方 `faceless-explainer` 技能 | `hyperframes skills update faceless-explainer` 裝的位置，通常是 `~/.agents/skills/faceless-explainer` 或 `~/.claude/skills/faceless-explainer` |
| `<review-loop>` | 本 repo 的 `review-loop` 技能 | 和 `<me>` 放在同一個 skills 資料夾 |

```bash
ls -d ~/.claude/skills/{motion-explainer,faceless-explainer,review-loop} ~/.agents/skills/{motion-explainer,faceless-explainer,review-loop} 2>/dev/null
```

PowerShell（Windows 沒有 bash 時）：

```powershell
Get-ChildItem "$HOME\.claude\skills","$HOME\.agents\skills" -Directory -ErrorAction SilentlyContinue | Select-Object FullName
```

其他 agent（例如 Gemini CLI）：在它的 skills 資料夾裡找同名資料夾。

**沒有 sub-agent 的 agent**（某些 Codex、Gemini 設定）也能跑完整個流程：第 6 節「每格派一個 sub-agent」改成自己照順序一格一格做，每格讀的檔案和順序都不變。其他步驟都是一般的終端機指令。

## 0. 環境檢查（第一次用時）

- **先跑 `python <me>/scripts/hw_check.py --project <專案>`**：它會偵測 CPU、記憶體、GPU 和硬碟，並建議要用哪個旁白引擎、`--workers` 設多少、sub-agent 要不要分批派。照 `references/hardware.md` 的說明告訴使用者；那些建議都是推估，不是跑分。
- Node.js 22+、ffmpeg/ffprobe、Python 3 + Pillow + fonttools（`pip install pillow fonttools`；裝了 `brotli` 字型會輸出成 woff2，沒裝就輸出 ttf）。
- HyperFrames CLI：`npm install -g hyperframes`，再跑 `hyperframes doctor`（Docker、Whisper、Kokoro、MusicGen 都是選配）。
- 官方 skills：`hyperframes skills update`，做這類片還要 `hyperframes skills update faceless-explainer`。裝好後找出 `<fe>` 的位置（見上方）。
- 匿名使用統計預設開啟，問使用者要不要 `hyperframes telemetry disable`。
- TTS（擇一，問使用者）：
  - **edge-tts（預設）**：`pip install edge-tts`，不需要 GPU，產生時要連網。台灣口音有 `zh-TW-HsiaoChenNeural`（女）、`zh-TW-HsiaoYuNeural`（女）、`zh-TW-YunJheNeural`（男）。
  - **Breeze TTS 2（進階）**：本機 NVIDIA GPU（約 7.7 GB VRAM，建議 12 GB 以上；模型檔約 7 GB），可以用文字描述來設計聲音，再做聲音複製，口音和情緒的控制最細。
  - 其他引擎也可以：只要能為每一句輸出 `assets/voice/raw/NN.wav`。英文片可以用 HyperFrames 內建的 Kokoro／HeyGen。

## 1. 研究（有網路搜尋時）

- 搜尋主題的最新資料，至少兩個獨立來源。數字對不上的地方要寫下來，取來源一致的那個。
- 每個數字分成三類，之後畫面上都要標：**官方宣稱**／**實測或報導**／**自己的估算**。
- 自己做簡單物理或數學估算，讓觀眾「算得出來」，那是教學片最有價值的部分。估算一定要拿現實比對（例如：「一般車最多 1.2 g」被市售車 1.8 秒破百推翻，要改成 1.5 g）。
- 不用品牌照片和 logo；主角用自己畫的示意圖，標「示意圖」。

## 2. 需求訪談（照 `/hyperframes` 的 intent layer，一次問完）

一定要確認：播放平台（決定比例：上課／YouTube → 16:9）、長度（建議 60–90 秒，旁白長度會決定實際片長）、要不要旁白（推薦要）、要不要先審分鏡、自動化還是一起邊做邊調。

**再加問三個顏色**（本技能新增），像簡報版型：
- **背景色**、**主色**（文字與線稿）、**強調色**（只給答案、結論、關鍵數字、章節卡）。
- 沒有偏好就推薦：黑底 `#121212`、白字 `#F2F0EA`、橘色強調 `#FF7A1A`。
- **字型**：全片統一用一種字型。預設是**源石黑體 粗體**（GenSeki Gothic Bold，OFL 授權，中文、英文、數字、字幕都用它）。使用者有指定字型就換，但要確認那個字型可以自由使用。
- 顏色和字型都寫進專案的 `theme.json`（範例 `<me>/templates/theme.example.json`，每個欄位的意思和 `source` 怎麼填，見 `references/theme-json.md`）。

彙整成需求摘要，分「使用者回答」和「我推斷的」兩區，使用者確認後才開工。

## 3. 建專案與分鏡

1. `hyperframes init videos/<kebab-name> --non-interactive --example=blank --skill=faceless-explainer`，接著寫 `BRIEF.md`，然後照 `/faceless-explainer` 的 Step 0–2 做（`capture/extracted/`、選一個 frame preset 產生 `frame.md`）。
2. **選 preset 時優先選線稿清楚的**（例如 `cobalt-grid`）。它只是「來源配色」，最後會被 `theme.py` 換成使用者的三色。
3. 在 `frame.md` 加上 **繁體中文覆寫**（字型、字重、字距、行高、投影機最小字級），內容照 `motion-design` 第 5 節。
4. 跑 `bash <me>/scripts/fetch_fonts.sh <project>`，把源石黑體粗體（從官方 GitHub release 下載）、frame worker 製作時用的 Latin 字型和 Noto TC，全部放進 `assets/fonts/`，**不要依賴 Google Fonts 線上載入**。
5. 寫 `STORYBOARD.md` 和 `SCRIPT.md`（格式照官方 storyboard-format / script-format）。旁白要**照「子句」切**，每個逗號就是一個畫面揭示的時間點；數字寫成國字（「零點八一秒」），TTS 才不會唸錯。

## 4. 旁白

1. 產生 `assets/voice/raw/NN.wav`（每句一個檔，NN 是分鏡格號）：
   - **edge-tts**：`python <me>/scripts/edge_tts_voice.py --project <p> --voice zh-TW-HsiaoChenNeural [--rate=-5%]`。全片用同一個 voice，聲音天然一致；`--list zh-TW` 可以列出所有聲音。
   - **Breeze TTS 2**：`python <me>/scripts/breeze_voice.py --project <p> --breeze-repo … --model … --voice "<聲音描述>" --only-ref`，先設計**一個**參考聲音讓使用者聽，確認後再拿掉 `--only-ref` 產生全部句子（每一句都複製這個參考聲音）。如果有批次 runner，改用 `<me>/scripts/tts_jobs.py` 產生工作清單。
   - 使用者還沒裝、或不確定要選哪一個：照 `references/tts-setup.md` 給建議，一步一步確認，不要擅自安裝。
2. **先讓使用者試聽前一兩句**，口音與情緒由使用者用耳朵決定，不拿分數代替。不滿意就換一個 voice 或改語速，刪掉舊的 WAV 再重新產生。
   - **整支片做完才發現某個字唸錯**（例如英文品牌名、破音字）：不要整句重錄，不然那一格的動畫時間會全部跑掉。改成：同一個聲音、同一句話產生 4–6 個候選，可以換 seed，也可以換拼法，例如 `Road-ster` 或同音同調的字，字幕仍然用原文；放到 `assets/voice/fix/cand/NN_X.wav`。edge-tts 沒有 seed，用拼法、`--rate`、`--pitch` 做出差異：`python <me>/scripts/edge_tts_voice.py --project . --line N [--text "<換拼法的整句>"] [--rate=-3%] --out assets/voice/fix/cand/NN_B.wav`；Breeze 換 seed 重產同一句。然後跑 `python <me>/scripts/fix_voice.py --project . audition --line N --clauses <那個詞所在的子句>`，把關鍵片段串成一個試聽檔給使用者用耳朵選。選好之後跑 `apply --line N --take NN_X`，它會把新句子**整句等比伸縮回原本的長度**，音量對齊原本那一句，再重算那一句的字幕時間，每一格的長度不變。接著重建字幕 → `patch_captions.py` → `theme.py`（它會自動認出新字幕）→ 重新輸出。**不要把重錄的句子照停頓切成子句再對時間**：重錄的停頓位置不一樣，切點會落在字中間，結果漏字或重複（實測發生過）。ASR 只能用來篩掉明顯錯的；聲調對不對，ASR 聽不出來（實例：「輪胎」ASR 判對，使用者聽起來是錯的）。
3. `python <me>/scripts/voice_meta.py --project <p>`：去頭尾靜音、量出每個子句的時間、寫 `audio_meta.json`。
4. `node <fe>/scripts/audio.mjs sync-durations --audio-meta ./audio_meta.json --storyboard ./STORYBOARD.md`
5. 響度：最後成片要約 −14 LUFS、true peak ≤ −1 dBFS。先量成片：`ffmpeg -hide_banner -nostats -i renders/video.mp4 -af ebur128=peak=true -f null -`，看 `Integrated loudness`（I）。差多少（G = −14 − I），就在**每一句旁白**加上同樣的 G dB 再壓峰值，保留各句之間的相對音量，然後重新輸出：
   ```bash
   for f in assets/voice/[0-9]*.wav; do ffmpeg -v error -y -i "$f" -af "volume=${G}dB,alimiter=limit=0.89" "${f%.wav}.tmp.wav" && mv "${f%.wav}.tmp.wav" "$f"; done
   ```

## 5. 鏡頭設計（Step 4）

- 在 `shots.json`（見 `<me>/templates/shots.example.json`）裡，每格用「第幾個子句 → 畫面上出現什麼」來寫，跑 `python <me>/scripts/apply_shots.py --project <p>` 換算成真實秒數，寫回 `STORYBOARD.md`。
- `blueprint` 欄位只能是 `<id> (Adapt)`、`<id> (Reproduce)` 或 `compose`，說明另外放在 `note`。
- 先用 `hyperframes catalog --query` 找現成元件，找不到再自己畫。
- **會在多格重複出現的主角（車、人、儀器）先畫成一個共用 SVG**，固定各部件的座標，所有 worker 都必須照抄。不這樣做，每格的主角都會長得不一樣。

## 6. 平行做每一格

1. `node <fe>/scripts/frame-packets.mjs --project <p> --storyboard <p>/STORYBOARD.md`
2. 從 `<me>/templates/dispatch_context.md` 複製一份到 `.hyperframes/frame-packets/_dispatch_context.md`，把專案的值填進去：Video direction、共用素材、時間規則、字型。
3. 每一格派一個 sub-agent，全部平行。prompt 依序讀：`_role.md` → `_dispatch_context.md` → 該格 packet → `frame.md` → 共用素材。**沒有 sub-agent 時**，自己照格號順序一格一格做，每格照同樣的順序讀這幾個檔案；做完一格先截幾張圖確認，再做下一格。
4. **相鄰格要接續同一個畫面時**（例如同一條刻度尺），先做完的那一格回報的精確幾何，要立刻轉給還在做的那一格。
5. 全部回來以後：`python <me>/scripts/unify_frames.py --project <p>`，統一字型和髮絲線位置。

## 7. 組裝、字幕、配色

```bash
node <fe>/scripts/captions.mjs build --storyboard ./STORYBOARD.md --audio-meta ./audio_meta.json --hyperframes . --out ./caption_groups.json
node <fe>/scripts/assemble-index.mjs --storyboard ./STORYBOARD.md --hyperframes .   # 要在字幕之後：輸出要看到 captions (track 2): yes
python <me>/scripts/patch_captions.py --project .     # 中文字幕字型與粗細（預設粗體 700）
python <me>/scripts/theme.py --project .              # 套用 theme.json 的三色與字型（index、每一格、字幕）
node <fe>/scripts/transitions.mjs inject --storyboard ./STORYBOARD.md --hyperframes .
node <fe>/scripts/transitions.mjs verify --storyboard ./STORYBOARD.md --index ./index.html
hyperframes lint && hyperframes check
```

（`<fe>` = 已安裝的 faceless-explainer skill 資料夾。）字幕每次重建後，都要重跑 `patch_captions.py` 再跑 `theme.py`。`theme.json` 的 `accents` 指定每一格裡哪些元素用強調色（block／fill／text／stroke）。`theme.py` 會自動認出重新產生過的檔案（沒有 `(theme.py)` 標記的），拿它當新的原始檔；但手動改已套色的檔案時，`.hyperframes/pre-theme/` 裡那一份也要一起改。`transitions.mjs inject` 會延長每一格的長度：每次跑完 `theme.py` 都要再 inject 一次，但不要連續 inject 兩次（中間沒有跑 `theme.py` 的話，長度會被延長兩次）；`font` 會把每一格和字幕的所有文字都換成同一個字型和字重，覆蓋 worker 原本寫的字型設定。換字型後字變寬了，要重跑 `hyperframes check` 看有沒有溢出或重疊。

**最後一步才瘦身字型**：`python <me>/scripts/subset_fonts.py --project .`。它會只留下片中用到的中文字（CJK 字型從 12–17 MB 降到幾百 KB），並把每一格的 `@font-face` 改指向瘦身後的檔案。任何改動文字、字幕或配色的動作之後都要重跑：`theme.py` 每次都從配色前的原始檔重新套色，原始檔指向的是完整字型，新加的字如果不在瘦身檔裡，就會退回系統字型。

## 8. 審查（`review-loop`）

- 先 `hyperframes check`，再用 draft 品質輸出整片（`hyperframes render --quality draft --workers <hw_check 建議值> --output renders/draft.mp4`；審查階段一律用 draft），在**每個子句結束前 0.15 秒**截一格（取落定的狀態），拼成 contact sheet，**每一張都要打開來親眼看**：
  ```bash
  python <review-loop>/scripts/sheet.py --video renders/draft.mp4 --at "$(python <me>/scripts/review_times.py --project .)" --out review --name draft
  ```
- 對照 `references/lessons.md` 的檢查表逐項看，修完重新輸出、重新看，直到一輪都沒有問題。
- 看完才輸出最終版：`hyperframes render --skill=faceless-explainer --quality high --output renders/video.mp4`，再量一次響度。

## 9. 交付

交出 MP4 路徑、片長、一張總覽 contact sheet，並列出：用了哪些來源、哪些數字是宣稱、哪些是估算、哪些地方和需求不一樣（例如片長超出）、哪些沒做（例如沒有配樂）。
