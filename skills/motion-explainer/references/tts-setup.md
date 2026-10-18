# 旁白語音：怎麼選、怎麼裝（給 agent 的建議）

先問使用者：**電腦有沒有 NVIDIA 顯示卡（至少 12 GB 顯示記憶體）？影片會不會拿去商用？** 再依答案推薦。

| | edge-tts（預設） | Breeze TTS 2（進階） |
|---|---|---|
| 適合誰 | 大部分人：任何電腦都能用 | 有 NVIDIA GPU、想精細控制口音和情緒的人 |
| 硬體 | 不需要 GPU | NVIDIA GPU，約 7.7 GB VRAM（建議 12 GB 以上） |
| 網路 | 產生語音時需要連網（Microsoft 線上服務） | 下載模型之後可以離線 |
| 台灣口音 | `zh-TW-HsiaoChenNeural`（女）、`zh-TW-HsiaoYuNeural`（女）、`zh-TW-YunJheNeural`（男） | 用文字描述設計聲音，例如「台灣口音的年輕女老師，語氣親切」，再複製給每一句 |
| 一致性 | 全片固定用同一個 voice，天然一致 | 先設計一個參考聲音，每一句都用它做聲音複製 |
| 授權 | 使用 Microsoft 線上服務，商用前請自行確認服務條款 | 模型權重和**產生的聲音只限研究與非商業用途**（BreezeBlue Research and Non-Commercial License） |
| 本技能腳本 | `scripts/edge_tts_voice.py` | `scripts/breeze_voice.py`（官方 CLI），或 `scripts/tts_jobs.py`（批次工作清單） |

兩條路都輸出 `assets/voice/raw/NN.wav`，後面的 `voice_meta.py` 和整條流程完全一樣。

## edge-tts 安裝（給使用者的步驟）

```bash
pip install edge-tts
python <me>/scripts/edge_tts_voice.py --list zh-TW          # 列出可用的台灣聲音
python <me>/scripts/edge_tts_voice.py --project <專案> --voice zh-TW-HsiaoChenNeural
```

需要時用 `--rate -5%` 放慢一點，國中生比較跟得上；也可以用 `--pitch -2Hz` 微調音高。

## Breeze TTS 2 安裝（使用者要求時才建議，逐步確認）

1. **先確認硬體**：`nvidia-smi` 看得到顯示卡，而且 VRAM ≥ 12 GB。沒有的話建議改用 edge-tts。
2. **先說明授權**：模型和它產生的聲音只限研究、教學這類非商業用途，使用者要同意才繼續。
3. 下載程式碼與安裝套件（官方說明以 Linux + Python 3.10+ 為準；Windows 也跑得動，但要自己裝對應 CUDA 版本的 PyTorch）：
   ```bash
   git clone https://github.com/breezeblue-ai/breeze-tts.git
   cd breeze-tts
   python -m venv venv && venv/Scripts/activate      # Linux/macOS: source venv/bin/activate
   python -m pip install -r requirements.txt
   ```
4. 下載模型權重：Hugging Face `BreezeBlue/Breeze-TTS-2`（約數 GB，下載前先告訴使用者檔案大小並取得同意）。
5. 試跑一句（Voice Design）：
   ```bash
   python infer.py ../Breeze-TTS-2 --text "同學們好" --instruction "一位台灣口音的年輕女老師，聲音清晰，語氣親切" --cfg-scale 4 --output test.wav
   ```
6. 接上本技能：
   ```bash
   python <me>/scripts/breeze_voice.py --project <專案> --breeze-repo <breeze-tts 路徑> --model <Breeze-TTS-2 路徑> \
       --python <breeze-tts/venv 的 python> --voice "<聲音描述>" --only-ref
   ```
   先讓使用者聽 `assets/voice/raw/ref_narrator.wav`，滿意了再拿掉 `--only-ref`，產生全部句子。

## 共通注意

- 旁白裡的數字寫成國字（「零點八一秒」），兩種引擎都比較不會唸錯；英文專有名詞（SpaceX、Roadster）要聽一次確認發音。
- 口音和情緒交給使用者用耳朵判斷，不要拿 ASR 或相似度分數代替。
- 響度最後統一處理（成片約 −14 LUFS），見 SKILL 第 4 節。
