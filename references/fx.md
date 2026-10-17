# 特效與形變

所有「東西一個個出現」「一群東西飛到某處」的效果，都用兩個 Geometry Nodes 群組實作（`mfilm.gn`），用 `gn.set_input(mod, 'Progress', 值, 幀)` 打關鍵幀：

| 群組 | 點上需要的屬性 | 輸入 | 行為 |
|---|---|---|---|
| `reveal_group(name, 實例物件)` | `order`（0–1），可選 `rot` | Progress、Width、Gap、Squash | Progress 掃過 order 時，該點的實例從 0 長到 1（smootherstep＋小過衝）。Gap < 1 留縫、> 1 縫消失；Squash = 1 把實例壓成薄片（2D） |
| `flock_group(name, 實例物件或集合)` | `start`、`target`、`order`、`size`，可選 `spin`、`rot`、`variant` | Progress、Width、Arc | Progress 掃過 order 時，實例從 start 飛到 target（弧線高 Arc，飛行中翻滾 spin）。`gravity=True` 用 t² 模擬下落 |

點雲用 `gn.points_object(name, 位置, {屬性: 值列表})` 建。**缺屬性不會報錯，只會看不到**。

## 1. 誕生：游標 → 2D → 體素 → 實體（S01）

| 時間 | 階段 | 做法 |
|---|---|---|
| 0.5–2.5 s | 游標閃爍 | `env.blink(cursor, ctx.beat, 1, 5)`：一拍亮一拍暗 |
| 2.6–3.6 s | 打字成形 | `voxel.sprite_points(n=2, cursor_x=游標位置)`：order = 離游標的距離（像從游標往外打字）；`reveal_group(Squash=1, overshoot=1.4)`；游標 2.9 s 消失（被像素接手）；角色腳下橘光 0 → 400 |
| 3.6–4.2 s | 2D 停留 | 平面像素圖完整呈現，底部橘光最亮（基準幀 S01_t03.60） |
| 4.2–4.8 s | 擠出 | 換成 `voxel.voxel_points(order_by='depth', skip_eyes=True)`：正面一層先出現，一層層往後長；眼睛另放深色方塊（基準幀 S01_t04.80：網格清楚的體素體） |
| 5.5–5.85 s | 網格閉合 | Gap 0.9 → 1.04（縫消失） |
| 5.9 s | 換成實體 | 隱藏體素、顯示 rig（`C.show`），壓扁 0.14 → `back` 回正（基準幀 S01_t06.00） |
| 6.4 s 起 | 活過來 | 眨眼、瞇眼、走兩步（基準幀 S01_t07.50） |

相機在 4.2–5.9 s 環繞 30°，讓觀眾看到「它原來是平的，現在有厚度了」。

## 2. 樹的生長（S12）

| 時間 | 階段 | 做法 |
|---|---|---|
| 36.0–37.6 s | 樹幹 | `voxel.tree()` → `trunk_points()`（order 由下往上）→ `reveal_group(width=0.05)`。最初幾幀是一根和游標同比例的深色方柱 |
| 37.2–39.0 s | 樹冠 | 樹冠點雲（order 由內往外）→ `reveal_group(width=0.15)` |
| 38.3–39.3 s | 光束 | `FX.beam` 斜穿樹冠 |
| 39.0–39.8 s | 結果 | `swarm.fruit_grow`：分身在樹冠表面隨機冒出 |
| 40.0–40.9 s | 落下 | `swarm.fruit_fall`：flock gravity，**40.0 s 是全片重拍** |

## 3. 分身雨（S13）

`swarm.rain_rigidbody`：分身是共用網格的連結複本，帶剛體；釋放前是 kinematic（固定在空中），到各自的釋放幀才開始模擬；地面、樹幹是被動碰撞體。建場景時就 bake。

- 重力 `gravity=300`（BU/s²）：1 cm 世界的真實重力是 981，看起來像「小玩具掉下來」；300 讀起來像「大東西落下」，符合草原內部的尺度感。
- 數量 60–120；碰撞形狀 BOX；摩擦 0.7、彈性 0.25。

## 4. 分身海（S14）

`swarm.pile`：連結複本隨機散在樹下，15 % 側躺、10 % 翻倒，旋轉加噪聲修改器（蠕動）。避開樹幹和角色（`avoid`）。

## 5. 多成一：堆成巨人（S15）

`swarm.assemble_giant`：

- 目標 = Clawd 以 n = 1.5 格／px 體素化、只留外殼、去掉眼睛格 → 約 680 個位置。
- 起點 = 樹下分身海的範圍內隨機。
- order = 目標高度 × 0.8 + 隨機 0–0.12 → **由下往上堆**，最後幾個從頂上落下（參差的頂部）。
- 飛行弧線 Arc 4、翻滾 spin、Progress 43.2 → 47.4 s 線性（每個實例自己有 smootherstep）。
- 堆到 45 % 時出現深色核心，讓眼洞是黑的。

## 6. 會走的巨人（S16）

`swarm.giant_rig`：用 `character.build(px=0.72)` 建一副隱形的 rig，把每個部件的分身點雲掛在對應的骨架上（身體 → hip，手臂 → 肩，腳 → 腳頂）。所以 `C.walk(giant, …)`、`C.wave(giant, …)` 照用；步伐要慢（step 12、swing 18、bob 0.15），才有重量。

## 7. 介面特效（`mfilm.fx`）

| 函式 | 效果 | 時間建議 |
|---|---|---|
| `membrane(name, loc, radius, flatten, axis)` + `membrane_pass(o, 進, 滿, 出)` | 光膜（扁球、菲涅爾發光） | 角色穿過前 0.3 s 亮起 |
| `ripple(name, loc, radius, f0, dur, normal)` | 同心圓擴散漣漪 | 20–34 幀 |
| `glow_seed(name, loc, f_on)` | 地面暖色小光點＋點光 | 閃到 1.4 再回 1.0 |
| `beam(name, loc, height, radius, tilt, f0, f1)` | 體積光束 | 約 1 s |
| `lens_bubble(name, loc, r1, f_glint, f_open, f_full)` | 光點 → 圓環 → 玻璃球 | 光點 4–5 幀、張開 5–6 幀 |
| `burst(name, loc, f)` | 爆閃：點光尖峰＋方塊四散＋漣漪 | 16 幀 |
| `splash(name, loc, f)` | 泡沫方塊濺起（鍵帽內） | 14 幀 |
| `ballistic(objs, f0, vels, life)` | 任何物件的拋物線 | |

## 8. 特效檢查

- [ ] reveal／flock 的 Progress 從 0 開始、到 > 1 結束（不然最後幾個不會完全出現）
- [ ] 形變的每個階段都有足夠時間被看清（≥ 0.8 s）
- [ ] 剛體已 bake（`.blend` 存檔前），沒有物件穿模或抖動
- [ ] 介面特效都在動作的那一幀觸發（落地、撞擊、穿過）
