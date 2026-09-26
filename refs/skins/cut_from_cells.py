#!/usr/bin/env python3
"""Cut a finished skin sheet into per-frame PNGs.
Usage: python3 cut_from_cells.py <skin>/<skin>_cells.json <skin>/<skin>_DRAWN.png <out_dir>
Writes sk_<skin>_<frameKey>.png, one per cell.
Legacy sheets (no "scale" field, e.g. geka/bk K1b kit: cell == native frame size) are cut as-is,
unchanged from before.
F4a sheets (schema 1: "scale"/"margin" fields, cell = base frame x scale + a transparent margin):
each cut PNG is downscaled by 1/scale back to native resolution (still larger than the base frame,
since the margin is kept, in case the artist drew outside it); ox/oy (native px, the base frame's
offset from the cut PNG's top-left, from the margin) are written to <skin>_offsets.json alongside
the PNGs for every frame where they are non-zero -- this is normal for every F4a frame, not a sign
of anything unusual.
Empty cells -> WARNING (missing frame, the game renders that frame without the skin).
Pixels drawn outside every cell -> WARNING (they would be lost)."""
import json,sys,os
from PIL import Image
cfg=json.load(open(sys.argv[1]));sheet=Image.open(sys.argv[2]).convert('RGBA');out=sys.argv[3]
os.makedirs(out,exist_ok=True)
if sheet.size!=(cfg['sheet']['w'],cfg['sheet']['h']):sys.exit(f"ERROR sheet is {sheet.size}, template is {cfg['sheet']['w']}x{cfg['sheet']['h']} - do not resize the template")
scale=cfg.get('scale') or 1
a=sheet.getchannel('A');missing=[];mask=Image.new('L',sheet.size,0);offsets={}
for k,c in cfg['frames'].items():
    box=(c['x'],c['y'],c['x']+c['w'],c['y']+c['h']);mask.paste(255,box)
    im=sheet.crop(box)
    if im.getchannel('A').getextrema()[1]==0:missing.append(k);continue
    if scale!=1:
        base=c.get('base')
        if base:
            ox,oy=(base['x']-c['x'])/scale,(base['y']-c['y'])/scale
            if ox or oy:offsets[k]={"ox":round(ox,2),"oy":round(oy,2)}
        im=im.resize((round(c['w']/scale),round(c['h']/scale)),Image.LANCZOS)
    im.save(f"{out}/sk_{cfg['skin']}_{k}.png")
if offsets:json.dump(offsets,open(f"{out}/{cfg['skin']}_offsets.json",'w'),indent=1)
from PIL import ImageChops
outside=sum(1 for v in ImageChops.subtract(a,mask).tobytes() if v)
print(f"{cfg['skin']} ({cfg['mode']}): {len(cfg['frames'])-len(missing)}/{len(cfg['frames'])} frames cut"+(f", downscaled 1/{scale}" if scale!=1 else ""))
if offsets:print(f"{len(offsets)} frame(s) have an ox/oy offset -> {cfg['skin']}_offsets.json")
if missing:print("WARNING missing frames:",", ".join(missing))
if outside:print(f"WARNING {outside} drawn pixels are outside the cells and were ignored")
