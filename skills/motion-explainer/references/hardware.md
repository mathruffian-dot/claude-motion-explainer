# 硬體效能：哪些步驟吃什麼資源（給 agent 的建議）

動工前先跑 `python <me>/scripts/hw_check.py --project <專案>`，它會偵測 CPU、記憶體、NVIDIA GPU 和硬碟空間，印出建議設定。**那些建議都是依經驗法則推估的，不是跑分結果**；下面說明推估的依據。

唯一的實測資料：Intel Ultra 7 270K（24 核心）、95 GB RAM、RTX 5090，105 秒的片，draft 輸出約 75–80 秒，high 輸出約 85–90 秒，`auto` 選了 3 個 render worker。效能普通的電腦會照比例變慢，但我們沒有測過。

## 吃重：決定「能不能跑」

**Breeze TTS 2（進階旁白，選配）**
- 需要 NVIDIA GPU。一般模式約 7.7 GB VRAM；`--fast-all` 模式約 14.4 GB。建議 12 GB 以上的卡。
- 模型檔約 7 GB（實測 7.2 GB），另外要加 Python 環境的空間。
- 速度：用批次 runner 每句約 20–35 秒（RTX 5090）。`breeze_voice.py` 走官方 `infer.py`，每一句都會重新載入模型，會更慢。
- 沒有 GPU，或 VRAM 不到 12 GB：用 **edge-tts**。它在 Microsoft 的伺服器上合成，本機幾乎不吃資源，只需要網路。詳見 `tts-setup.md`。

## 中等：決定「要等多久」

**HyperFrames 輸出影片**
- 原理是開好幾個無頭 Chrome，一格一格截圖，再交給 ffmpeg 壓成影片。主要吃 CPU，有 GPU 時也會用上。
- 每個 Chrome worker 都要占記憶體。記憶體小的電腦要把 `--workers` 調低：不到 8 GB 用 1，8–16 GB 用 2，更多就用 `auto`。這是推估值，遇到記憶體不足或當機就再調低。
- 一支片通常要輸出 **2–3 次**：草稿、修改後再一次草稿、最後的正式版。審查階段一律用 `--quality draft`，只有最後一次用 `--quality high`。

**中文字型**
- Noto Sans TC 和 Noto Serif TC 各 12–17 MB，每一格都要載入。
- `scripts/subset_fonts.py` 會只留下片中用到的字。實測：358 個字，Sans 11.9 MB → 239 KB、Serif 16.9 MB → 329 KB（約小 98%）。逐格比對畫面 SSIM 0.999996，沒有缺字。
- **老實說**：在上面那台快的電腦上，輸出時間沒有變快（74.6 秒對 79.9 秒，差異在誤差範圍內）。好處在檔案小 98%、每個 Chrome worker 要載入的字型少很多（理論上比較省記憶體，未實測），以及複製、上傳、雲端輸出專案時快很多。效能普通的電腦上有沒有變快，我們沒有測過。

**`hyperframes check` 和 snapshot**：也要開瀏覽器跑整支片，大約是一次輸出時間的幾分之一。

## 輕量：一般電腦都沒問題

- ffmpeg 小工具：`voice_meta.py`（裁掉靜音、偵測停頓）、`review-loop/scripts/sheet.py`（拼 contact sheet）、響度量測，每次幾秒鐘。
- 其他 Python 腳本：`theme.py`、`unify_frames.py`、`patch_captions.py`、`apply_shots.py`、`subset_fonts.py`，都在幾秒內跑完。

## 不吃本機硬體，但有其他成本

- **平行派出的 frame sub-agent**：在雲端跑，不耗本機效能，但很耗 token，每格約 14–22 萬（9 格的片實測）。有些 worker 會在本機開瀏覽器預覽自己做的那一格，所以 9 個同時跑的時候記憶體會有一陣高峰。記憶體不到 16 GB 的電腦，改成每批 3 個分批派出。
- **需要網路的部分**：edge-tts 合成、各格從 CDN 載入 GSAP、`fetch_fonts.sh` 下載字型（源石黑體從 GitHub release、Latin 字型從 npm、系統沒有 Noto TC 時從 google/fonts）。

## 技能沒用到的 HyperFrames 選配

`hyperframes doctor` 會列出 Whisper（語音轉文字）、Kokoro（本機英文語音）、MusicGen（本機生成配樂），其中 MusicGen 很吃 GPU。這個技能刻意都沒用到：字幕時間用「腳本原文加停頓偵測」取代 Whisper，旁白用 edge-tts 或 Breeze。
