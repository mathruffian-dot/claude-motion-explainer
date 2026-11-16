# 3D 格：three.js 嵌在 HyperFrames 裡（2026-11-16）

**規則（使用者 2026-11-16）：內容需要 3D 就自動用 three.js，不用先問。** 2D 線稿講得清楚的仍用 2D。

範本：`templates/three_scene.example.html`（行星＋地軸＋標籤＋推近鏡頭，已在「從第 2 秒開始的格」實測過）。完整實例：高中地理〈等高線地形圖判讀〉55 秒（地圖升成山 → 每 100 公尺切一刀 → 投影回地圖 → 疏密 → 山脊山谷）。那支片的程式沒有放進這個技能，做法都整理在本檔和範本裡。

## 什麼時候用 3D

| 內容 | 用 3D 的理由 |
|---|---|
| 立體地形、等高線、剖面 | 「平面圖 ↔ 立體」的轉換本身就是要教的東西 |
| 分子、晶體、DNA | 空間結構，2D 只能畫投影 |
| 天體運行（公轉、自轉、月相、四季） | 角度與位置關係要轉著看 |
| 立體圖形（展開圖、截面、旋轉體） | 從平面摺起來、切開，要連續變形才懂 |
| 物理模擬（拋體、單擺、電場線） | 先算好整段軌跡，再照時間查表 |

一個主角物件就好。鏡頭「推進去」（dive）比一直繞圈有用；每一段只講一件事，配一行字。

## 接法（每一條都踩過）

1. **`three.min.js` 放 `assets/lib/`，`<script src="assets/lib/three.min.js">` 寫在那一格自己的 `<template>` 裡。** 寫在 `index.html` 的 `<head>`，lint 報 `missing_three_script`（錯誤）。用 three@0.149.0 的 `build/three.min.js`（傳統 script 版，全域 `THREE`；r160 以後只剩 ES module）：`npm install three@0.149.0` 後複製過去。
2. **`hf-seek` 給的是全片時間，不是這一格的時間。** 實測 0.8.168：從第 2 秒開始的格，在全片 2.5 秒收到 `2.5`。要減掉這一格的開始時間，從 `index.html` 宿主 div 讀：
   `document.querySelector('[data-composition-id="ID"][data-start]').getAttribute("data-start")`（snapshot 和 render 都實測正確）。只有整支片一格、從 0 秒開始時才剛好不用減。
3. **畫面只由時間決定**：`window.addEventListener("hf-seek", e => renderAt(e.detail.time))`。不用 `requestAnimationFrame`、不用時鐘；輸出時每一格是亂序、分給不同 worker 算的。所有狀態（鏡頭、物體位置、透明度、顏色）都在 `renderAt(t)` 裡從 t 重新算。模擬（物理、粒子）要先在載入時算完存成陣列，再照 t 查表；亂數用固定 seed。
4. **`WebGLRenderer({ preserveDrawingBuffer: true, alpha: true })`**，背景透明，底色交給頁面（三色主題才換得到）。
5. **載入完成要通知**：`window.__hf.buildReady["ID"] = promise`（字型載好、幾何算完）。還要照常註冊一條長度＝這一格的 GSAP 時間軸 `window.__timelines["ID"]`。
6. **顏色寫成 `"#rrggbb"` 字串**（`new THREE.Color("#E2452B")`），用 `frame.md` 的來源配色。`theme.py` 是把整個檔案裡的色碼字串換掉，`0xE2452B` 這種數字換不到，換主題後 3D 會留著舊顏色。
7. **粗線用細圓柱。** WebGL 的線寬固定 1 px，1080p 上幾乎看不到。很多段的線（等高線、軌跡）用 `InstancedMesh`：每段一根圓柱，長度乘 1.2 倍蓋住接縫。
8. **標籤用 HTML，不畫進 3D。** 每格把 3D 座標 `project(cam)` 成螢幕座標，設 `left`／`top`；`z ≥ 1`（跑到鏡頭後面）就藏起來。標籤字用 px，不用 cqw。字不小於 32 px，避開字幕區。
9. **地形、曲面上的線會沉進去**：曲面材質開 `polygonOffset`（factor／units 約 3），線再抬高一點點。
10. **立體 ↔ 平面的轉換**：網格的 y 存真實數值（例如公尺），畫的時候用 `mesh.scale.y = r × 比例`（r 從 1 到 0）。法線會自動跟著對（three.js 用逆轉置矩陣），壓平時光線變均勻，剛好像一張地圖。**高度有放大就要在畫面上標「高度放大 N 倍」。**
11. **燈光**：暖色主光、冷色輪廓光，加一盞半球光。材質用 `MeshLambertMaterial`，在沒有 GPU 的電腦上比 Standard 快。

## 鏡頭

- 每個鏡位寫成參數（俯角、方位、距離、注視點、畫面偏移），轉場在兩個鏡位之間用 ease 內插，時間用旁白的子句來排。
- 正上方俯視（地圖）：俯角 89.3° 左右就好，不要剛好 90°（lookAt 會不穩定）。
- 旁邊要放字卡時，用 `cam.setViewOffset(W, H, 偏移px, 0, W, H)` 把畫面往旁邊推，不用移動物體。

## 審查

- `hyperframes check` 之後，**截圖一定要截到每一次鏡頭轉換的中間和結束**，看這些：
  - 標籤有沒有跑到物體背後；
  - 線有沒有沉進曲面；
  - 鏡頭有沒有跳一下；
  - 邊緣有沒有切到主體。
- 沒有 GPU 也輸出得出來（瀏覽器改用軟體算 3D）。等高線那支 55 秒的片：本機 GPU 1 個 worker 2:25；`--no-browser-gpu` 2 個 worker 2:43，兩版畫面 SSIM 0.998。桌機 CPU 量的，筆電沒實測。3D 片每秒片長的輸出時間約是 2D 的 2.5 倍。
