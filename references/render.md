# 渲染：預設、預算、外包

## 1. 預設（`project.PRESETS`）

| 預設 | 引擎 | 解析度 | samples | 光追 | 動態模糊 | Bloom | 用途 |
|---|---|---|---|---|---|---|---|
| `clay` | Workbench | 50 % | — | — | — | — | 只看構圖、走位（最快） |
| `previs` | EEVEE | 50 % | 16 | 關 | 關 | 關 | **日常迭代**：英雄幀、整段低解析度看運動 |
| `look` | EEVEE | 100 % | 64 | 開 | 開 | 開 | 質感確認（幾張） |
| `final` | EEVEE | 100 % | 128 | 開 | 開 | 開 | 正式輸出（大部分鏡頭） |
| `cycles_draft` | Cycles | 50 % | 64 | — | 開 | 開 | 檢查透明疊透明 |
| `cycles` | Cycles | 100 % | 512（自適應、OIDN 降噪） | — | 開 | 開 | 鍵帽特寫、拉出鏡頭 |

用法：`build.py --preset <名>`（建場景時）或 `render.py --preset <名>`（改已存的 `.blend`）。

## 2. 哪些鏡頭用 Cycles

EEVEE 的折射是螢幕空間近似，**鍵帽疊鍵帽、鍵帽裡有水、透鏡**會出錯。建議：

| 鏡頭 | 引擎 |
|---|---|
| S01–S04（終端機） | EEVEE `final` |
| S05、S08、S17（鍵帽特寫、拉出） | Cycles |
| S06、S07（鍵盤中遠景） | EEVEE `final`，先用 `cycles_draft` 比對一張，差太多就改 Cycles |
| S09–S16（草原） | EEVEE `final`（草太多，Cycles 很慢；S16 的透鏡幾幀可以單獨用 Cycles） |

## 3. 時間估算（未實測，僅供規劃）

1080p，每幀秒數的量級：

| 機器 | previs | final（EEVEE） | cycles（鍵帽） | cycles（草原） |
|---|---|---|---|---|
| MacBook Air M4 16GB | 2–6 s | 15–40 s | 2–6 分 | 5–15 分（可能記憶體不足） |
| 桌機 RTX 4070 級 | <1 s | 2–6 s | 20–60 s | 1–3 分 |
| 桌機 RTX 4090 級 | <1 s | 1–3 s | 8–25 s | 30–90 s |

全片 60 s × 30 fps = 1800 幀，加 handles 約 2000 幀。以 RTX 4070 級、EEVEE 為主 + 3 個 Cycles 鏡頭（約 650 幀）估計：EEVEE 約 2 小時，Cycles 約 5–10 小時。

**先渲染一張 `look` 和一張 `cycles` 英雄幀，量出實際每幀時間，再乘幀數**，把估算寫給使用者。

## 4. 弱機器策略（製作機）

- 日常只用 `previs` 渲染英雄幀（每鏡 3–6 張）；整段運動用 `previs` 或 `clay` 渲染 50 % 解析度。
- 草原鏡頭先把 `grass_density` 降到 4–6 看構圖，最後再調回 16–22。
- `only={…}` 只建鏡頭裡看得到的鍵帽。
- 關掉不需要的東西：遠景鏡頭不要露珠、不要雲（`meadow(clouds=False)`）。
- 使用者說「先不渲染」時，交付到建好的 `.blend` 和英雄幀為止。

## 5. 外包渲染（渲染機）

專案資料夾是自足的（`new_project.py` 會把 `lib/mfilm` 複製進去），`.blend` 裡已經存好所有幾何、動畫、bake 好的剛體、輸出路徑。

```bash
# 在渲染機上（Blender 版本與製作機相同的大版本）
blender -b blend/S05.blend -P render.py -- --preset cycles            # 一個鏡頭
for s in S01 S02 S03; do blender -b blend/$s.blend -P render.py -- --preset final; done
blender -b blend/S12.blend -a                                          # 直接用存檔裡的設定
```

- **可續傳**：已存在的幀會跳過（`use_overwrite = False`、`use_placeholder = True`），中斷後重跑同一行即可；多台機器可以共用同一個輸出資料夾平分幀。
- **輸出**：`out/frames/<鏡號>/0001.png`（16-bit PNG，本地幀號，包含 handles）。剪輯時 `edit.py` 只取 CUT_IN…CUT_OUT。
- **雲端／算圖農場**：任何能跑 Blender 4.2+ 的 GPU 機器都可以；需要上傳 `.blend` 的農場時，先在製作機執行 `bpy.ops.file.pack_all()`（目前庫裡沒有外部貼圖，通常不需要）。
- 改了任何東西：在製作機重建該鏡頭的 `.blend`，再送去渲染。

## 6. 交付規格

- 最終 MP4：H.264、CRF 16、yuv420p、`+faststart`（`edit.py assemble`）。
- 保留 `out/frames/` 的 PNG 序列，方便調色或重剪。
- 報告：每個鏡頭的引擎、samples、每幀實際耗時、總耗時。
