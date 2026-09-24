#!/usr/bin/env python3
"""Cut a finished skin sheet into per-frame PNGs.
Usage: python3 cut_from_cells.py <skin>/<skin>_cells.json <skin>/<skin>_DRAWN.png <out_dir>
Writes sk_<skin>_<frameKey>.png, one per cell, at the exact base-frame size.
Empty cells -> WARNING (missing frame, the game renders that frame without the skin).
Pixels drawn outside every cell -> WARNING (they would be lost)."""
import json,sys,os
from PIL import Image
cfg=json.load(open(sys.argv[1]));sheet=Image.open(sys.argv[2]).convert('RGBA');out=sys.argv[3]
os.makedirs(out,exist_ok=True)
if sheet.size!=(cfg['sheet']['w'],cfg['sheet']['h']):sys.exit(f"ERROR sheet is {sheet.size}, template is {cfg['sheet']['w']}x{cfg['sheet']['h']} - do not resize the template")
a=sheet.getchannel('A');missing=[];mask=Image.new('L',sheet.size,0)
for k,c in cfg['frames'].items():
    box=(c['x'],c['y'],c['x']+c['w'],c['y']+c['h']);mask.paste(255,box)
    im=sheet.crop(box)
    if im.getchannel('A').getextrema()[1]==0:missing.append(k);continue
    im.save(f"{out}/sk_{cfg['skin']}_{k}.png")
from PIL import ImageChops
outside=sum(1 for v in ImageChops.subtract(a,mask).tobytes() if v)
print(f"{cfg['skin']} ({cfg['mode']}): {len(cfg['frames'])-len(missing)}/{len(cfg['frames'])} frames cut")
if missing:print("WARNING missing frames:",", ".join(missing))
if outside:print(f"WARNING {outside} drawn pixels are outside the cells and were ignored")
