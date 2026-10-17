# claude-miniature-film

A Claude Code skill for making cinematic 3D miniature-world character shorts with **scripted Blender** (Python `bpy`, Geometry Nodes, EEVEE / Cycles), benchmarked against a 60-second reference film: a terminal cursor comes alive as Clawd (the Claude Code pixel critter), walks out of the screen onto a keyboard of clear resin keycaps with voxel worlds sealed inside, dives into one, plants the cursor as a seed, grows a tree of copies that assemble into a giant, and pulls back out to the terminal.

說明文件以繁體中文撰寫。

## Install

```bash
git clone https://github.com/victoryuanxichen/claude-miniature-film.git ~/.claude/skills/claude-miniature-film
```

Claude Code picks it up automatically; it triggers on requests for Blender / scripted 3D character shorts, miniature worlds, keycap dioramas, scale reveals, or "remake claude.MP4".

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Main rules: workflow, quality bar, must-follow rules, Blender pitfalls |
| `references/` | Story recipe, character, keycaps, environments, materials, lighting, camera, transitions, FX, rhythm, render, review, **acceptance**, API |
| `lib/mfilm/` | `bpy` library: Clawd rig & acting, voxel morphs, keycaps + 17 biomes, meadow scatter, swarm / giant, interface FX, camera language |
| `examples/claude-keycap-world/` | Shot-by-shot Blender implementation of the benchmark (17 shots + black) |
| `template/` | Project template: `build.py`, `render.py`, `edit.py`, `filmmetrics.py`, `shots.json`, `STORYBOARD.md` |
| `benchmark/` | Reference frames per hero moment, contact sheets, transition strips, numeric fingerprint (`metrics.json`) |
| `scripts/new_project.py` | Scaffold a self-contained project folder |

## Quick start

```bash
python3 scripts/new_project.py ./my-film --example claude-keycap-world
cd my-film
python3 edit.py check                                            # timing vs beat grid
blender -b -P build.py -- --shot S05 --stills hero --preset previs
python3 edit.py compare S05 && python3 edit.py metrics S05      # acceptance vs benchmark
```

Targets Blender 4.2–4.5 LTS. Status: library and all shot scripts pass static checks and a mocked-`bpy` run; not yet executed in real Blender.

Benchmark frames are stills from a third-party reference video, included for study and acceptance comparison only.
