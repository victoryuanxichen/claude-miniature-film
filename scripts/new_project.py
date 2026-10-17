#!/usr/bin/env python3
"""Create a project folder for a miniature film.

    python3 ~/.claude/skills/claude-miniature-film/scripts/new_project.py ./my-film
    python3 ~/.claude/skills/claude-miniature-film/scripts/new_project.py ./my-film --example claude-keycap-world

Copies the template (build.py, render.py, edit.py, shots.json, STORYBOARD.md, shots/) and
the mfilm library into <dir>/lib so the folder is self-contained: zip it and render it on
any machine with Blender 4.2+. --example also copies that example's shots.json, storyboard
and shot modules (a working starting point you then redesign).
"""
import argparse
import os
import shutil
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument('dir')
ap.add_argument('--example', default=None)
ap.add_argument('--force', action='store_true')
a = ap.parse_args()

dst = os.path.abspath(a.dir)
if os.path.exists(dst) and os.listdir(dst) and not a.force:
    sys.exit(f'{dst} exists and is not empty (use --force to add files into it)')
os.makedirs(dst, exist_ok=True)
for name in ('build.py', 'render.py', 'edit.py', 'filmmetrics.py', 'shots.json', 'STORYBOARD.md'):
    shutil.copy2(os.path.join(SKILL, 'template', name), os.path.join(dst, name))
shutil.copytree(os.path.join(SKILL, 'template', 'shots'), os.path.join(dst, 'shots'), dirs_exist_ok=True)
shutil.copytree(os.path.join(SKILL, 'lib', 'mfilm'), os.path.join(dst, 'lib', 'mfilm'), dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('__pycache__'))
if a.example:
    ex = os.path.join(SKILL, 'examples', a.example)
    if not os.path.isdir(ex):
        sys.exit(f'no example {a.example!r}; have: {os.listdir(os.path.join(SKILL, "examples"))}')
    for name in ('shots.json', 'STORYBOARD.md'):
        if os.path.exists(os.path.join(ex, name)):
            shutil.copy2(os.path.join(ex, name), os.path.join(dst, name))
    shutil.copytree(os.path.join(ex, 'shots'), os.path.join(dst, 'shots'), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(os.path.join(SKILL, 'benchmark', 'ref'), os.path.join(dst, 'reference', 'ref'), dirs_exist_ok=True)
shutil.copy2(os.path.join(SKILL, 'benchmark', 'metrics.json'), os.path.join(dst, 'reference', 'metrics.json'))
for d in ('assets', 'blend', 'out/frames', 'out/stills', 'out/check'):
    os.makedirs(os.path.join(dst, d), exist_ok=True)
open(os.path.join(dst, '.gitignore'), 'w').write('out/\nblend/\n__pycache__/\n*.blend1\n')
print(f'project ready: {dst}')
print('next: edit STORYBOARD.md + shots.json, then\n'
      f'  cd {dst} && blender -b -P build.py -- --shot S01 --stills hero --preset previs')
