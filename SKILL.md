---
name: claude-miniature-film
description: 用 Blender 腳本（Python bpy、Geometry Nodes、EEVEE/Cycles）做電影級 3D 微縮世界角色短片，對標《claude.MP4》：終端機游標活過來變成 Claude Code 像素小怪 Clawd，2D 像素→體素→黏土實體，走出螢幕，踩著封有體素地景的透明樹脂鍵帽前進，鑽進鍵帽裡的寫實草原，種下游標長出一棵結滿分身的樹，分身拼成巨人，一鏡拉出才發現世界在鍵帽裡。內含整套導演系統（敘事配方、母題、尺度敘事、120 BPM 剪輯網格、轉場庫、光影與材質規範）、bpy 腳本庫（角色 rig 與表演、體素形變、鍵帽與 17 種微縮地景、草地散佈、分身群集與剛體雨、光膜／漣漪／透鏡特效、相機語言）和 17 個鏡頭的完整基準實作。只要使用者想用 Blender 或程式做 3D 動畫短片、角色短片、產品擬人化片、微縮世界或移軸感影片、體素／像素角色變 3D、鍵帽或桌面上的小世界、尺度揭示或一鏡拉出、Pixar 感小短片，或提到 Clawd 3D、claude.MP4、復刻這支片，即使沒提 skill 也要使用。Use for any Blender-scripted 3D character short, miniature-world film, voxel/pixel-to-3D character animation, keycap diorama or scale-reveal story.
---

# Blender 微縮世界短片（claude-miniature-film）

用 Python 驅動 Blender，做出完成度對標《claude.MP4》（`references/benchmark.md`）的 3D 角色短片：一個小角色穿過一層層「介面」，在微縮世界裡完成一件事，最後鏡頭拉出，回到起點。

每個鏡頭都是一個獨立的 Blender 場景，由 `shots/sXX_*.py` 腳本**從零重建**：同樣的種子、同樣的版圖資料，所以世界在每個鏡頭裡完全一致，連戲寫在資料裡，不靠手工。`lib/mfilm/` 是腳本庫，`examples/claude-keycap-world/` 是逐鏡頭復刻基準片的完整實作。

文件是「總—分」結構：這份 SKILL.md 是**總則**（流程、品質標準、必守規則），`references/` 是**分則**，按需閱讀。

## 創作優先順序

除非使用者明確要求草圖或快速版，**一律以畫面的精緻度、表現力和敘事巧思為最優先**：省事、程式短、渲染快都排在後面。這支基準片的水準來自四件事，缺一不可：

1. **導演設計**：一個貫穿全片的母題（游標）、兩次以上的尺度翻轉、一變多再多成一的奇觀、回到起點的閉環。見 [story.md](references/story.md)。
2. **世界的連續性**：同一個 3D 世界，狀態會跨鏡頭保留（踩過的鍵一直亮著；鍵帽裡的微縮版會留下角色做過的事）。見 [keycaps.md](references/keycaps.md)。
3. **物理渲染質感**：多層透明正確折射、物理景深、全域光照的色溢、寫實植被。見 [materials.md](references/materials.md)、[lighting.md](references/lighting.md)。
4. **剪輯節奏**：硬切卡在 120 BPM 的拍點上，奇觀卡在重拍上。見 [rhythm.md](references/rhythm.md)。

## 品質標準

**驗收以基準片為尺**：[acceptance.md](references/acceptance.md) 把《claude.MP4》拆成四層可以逐條打勾的檢查（A 紙上驗收、B 英雄幀對照、C 數值指紋、D 整片節奏），附每個鏡頭的參考幀和數值帶。八項品質標準是方向，acceptance.md 是及格線。

每支片都以這八項為目標。交付前逐項自評 1–5 分，**每個分數附一張原尺寸渲染圖當證據**（錨點見 [review.md](references/review.md)）；任何一項低於 4 分就繼續改，評分要誠實寫給使用者：

| 項目 | 要做到 | 常見不及格 |
|---|---|---|
| **概念與母題** | 一句話講得清楚的故事；源點符號在開頭、中段、結尾都出現；至少兩次尺度翻轉 | 一連串好看的鏡頭，但沒有因果、沒有回收 |
| **世界連續性** | 同一個世界在每個鏡頭裡版圖一致；角色造成的改變會留下來 | 每個鏡頭各蓋各的佈景，地標位置對不上 |
| **角色一致與表演** | 比例、顏色、部件永遠一致；用眨眼、瞇眼、傾身、轉身、蹦跳演戲；每個動作有預備、壓扁拉伸、落地緩衝 | 角色漂浮滑行、等速移動、落地沒有重量 |
| **材質** | 黏土啞光帶細顆粒；樹脂透明有折射和亮邊；體素地景有地層剖面；草有透光和露珠 | 塑膠感、玻璃像灰色半透明片、體素平塗 |
| **光影** | 每個光有來源（螢幕、太陽、發光的鍵帽）；角色永遠有分離光；用亮度講故事 | 平光、角色融進背景、發光物不照亮周圍 |
| **鏡頭語言** | 低機位、淺景深、前景虛化；每個鏡頭都有相機意圖；景別有遠中近特寫的變化 | 固定機位、所有東西都清晰、景別單一 |
| **轉場** | 每次換世界都穿過一個物理介面（玻璃、鍵帽表面、透鏡），介面有反應 | 換場只有硬切或溶解 |
| **節奏** | 硬切卡拍、奇觀卡重拍、先收後放；長鏡頭給形變和奇觀，短鏡頭給揭示和反應 | 畫面和音樂各走各的 |

## 硬體與渲染預算（先讀）

**Claude 看不到 Blender 視窗**，所有判斷都靠渲染出來的圖。所以流程分兩種機器：

- **製作機**（使用者的電腦，可以很弱，例如 M4 Air 16GB）：寫腳本、建場景、存 `.blend`、渲染**低解析度預覽靜幀**（`previs`：EEVEE、50% 解析度、16 samples，每張幾秒），用 Read 工具看圖迭代。偶爾渲染幾張 `look` 英雄幀確認質感。
- **渲染機**（另一台有獨顯的電腦、雲端 GPU、算圖農場）：整個專案資料夾是自足的（`lib/` 一起複製過去），用 `render.py` 或 `blender -b blend/SXX.blend -a` 渲染整片。時間估算和外包方式見 [render.md](references/render.md)。

使用者說「只做到某一步」「先不渲染」時照辦，交付到那一步為止，並告訴他下一步怎麼接。**不渲染也要驗收**：做完 acceptance.md 的 A 層（紙上驗收：結構、時間點、鏡頭參數逐項對照基準片），在交付報告裡列出結果，並註明 B–D 層等渲染後再驗。

## 完成標準

1. **新子資料夾**：每次製作都用 `scripts/new_project.py` 在目前專案裡建一個新子資料夾，所有檔案都在裡面。
2. **先參數卡，後分鏡**：參數卡經使用者確認（[params.md](references/params.md)），再寫 `STORYBOARD.md`，再寫 `shots.json`，最後才寫鏡頭腳本。
3. **A 層紙上驗收通過**（acceptance.md）：結構落點、鏡頭表、腳本逐項、時間點都對照過基準；`python3 edit.py check` 通過。
4. **B 層靜幀驗收**：每個鏡頭的英雄幀用 `previs` 渲染，`edit.py compare` 和基準幀並排，逐項判斷相符；瑕疵清單（[review.md](references/review.md)）全部通過。
5. **C 層數值驗收**：`edit.py metrics` 全部在容差內，或對每個超出的指標寫出理由。
6. **D 層整片驗收**：每個接縫用 `edit.py strip` 逐幀看過；重拍、閉環都在。
7. **交付**：`.blend`、靜幀、對照圖、（有渲染的話）`out/<slug>.mp4`，加上驗收結果（四層各自通過／未做）、八項自評（附圖）和還能加強的地方。

## 工作流程

### 0. 對齊參數（必做）

讀 [params.md](references/params.md)，按格式準備**推薦參數卡**：主題與源點符號、片長、畫幅、fps、BPM、世界清單、角色、結尾、渲染路線（哪台機器、EEVEE 還是 Cycles）、子資料夾名稱。每一項填推薦值和一句理由，使用者沒提的也要填。發給使用者確認；他說「按推薦」或「直接做」時，在回覆裡列出參數卡然後繼續。

本機沒有 Blender 時，先問使用者要不要安裝（`brew install --cask blender`，約 1 GB），不要自己裝。

### 1. 概念與分鏡

- **完整閱讀**：[benchmark.md](references/benchmark.md)（對標作品的逐鏡頭拆解）、[story.md](references/story.md)、[transitions.md](references/transitions.md)、[review.md](references/review.md)。
- 用 story.md 的**九步配方**設計故事：源點符號 → 變成角色 → 穿越介面 → 尺度反轉 → 母題回收 → 奇觀（一變多、多成一）→ 拉出回到起點。題材不是 Claude Code 時，按 story.md 第 4 節替換符號和世界。
- 寫 `STORYBOARD.md`（模板在 `template/STORYBOARD.md`，範例在 `examples/claude-keycap-world/STORYBOARD.md`）：一句話概念、母題清單、尺度階梯、色彩腳本、能量曲線、分鏡表（每鏡：時間、景別與鏡頭、畫面、觀眾要讀懂的一件事、轉場、聲音）。
- 把分鏡摘要給使用者看。

### 2. 時間網格與版圖：`shots.json`

- 所有時間是**全片秒數**；切點放在 `n × 60/BPM` 上。
- `layout`：跨尺度共用的版圖（池塘、樹、種子、巨人在鍵帽裡的歸一化座標），寫實世界和微縮世界都從這裡讀。
- `state`：會跨鏡頭保留的世界狀態（`lit_trail`：哪顆鍵在幾秒被點亮）。
- 跑 `python3 edit.py check`。
- **做 A 層紙上驗收**（acceptance.md）：九步落點、鏡頭長度分佈、事件時間點對照基準表。新題材時每個鏡頭加 `"ref"` 指向最接近的基準鏡頭。

### 3. 搭專案

```bash
python3 ~/.claude/skills/claude-miniature-film/scripts/new_project.py ./<片名-slug>
python3 ~/.claude/skills/claude-miniature-film/scripts/new_project.py ./<片名-slug> --example claude-keycap-world   # 從基準實作開始
```

### 4. 逐鏡頭製作

每個鏡頭：先讀對應分則（角色 [character.md](references/character.md)、鍵帽 [keycaps.md](references/keycaps.md)、環境 [environments.md](references/environments.md)、特效 [fx.md](references/fx.md)、相機 [camera.md](references/camera.md)、光 [lighting.md](references/lighting.md)、材質 [materials.md](references/materials.md)、API [library.md](references/library.md)）→ 寫 `shots/sXX_<slug>.py` → 建場景並渲染英雄幀 → 用 Read 看圖 → 修正 → 下一個。

```bash
blender -b -P build.py -- --shot S05 --stills hero --preset previs    # 建場景 + 英雄幀（低解析度）
blender -b -P build.py -- --shot S05 --stills t=1.9,4.6 --preset look # 指定秒數、全解析度質感確認
blender -b -P build.py -- --shot S05 --render --preset previs         # 整個鏡頭低解析度（看運動、轉場）
```

以 `examples/claude-keycap-world/shots/` 為起點時，把它當**最低標準**：你的鏡頭至少要一樣精緻，再針對新題材重新設計。

每個鏡頭寫完先做 acceptance.md 的 A3 腳本逐項核對；能渲染時立刻做 B 層：

```bash
python3 edit.py compare S05     # 左：基準幀，右：你的英雄幀 -> out/check/compare_S05_t*.jpg，用 Read 看
python3 edit.py metrics S05     # 亮度、對比、飽和、橘色佔比、冷色佔比對照基準
```

### 5. 檢查轉場與節奏

整片或相鄰兩個鏡頭用 `previs` 渲染後：

```bash
python3 edit.py strip 28.37 --before 0.3 --after 0.5   # 接縫前後逐幀
python3 edit.py sheet S12 --every 6                    # 一個鏡頭的 contact sheet
python3 edit.py assemble && python3 edit.py overview   # 粗剪 + 全片縮圖
```

逐條對照 review.md 的瑕疵清單和 transitions.md 的轉場清單。

### 6. 正式渲染、剪輯、配樂、交付

渲染設定、時間估算、外包方式見 [render.md](references/render.md)；配樂與音效見 [rhythm.md](references/rhythm.md)；你聽不到聲音，用頻譜和分段 RMS 驗證，並告訴使用者你沒辦法試聽。交付時報告：路徑、長度、解析度、每幀耗時、全片縮圖、八項自評（附圖檔名與理由），以及還能加強的地方。

## 必守規則

1. **參數先行。** 參數卡沒確認不寫鏡頭腳本。中途改參數，先改 `shots.json` 和分鏡，再改程式。
2. **每個鏡頭從零重建。** 鏡頭腳本只能讀 `shots.json` 和共用函式（`shots/common.py`），不能依賴上一個鏡頭留下的 `.blend`。隨機一律用 `core.rng(seed)`，不用 `random.random()`。
3. **連戲寫在資料裡。** 跨尺度的地標位置只能來自 `layout`；跨鏡頭的狀態只能來自 `state`。在某個鏡頭裡臨時擺的東西，別的鏡頭看不到。
4. **角色只用 rig。** Clawd 一律用 `character.build()` 建，比例不准改（只能整體縮放 `px`）；橘色只屬於角色系統（Clawd、游標、分身、果實）。
5. **每個鏡頭一件事。** 有原因 → 結果、有變化、有收尾。只有相機在動不算一件事。
6. **每個動作都有物理。** 預備動作、壓扁拉伸、落地緩衝、慣性；不准等速、不准滑行、不准漂浮（刻意的懸空除外，並且要有下落的加速）。用 `character.hop/walk/squash`，不要直接線性移動 root。
7. **每次換世界都穿過介面。** 玻璃、鍵帽表面、透鏡；介面要有反應（漣漪、光、水花）。見 transitions.md。
8. **光要有來源。** 不准憑空補光讓畫面變亮；暗場景靠螢幕和發光的鍵帽，亮場景靠太陽和天空。角色永遠要有分離光。
9. **卡拍。** 切點和重要動作落在 `ctx.beat(n)` 上；動作驅動的切點標 `offbeat`，但動作的高點仍要卡拍。
10. **先看圖再說完成。** 沒用 Read 看過渲染圖的鏡頭不算完成；沒看過 strip 的轉場不算完成。
11. **合規。** Clawd 是 Claude Code 的吉祥物，這是同人／創作用途：不放 Anthropic 標誌、不做官方宣稱；字型、素材（HDRI、植被）只用 CC0 或開源可商用的，並在交付時列出來源。

## 分則（references/）

| 文件 | 內容 | 何時讀 |
|---|---|---|
| [benchmark.md](references/benchmark.md) | 基準片逐鏡頭拆解：鏡頭表、母題、鍵帽地景目錄、拉出揭示逐幀、光影、節奏 | 第 1 步，每次都讀 |
| [acceptance.md](references/acceptance.md) | **驗收標準**：A 紙上／B 靜幀對照／C 數值指紋／D 整片四層，逐鏡頭驗收卡（參考幀＋數值帶） | 每次都讀；第 2、4、5、6 步 |
| [story.md](references/story.md) | 九步敘事配方、母題設計、尺度階梯、能量曲線、換題材的方法、鏡頭長度規則 | 第 1 步，每次都讀 |
| [params.md](references/params.md) | 參數卡格式、`STORYBOARD.md` 寫法、`shots.json` 欄位 | 第 0、1、2 步 |
| [character.md](references/character.md) | Clawd 規格、rig、表演庫、2D→體素→實體、巨人、分身 | 有角色的鏡頭 |
| [keycaps.md](references/keycaps.md) | 鍵帽構造、17 種地景、鍵盤佈局、點亮敘事、按壓、微縮版跟寫實版對位 | 鍵盤段 |
| [environments.md](references/environments.md) | 終端機內部、房間、草原（草的散佈、雛菊、露珠、池塘、遠樹、雲） | 對應世界的鏡頭 |
| [materials.md](references/materials.md) | 全部材質配方與數值、色板、EEVEE／Cycles 透明設定 | 第 4 步 |
| [lighting.md](references/lighting.md) | 五套燈光、世界與霧、亮度敘事、常見問題 | 第 4 步 |
| [camera.md](references/camera.md) | 相機與瞄準點、景深、鏡頭運動庫、跟拍、甩鏡、手持、構圖 | 第 4 步 |
| [transitions.md](references/transitions.md) | 六種轉場的做法與時間、介面原則、檢查清單 | 第 1、5 步 |
| [fx.md](references/fx.md) | 形變、樹生長、分身群集、剛體雨、光膜、漣漪、透鏡、爆閃、水花 | 對應鏡頭 |
| [rhythm.md](references/rhythm.md) | 120 BPM 網格、切點規則、能量曲線、配樂與音效清單、剪輯 | 第 2、6 步 |
| [render.md](references/render.md) | 預設、時間估算、弱機器策略、外包渲染、輸出規格 | 第 4、6 步 |
| [review.md](references/review.md) | 看圖流程、瑕疵清單、八項評分錨點 | 每個鏡頭 |
| [library.md](references/library.md) | `mfilm` 全部函式速查 | 寫腳本時 |

## Blender 陷阱

- **版本**：目標 Blender 4.2 LTS–4.5 LTS。5.x 改了 Action（slots）、合成器（node group）、EEVEE 引擎名稱、天空模型名稱；`core.py`／`project.py` 都做了相容處理，但 5.x 未實測，遇到錯誤先看 API 是否改名。
- **單位**：1 BU = 1 cm（`unit_scale = 0.01`）。相機的物理景深因此自帶微縮感；但**燈光能量不隨單位縮放**，數值一律用 `look` 靜幀調，不要憑感覺。
- **`frame_set` 才會更新動畫值**：要讀某一幀的位置（起跳點、跟拍），先 `scene.frame_set(f)`。`character.hop/turn`、`camera.whip/follow_bake` 已處理。
- **剛體要 bake**：`swarm.rain_rigidbody` 會在建場景時 bake，否則平行渲染或跳幀時模擬會錯。改了任何東西就重建該鏡頭。
- **EEVEE 的透明疊透明**是螢幕空間近似：鍵帽疊鍵帽、鍵帽裡有水時，前後關係可能錯。鍵帽特寫和拉出鏡頭用 Cycles 渲染（render.md）。
- **Track To 的正上方**：俯拍時瞄準點要比相機低、並在 Y 方向偏一點點，否則相機會翻轉。
- **轉向角度不會自動取最短路徑**：從 170° 轉到 −170° 會繞一大圈，必要時自己加減 360°。
- **Geometry Nodes 的屬性**：`reveal` 需要點上有 `order`；`flock` 需要 `start/target/order/size`；草地散佈需要地面有 `density`。缺了不會報錯，只會什麼都看不到。
- **GN 修改器的輸入**用 `gn.set_input(mod, '名稱', 值, 幀)` 設定和打關鍵幀，不要直接寫 `mod["Socket_2"]`（編號會變）。
- **背景模式下的 `bpy.ops`**：需要選取物件的操作（剛體、bake）要包在 `bpy.context.temp_override(...)` 裡，庫裡已處理；自己寫時照抄。
