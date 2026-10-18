# `theme.json` 欄位說明

`theme.json` 放在專案根目錄，四個工具會讀它：`theme.py`（配色、強調色、字型）、`unify_frames.py`（字型 fallback、髮絲線位置）、`patch_captions.py`（字幕字型）、`subset_fonts.py`（瘦身哪些字型）。範例：`templates/theme.example.json`。

| 欄位 | 必填 | 誰讀 | 說明 |
|---|---|---|---|
| `bg` | ✔ | theme.py | 背景色，例如 `"#121212"` |
| `fg` | ✔ | theme.py | 主色：文字、線稿、細線 |
| `accent` | ✔ | theme.py | 強調色：只給答案、結論、關鍵數字、章節卡 |
| `font` | 建議 | theme.py | 全片唯一字型：`{"family": "GenSekiGothic", "file": "GenSekiGothic2TW-B.otf", "weight": 700}`。檔案放在 `assets/fonts/`。設定之後，每一格和字幕的所有文字都會換成它 |
| `source` | ✔ | theme.py | 被替換掉的「來源配色」，見下一節 |
| `accents` | 選填 | theme.py | 每一格哪些元素用強調色，見下面 |
| `font_stacks` | 選填 | unify_frames.py | worker 寫的中文字型後面補上的 Latin 字型，例如 `{"NotoSansTC": "Hanken Grotesk"}` |
| `hairlines` | 選填 | unify_frames.py | 每一格上下兩條細線的位置，例如 `{"top": "3cqw", "bottom": "880px"}`，讓每一格的細線對齊 |
| `caption` | 選填 | patch_captions.py | 字幕字型：`{"cjk": "NotoSansTC", "cjk_file": "NotoSansTC-VF.ttf", "latin": "Hanken Grotesk", "weight": 700}`。有 `font` 時，字幕最後還是會被換成 `font` |

## `source`：從 frame preset 的色票填

每一格是 worker 照 `frame.md`（你選的 frame preset）的色票畫的。`theme.py` 把這些色碼換成你的三色：

| 鍵 | 換成 | 從哪裡找 |
|---|---|---|
| `ink`（陣列） | `fg` | `frame.md` 色票裡的主要墨色（文字、線稿） |
| `ink_rgb`（字串 `"R,G,B"`） | `fg` 的 rgba | 同一個墨色的 RGB，用來替換 `rgba(R, G, B, α)` 寫法的半透明線（格線） |
| `paper`（陣列） | `bg` | 紙色、背景色（可能有兩三個深淺） |
| `ink_soft`（陣列，選填） | `fg` 和 `bg` 7:3 混色 | 次要文字、較淡的墨色 |

範例是 `cobalt-grid` 的色票（`#1F2BE0` 墨色、`#F0EBDE`／`#E6E0CE` 紙色）。換了 preset，就要打開 `frame.md` 找它的色票，把色碼填進來。檢查方法：套色之後在每一格的 HTML 裡搜尋舊色碼，還找得到就是漏填了。

## `accents`：每一格的強調元素

鍵是每一格的檔名（不含 `.html`），值是四種模式，每種是一串 CSS 選擇器：

| 模式 | 效果 | 用在 |
|---|---|---|
| `block` | 強調色底 + 背景色字 | 章節卡、結論方塊 |
| `fill` | 強調色底 | 代表結論的那一條長條、那一格方格 |
| `text` | 強調色字 | 大數字、答案 |
| `stroke` | 強調色線 | SVG 的線或外框（例如斜邊） |

最簡單的做法：在 `_dispatch_context.md` 規定 worker 在要強調的元素加上 class `accent-block`／`accent-fill`／`accent-text`／`accent-stroke`，元素本身仍用來源配色畫。這樣每一格的 `accents` 都可以寫成同一組：

```json
"accents": {
  "02-squares": {
    "block": ["[class~=\"accent-block\"]"], "fill": ["[class~=\"accent-fill\"]"],
    "text": ["[class~=\"accent-text\"]"], "stroke": ["[class~=\"accent-stroke\"]"]
  }
}
```

id 以數字開頭時，CSS 要寫成 `[id="07-chap"]` 或 `#\\30 7-chap`（JSON 裡反斜線要寫兩次）。
