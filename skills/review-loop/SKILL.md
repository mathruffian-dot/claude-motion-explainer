---
name: review-loop
description: 動畫影片的視覺自我審查循環（HyperFrames 版）— 輸出草稿、在每個時間軸節拍截圖拼成 contact sheet、逐張對照檢查表、修正、重來。只要動畫的畫面或時間有任何修改，以及在宣告影片完成之前，都一定要使用此技能。
---

# Review loop（HyperFrames 版）

你看不了影片，但你看得了畫面。沒有看過「目前這一版」輸出的 contact sheet，絕對不要回報影片完成。

> 改編自 whaleyxbt/claude-motion 的 `review-loop` skill（MIT，見同資料夾 `LICENSE`）。原版的 `npm run …` 指令改成 kinocut MCP 的 HyperFrames 工具，以及本資料夾的 `scripts/sheet.py`。標示「（本版新增）」的段落不是原作內容。

下面的 `SHEET` 指的是 `python "<此技能資料夾>/scripts/sheet.py"`（例如 `~/.claude/skills/review-loop/scripts/sheet.py`）。所有路徑都用絕對路徑。

## 循環

0. **先過機器檢查**（本版新增）：在專案資料夾執行 `hyperframes check`。它一次跑完 lint、執行期、版面溢出、動作和對比度檢查（官方已經把 `validate`／`inspect` 標為過時，改用 `check`）。有錯先修，修完再往下。細節見官方 `hyperframes-cli` skill。
   - 遮罩揭示在進場途中一定會報 `container_overflow`，屬於刻意設計，在遮罩容器加 `data-layout-allow-overflow`。但如果落定之後還報 `text_box_overflow`，就是容器太矮，會切到字（中文和上標特別容易），要把容器加高。
1. **草稿**：`hyperframes_render`，參數 `quality: "draft"`，`output_path` 設成 `<專案>/out/draft.mp4`。
2. **Contact sheet**：`SHEET --video <專案>/out/draft.mp4 --timeline <專案>/timeline.js --out <專案>/out/sheets`
   每個節拍後 0.3 秒（動作已經落定）取一格，4×2 拼成 `out/sheets/beats-N.png`，每格標上節拍名稱和時間。每格預設 360 px 寬，也就是手機動態上的實際寬度。
3. 用 Read 打開每一張 sheet，逐項對照下面的檢查表。
4. 可疑的地方放大看：
   - 掃一段轉場：`SHEET --video … --from 3 --to 5 --every 0.2 --name scrub`
   - 看特定時刻：`SHEET --video … --at 3.7,3.75,3.8 --name exact`
   - 看單格全解析度：`hyperframes_still`，`frame` 填幀號（秒數 × fps）
   - 不想重新輸出影片時，也可以用 `hyperframes_snapshot` 的 `at` 直接從 composition 截圖，再用 `SHEET --images … --labels …` 拼起來。
5. 修正後回到第 0 步。完整跑一輪都沒有發現問題，才停。
6. **最終版**：`hyperframes_render`，`quality: "high"` 輸出成片，再對成片跑一次第 2 步，然後做聲音檢查（見下方）。

## 檢查表

構圖
- 每格只有一個焦點。兩個東西搶戲時，其中一個要等。
- 沒有非刻意的碰撞或重疊，特別是轉場時，退場和進場的元素共用同一塊空間。
- 安全區：重要內容不要離邊緣不到約 60 px。
- 第 0 格是真正的畫面，不是黑的（它就是社群平台上的縮圖）。

文字
- 沒有被遮罩、容器或畫面邊緣切到（除非是刻意的）。
- 縮成手機寬度（sheet 的格子）時，關鍵訊息仍然讀得清楚。
- 該被閱讀的時候，文字沒有在動。
- （本版新增）中文：沒有錯字；全部是繁體字形，沒有混入簡體；標點用全形；沒有字型缺字（出現方框或明顯不同的字體）。

節奏
- 每個要讓人讀的狀態都停得夠久（見 `motion-design` 第 4 節）。如果停留中段的格子裡文字還在動，就代表停留太短。
- 場景之間是重疊銜接，不是切到空白畫面。
- 退場比進場快。

一致性
- 只用 `:root` 色票裡的顏色；強調色標的就是這一格的重點。
- 同一個元素在每個出現的場景裡看起來都一樣。

聲音（只在有聲音時）
- 波形：`video_audio_waveform` 檢查聲音的峰值有沒有落在 `TL` 的節拍上。
- 響度（本版新增，取代原作的 `npm run wave`）：
  `ffmpeg -hide_banner -nostats -i <成片> -af ebur128=peak=true -f null -`
  看最後摘要的 `Integrated loudness` 和 `True peak`。目標是 −14 LUFS ±1，true peak ≤ −1 dBFS。
- 中文旁白的口音和情緒，請使用者用耳朵聽，不要拿分數代替（本版新增）。

## 回報

完成時要說清楚：檢查了什麼、修了什麼、哪一張 sheet 可以看到結果。沒有重新輸出並親眼看過的修正，不要宣稱已經修好。
