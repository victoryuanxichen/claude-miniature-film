# 材質配方

所有材質都在 `mfilm.materials`，用名字快取（同名呼叫兩次回傳同一個材質）。顏色寫 sRGB hex，函式內轉成線性。

## 1. 色板（從基準片取樣）

| 名稱 | hex | 用在 |
|---|---|---|
| `clawd` | `#cc6549` | 角色、游標、分身、果實（**只有角色系統能用橘色**） |
| `clawd_eye` | `#120c0b` | 眼睛 |
| `void` / `void_hi` | `#05080d` / `#191d24` | 終端機空間 |
| `floor` | `#0b1017` | 光滑深色地面 |
| `code` | `#9aa4ae` | 程式碼膠囊 |
| `resin` | `#a9bfcc` | 樹脂鍵帽（看起來會是 `#4d6472` 一帶） |
| `grass` / `grass_dark` / `grass_lit` | `#4f8a2a` / `#2f5a1a` / `#8fca4a` | 草（根 → 中 → 葉尖） |
| `sky_top` / `sky_hor` | `#82ade9` / `#c8d8e7` | 天空 |
| `far_tree` | `#9cb8e2` | 遠樹在霧後的顏色（目標值，由霧產生） |
| `water` / `water_deep` / `foam` | `#3d8fb8` / `#1d4f7a` / `#e8f4f8` | 水 |
| `snow` / `ice` / `sand` / `rock_dark` | `#eef3f6` / `#b9dbea` / `#d9c7a0` / `#2a2c31` | 地景 |
| `lava` | `#ff3a22` | 紅光鍵（全片唯一紅色） |
| `leaf` / `leaf_lit` / `bark` | `#3f8f2e` / `#77c84a` / `#3d3833` | 體素樹 |

## 2. 配方

| 函式 | 物件 | 關鍵數值 | 為什麼 |
|---|---|---|---|
| `clay()` | Clawd、分身 | 粗糙度 0.62、Specular 0.35、SSS 0.12（半徑 1, .35, .2，scale 0.08）、Coat 0.06、噪聲凹凸 260/0.03 | 啞光軟膠的「可以捏」感；SSS 讓邊緣偏暖不死黑；凹凸讓特寫有顆粒 |
| `eye()` | 眼睛 | 粗糙度 0.35 | 稍微有點亮光，眼睛才有神 |
| `resin()` | 鍵帽側壁 | 透射 1、IOR 1.5、粗糙度 0.03、體積吸收 0.18（`#7f9aa8`） | 越厚越藍灰；側壁出現折射和亮邊 |
| `resin(frost=True)` | 鍵帽頂面 | 粗糙度 0.22 | 霧面頂，微縮地景從頂面看下去有一點柔化 |
| `water()` | 鍵帽裡的水、池塘 | 透射 1、IOR 1.33、波紋凹凸 | |
| `matte(glow_attr='glow')` | 體素地景 | 粗糙度 0.85；自發光 = 底色 × `obj['glow']` × 2.5 | 「從內部亮起」的機制 |
| `emission()` | 程式碼、螢幕像素、城市燈 | 純自發光，可接 `glow` | |
| `fresnel_glow()` | 螢幕光膜、透鏡亮邊 | Layer Weight Facing^(1/power) × Alpha → 自發光／透明混合 | 只有邊緣亮，中間透明；Value 節點 `Alpha` 可打關鍵幀 |
| `ripple()` | 漣漪 | 依 UV 中心距離算環，Value 節點 `Phase`（0→1 擴散）、`Alpha`（淡出） | |
| `grass_blade()` | 草葉 | Principled 65 % + Translucent 35 %，顏色沿 UV.y 漸層，雙面 | 逆光時整片草發亮 |
| `bark()` | 樹幹 | 噪聲明暗斑（`#23211f`–`#6d675f`）＋強凹凸 | 基準片樹幹是迷彩似的深淺斑 |
| `leaf()` | 樹冠方塊 | 用 Object Info Random 給每塊不同綠，SSS 0.15 | 方塊樹冠不會一片死綠 |
| `sky_dome()` | 雲 | 噪聲遮罩白色自發光＋透明 | 物理天空沒有雲 |
| `volume_beam()` | 光束 | 自發光體積 | |

## 3. 透明與折射設定

`transparent_settings(m)` 會依版本設定：`surface_render_method = 'DITHERED'`、`use_raytrace_refraction`（4.2+）或 `use_screen_refraction`（舊版）、`use_transparent_shadow`、`thickness_mode = 'SLAB'`。

- **EEVEE**：折射是螢幕空間的近似。單層透明（光膜、單顆鍵帽）OK；**鍵帽疊鍵帽、鍵帽裡有水**時前後關係可能錯，這些鏡頭用 Cycles（render.md）。
- **Cycles**：`transmission_bounces = 16`、`transparent_max_bounces = 32` 才夠穿過一排鍵帽；`caustics_refractive` 關閉（否則噪點爆炸），所以鍵帽外殼和水都設 `visible_shadow = False`，讓內部的光照得出來。

## 4. 質感檢查（看原尺寸圖）

- [ ] 黏土：亮面有柔和的大高光，暗面不死黑（有 SSS 的暖邊），特寫看得到顆粒
- [ ] 鍵帽：側壁有亮邊和折射扭曲；頂面是霧的；裡面的地景比外殼亮
- [ ] 體素地景：側面看得到地層（頂色、土、石）
- [ ] 草：逆光時葉緣發亮；有露珠的高光點；前景草完全虛化
- [ ] 沒有任何物件用到角色的橘色（除了角色系統）
