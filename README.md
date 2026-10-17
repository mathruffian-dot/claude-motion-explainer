# claude-motion-explainer

**用一句話，讓 coding agent 做出一支「原理解說動畫」。** 上網查資料、寫腳本、中文旁白、一格一格做動畫、字幕、三色配色、自我審查，最後輸出可以直接上課投影或上傳 YouTube 的 MP4。

這是一組給 Claude Code（以及 Codex、Gemini CLI 等讀得懂 `SKILL.md` 的 agent）用的 skills，建立在 HeyGen 開源的 [HyperFrames](https://github.com/heygen-com/hyperframes)（HTML + GSAP → MP4）之上。

> 與 Anthropic 官方的 Claude Motion 無關。這是社群做的開源工作流。

## 你會得到什麼

用這套技能做出來的第一支片：〈Tesla Roadster 的三個神奇配備〉，105 秒、9 格。

- 用國中理化解釋三件事：倒掛靠壓力差，滯空靠作用力與反作用力，超快加速靠突破輪胎摩擦力的上限。
- 繁體中文旁白，字幕逐句高亮。
- 黑底、白線稿，橘色只標重點。
- 每個數字都在畫面上標「宣稱」或「估算」。

## 包含的 skills

| Skill | 做什麼 |
|---|---|
| [`motion-explainer`](skills/motion-explainer/SKILL.md) | **主流程**：研究 → 需求訪談（含三個顏色）→ 分鏡與子句化旁白 → TTS → 每格派一個 sub-agent 平行製作 → 字幕 → 套色 → 審查 → 輸出 |
| [`motion-design`](skills/motion-design/SKILL.md) | 品味規則：緩動、節奏、閱讀停留、繁體中文排版、三色配色，全部附具體數字 |
| [`review-loop`](skills/review-loop/SKILL.md) | 自我審查：在每個旁白子句截一格拼成 contact sheet，逐張對照檢查表 |

`motion-explainer/references/lessons.md` 收錄第一支片實際踩過的 23 個坑：整格樣式消失、遮罩漏字、數字和長條不同步、字型不一致……每一條都附解法。

## 需要的環境

先跑 `python skills/motion-explainer/scripts/hw_check.py`：它會檢查你的 CPU、記憶體、GPU 和硬碟，建議要用哪個旁白引擎、輸出時同時開幾個 worker。各步驟吃多少資源，見 [`hardware.md`](skills/motion-explainer/references/hardware.md)。

- Node.js 22+、ffmpeg、Python 3 + Pillow + fonttools（`pip install pillow fonttools`；另外裝 `brotli` 的話，瘦身後的字型會是 woff2）
- HyperFrames：`npm install -g hyperframes`，再跑 `hyperframes skills update` 和 `hyperframes skills update faceless-explainer`
- 旁白（擇一，詳見 [`tts-setup.md`](skills/motion-explainer/references/tts-setup.md)）：
  - **edge-tts（預設，大多數人用這個）**：`pip install edge-tts`。不需要 GPU，產生時要連網，有台灣口音的男聲和女聲。
  - **Breeze TTS 2（進階）**：本機 NVIDIA GPU（建議 12 GB 以上），可以用文字描述來設計聲音。模型和產生的聲音**只限研究與非商業用途**。想用的話，請 agent 照 `tts-setup.md` 一步一步帶你安裝。

## 安裝

```bash
git clone https://github.com/mathruffian-dot/claude-motion-explainer.git
cp -r claude-motion-explainer/skills/* ~/.claude/skills/        # Claude Code
# Codex / 其他 agent：複製到 ~/.agents/skills/
```

字型（開源 OFL）不放在 repo 裡，每個專案要用時，跑一次 `bash skills/motion-explainer/scripts/fetch_fonts.sh <專案資料夾>` 就會放好。影片做完、正式輸出前，`subset_fonts.py` 會把中文字型瘦身成只含片中用到的字（12–17 MB 降到幾百 KB）。

## 怎麼用

在 Claude Code 裡直接說：

```text
上網查資料，做一支 90 秒、解說「為什麼飛機飛得起來」的動畫，給國中生上課用。
```

Agent 會先問你播放平台、長度、旁白聲音和**三個顏色**（背景色、主色、強調色，預設是黑底、白字、橘色重點），確認後才開始做。做完會交給你 MP4 和一張總覽圖。

## 三色主題

像簡報版型一樣，由你決定三個顏色：

```json
{ "bg": "#121212", "fg": "#F2F0EA", "accent": "#FF7A1A" }
```

強調色只給「答案、結論、關鍵數字、章節卡」。想換一組顏色，改 `theme.json` 再跑 `python scripts/theme.py --project <專案>`，然後重新輸出就好，不用重做動畫。

## English

A set of agent skills that turn one sentence into a narrated, captioned explainer animation (MP4) on top of [HyperFrames](https://github.com/heygen-com/hyperframes): web research → brief (incl. a three-color theme) → clause-cued storyboard → TTS (edge-tts by default, Breeze TTS 2 optional) → parallel per-frame sub-agents → captions → theming → contact-sheet self-review → render. Written in Traditional Chinese; the workflow itself is language-agnostic. See `skills/motion-explainer/SKILL.md`.

## 授權

程式碼與文件採 [MIT](LICENSE)。`motion-design` 和 `review-loop` 改編自 [whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion)（MIT），其他第三方元件見 [NOTICE.md](NOTICE.md)。
