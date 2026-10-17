# `mfilm` 速查

鏡頭腳本的標準開頭：

```python
from mathutils import Vector
from mfilm import camera as CAM, character as C, core, env as E, fx as FX, gn, keycap as K
from mfilm import lighting as L, materials as M, swarm as SW, voxel as VX
from . import common as S          # 這部片共用的佈景函式

def build(ctx):
    g = ctx.g                       # 全片秒數 -> 本地幀
    ...
```

幀與時間都由 `ctx` 換算：`ctx.g(全片秒)`、`ctx.f(切入後秒)`、`ctx.beat(n)`、`ctx.cut_in`、`ctx.cut_out`、`ctx.last`、`ctx.H`（handles）。

## `project`：鏡頭生命週期

| 函式 | 說明 |
|---|---|
| `Ctx(project_dir, shot_id, preset)` | 讀 `shots.json`；屬性 `shot`、`start`、`end`、`fps`、`bpm`、`layout`、`state`、`sc` |
| `ctx.setup()` / `ctx.finish(save)` | 重設場景、時間範圍、拍點標記／套預設、設輸出路徑、存 `blend/<id>.blend`（`build.py` 會呼叫） |
| `ctx.lit_keys(t)` / `ctx.lit_events()` | `lit_trail` 裡 t 之前已點亮的鍵／本鏡頭內發生的點亮（鍵號, 本地幀） |
| `apply_preset(sc, name)` | `clay`／`previs`／`look`／`final`／`cycles_draft`／`cycles`（render.md） |
| `render_stills(sc, frames, folder, prefix)` / `render_range(sc, f0, f1, folder)` | 渲染靜幀／一段 |

## `core`：場景、物件、關鍵幀

| 函式 | 說明 |
|---|---|
| `box(name, lo, hi, c, mat, bevel, segs, par)` | 軸對齊盒子（從角 lo 到角 hi），可倒角、可掛父物件 |
| `empty(name, loc, c, size, kind, par)` / `parent(child, par)` | 空物件／設父物件（之後 location 是父空間座標） |
| `mesh_obj(name, verts, faces, c, mats, smooth, mat_idx)` | 從頂點和面建網格 |
| `join_meshes(name, objs, c)` | 套用修改器後合併成一個靜態網格（供大量實例化） |
| `coll(name, parent)` / `link(obj, c)` | 集合 |
| `key(idb, path, frame, value, ease, index)` | 插一個關鍵幀；`ease` 決定**離開**這個鍵的曲線：`ease`（貝茲）、`linear`、`const`、`back`、`bounce`、`elastic`、`sine`、`quad(_in/_out)`、`cubic(_in/_out)`、`expo(_in/_out)` |
| `keys(idb, path, [(f, v, ease), …])` | 多個鍵 |
| `key_visible(o, f, visible)` | 硬切顯示／隱藏 |
| `noise_mod(idb, path, …)` | 在已有關鍵幀的通道上加噪聲（手持、蠕動） |
| `fcurves_of(id)` | 取 F-curve（相容 4.4+ 的 slotted actions） |
| `Clock(fps, bpm, t0)` | 秒／拍 → 幀（`ctx` 已包好，通常不用直接用） |
| `rng(seed)` | 決定性亂數，**唯一允許的亂數來源** |
| `hexcol('#cc6549')` | sRGB hex → 線性 RGBA |
| `sset(obj, attr, v)` / `try_enum(obj, attr, *vals)` | 版本相容的設定 |
| `inp(node, *names, type)` / `outp(...)` / `setin(node, v, *names)` | 依名稱（和型別）找節點插槽 |

## `gn`：Geometry Nodes

| 函式 | 說明 |
|---|---|
| `points_object(name, positions, {attr: values})` | 只有頂點的網格，帶點屬性（float 或 3-tuple） |
| `reveal_group(name, source)` | 依 `order` 長出實例。輸入 Progress、Width、Gap、Squash |
| `flock_group(name, source, collection, arc, gravity, width)` | 依 `order` 從 `start` 飛到 `target`。需要 `size`；可選 `spin`、`rot`、`variant` |
| `scatter_group(name, collection, density, seed, scale, tilt)` | 在面上散佈集合實例，遮罩 = 點屬性 `density` |
| `add_modifier(obj, ng)` / `set_input(mod, 名稱, 值, 幀, ease)` | 加修改器／設定並打關鍵幀 |
| `GN(name)` | 自己組節點的小型建構器（`math`、`vmath`、`xyz`、`attr`、`maprange`、`instance`、`set_position`、`random`…） |

## `materials`

`clay`、`eye`、`resin(frost)`、`water`、`glass`、`emission(glow_attr)`、`fresnel_glow`、`ripple`、`dark_gloss`、`metal`、`matte(glow_attr)`、`grass_blade`、`bark`、`leaf`、`sky_dome`、`volume_beam`、`principled(...)`（通用）。`col('clawd')` 取色板。`value_node(mat, 'Alpha')` 取材質裡可打關鍵幀的 Value 節點。數值見 materials.md。

## `lighting`

| 函式 | 說明 |
|---|---|
| `light(name, kind, loc, target, energy, color, size, size_y)` | POINT／SPOT／AREA／SUN，建立時對準 target |
| `sun(name, elev, az, strength)` | 太陽（方位 0 = +Y，順時針） |
| `world_color` / `world_gradient` / `world_sky` / `world_haze` / `haze_box` | 世界與大氣 |
| `rig_terminal` / `rig_room_night` / `rig_keyboard` / `rig_meadow` / `rig_endcard` | 五套燈，回傳 dict 方便打關鍵幀 |
| `pulse(lamp, [(f, energy)])` | 燈光能量動畫 |

## `camera`

| 函式 | 說明 |
|---|---|
| `camera(name, loc, target, lens, fstop)` | 回傳 `(cam, target_empty)`，Track To + 對焦在 target |
| `move(obj, [(f, loc, ease)])` | 相機或瞄準點的路徑 |
| `orbit(cam, center, radius, height, deg_from, deg_to, f0, f1)` | 圓弧環繞 |
| `follow_bake(obj, subject, f0, f1, offset, smooth)` | 有延遲的跟拍（取樣角色位置、平滑後寫鍵） |
| `whip(target, f0, f1, to_loc)` | 甩鏡 |
| `handheld(cam, target, f0, loc_amp, aim_amp)` | 手持晃動 |
| `dof` / `rack` / `fstop_keys` / `lens_keys` | 景深、拉焦、光圈、變焦 |

## `character`

| 函式 | 說明 |
|---|---|
| `build(name, loc, px, facing_deg)` → `Rig` | 建 Clawd；`Rig.find(name)` 找回 |
| `static_mesh(name, px, mat)` | 合併成一個網格（分身、微縮版、小點） |
| `show(rig, f, visible)` | 整隻角色顯示／隱藏 |
| `place` / `hop` / `walk` / `squash` / `blink` / `squint` / `tilt` / `turn` / `wave` / `legs_pose` / `idle` | 表演庫（character.md 第 4 節） |
| `heading(dx, dy)` | 面向某方向的 yaw（弧度） |
| 常數 `PX`、`BODY`、`ARMS`、`LEGS`、`EYES`、`HIP_Z` | 造型定義（px 單位） |

## `voxel`

| 函式 | 說明 |
|---|---|
| `clawd_cells(n, shell)` | Clawd 體素化，回傳 `(ix, iy, iz, part)` |
| `sprite_points(name, n, cursor_x)` | 2D 像素圖點雲，`order` = 打字順序 |
| `voxel_points(name, n, order_by, skip_eyes)` | 體素點雲，`order_by`：`depth`（擠出）、`bottom`（堆疊）、`random` |
| `cube_obj(name, size, mat, bevel)` | 給 reveal／flock 用的倒角方塊（隱藏） |
| `terrain(name, nx, ny, cell, height_fn, color_fn, mats, origin, side_fn)` | 高度場方塊地形（只建露出的面） |
| `tree(name, base, cell, trunk_h, trunk_w, canopy_r, fruits)` / `trunk_points` | 體素樹（樹幹、樹冠點雲、果實位置） |
| `fbm(x, y, …)` | 決定性噪聲 |
| `SPRITE` | 像素圖字串 |

## `keycap`

| 函式 | 說明 |
|---|---|
| `build_keyboard(origin, seed, glow, cell, biomes, lights, only, meadow_kw)` → `Keyboard` | 整把鍵盤；`kb.keys[鍵號]` 是每顆鍵的根物件，`kb.top(鍵號)` 是頂面中心的世界座標 |
| `assign_biomes(rows, seed, hero, red, overrides)` | 決定每顆鍵的地景 |
| `build_key(kid, biome, u, h, loc, cell, glow)` / `shell(name, u, h)` | 單顆鍵／外殼 |
| `light_up(kb, kid, f)` / `set_key_glow` / `set_all_glow` / `wave_on(kb, f0, f1, origin)` | 點亮 |
| `press(kb, kid, f)` | 按下回彈 |
| `diorama_point(kb, kid, u, v)` | 微縮地景表面上某點的世界座標 |
| `BIOMES` / `b_*` | 地景函式（keycaps.md 第 2 節） |

## `env`

| 函式 | 說明 |
|---|---|
| `terminal_space(c, prompt, with_cursor)` | 終端機內部 |
| `cursor(name, loc)` / `blink(obj, ctx.beat, 起拍, 止拍)` / `chevron` / `code_rows` | 游標、閃爍、提示符、程式碼膠囊 |
| `monitor(c, screen_center, screen_size, desk_z)` / `screen_sprite(name, loc, pixel, cursor_blink)` | 顯示器／螢幕上的 2D 小怪 |
| `room(c, …)` | 房間全景 |
| `meadow(c, center, radius, size, dense_center, dense_r, grass_density, layout)` | 草原（回傳 `pos`：layout 換算後的世界座標） |
| `layout_to_world(uv, size)` / `ground_height(x, y)` | 版圖換算／地面高度 |
| `HERO_LAYOUT` | 預設版圖 |

## `fx`

`membrane` + `membrane_pass`、`ripple`、`glow_seed`、`beam`、`lens_bubble`、`burst`、`splash`、`ballistic`（fx.md 第 7 節）。

## `swarm`

`mini(cell)`、`fruit_grow`、`fruit_fall`、`rain_rigidbody(gravity)`、`pile`、`assemble_giant`、`giant_rig`（fx.md 第 3–6 節）。

## 專案工具（system Python + ffmpeg，不需要 Blender）

| 指令 | 說明 |
|---|---|
| `python3 edit.py check` | 鏡頭首尾相接、切點對拍 |
| `python3 edit.py compare SXX [--t 秒]` | 基準幀和你的英雄幀並排（acceptance.md B 層） |
| `python3 edit.py metrics [SXX …]` | 數值指紋對照基準容差（C 層）；`filmmetrics.py` 是量測程式，基準的 `metrics.json` 用同一份程式產生 |
| `python3 edit.py strip 秒` / `sheet SXX` / `assemble` / `overview` | 接縫逐幀、contact sheet、粗剪、全片縮圖 |
