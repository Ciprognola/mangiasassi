import numpy as np, json, os
from PIL import Image
from scipy import ndimage as nd
U='/mnt/user-data/uploads/'
OUT='/home/claude/fa/out/refs/ferma_algidone'
os.makedirs(OUT+'/frames',exist_ok=True)
def load(f):
    a=np.asarray(Image.open(U+f).convert('RGB')).astype(np.float32)
    c=np.concatenate([a[:20,:20].reshape(-1,3),a[:20,-20:].reshape(-1,3),a[-20:,:20].reshape(-1,3),a[-20:,-20:].reshape(-1,3)])
    bg=np.median(c,0); m=np.sqrt(((a-bg)**2).sum(2))>110
    return a,m,bg
def snap(a,m,b,ox=0.0,oy=0.0):
    H,W,_=a.shape
    nx=int((W-ox)//b); ny=int((H-oy)//b)
    offs=[0.3,0.5,0.7]
    xs=[(ox+(np.arange(nx)+o)*b).astype(int) for o in offs]
    ys=[(oy+(np.arange(ny)+o)*b).astype(int) for o in offs]
    cols=[];ms=[]
    for yy in ys:
        for xx in xs:
            cols.append(a[np.ix_(yy,xx)]); ms.append(m[np.ix_(yy,xx)])
    cols=np.stack(cols); ms=np.stack(ms).astype(np.float32)
    alpha=ms.mean(0)>0.5
    # median over opaque samples: set bg samples to nan
    cc=cols.copy(); cc[ms==0]=np.nan
    rgb=np.nanmedian(cc,axis=0)
    rgb=np.nan_to_num(rgb)
    return rgb,alpha
def to_img(rgb,alpha):
    out=np.zeros(rgb.shape[:2]+(4,),np.uint8)
    out[...,:3]=np.clip(rgb,0,255).astype(np.uint8); out[...,3]=alpha*255
    return out
def quant(img,n=64):
    im=Image.fromarray(img,'RGBA'); a=np.asarray(im)[...,3]
    q=im.convert('RGB').quantize(n,method=Image.Quantize.MEDIANCUT).convert('RGB')
    o=np.dstack([np.asarray(q),a]); o[a==0]=0
    return o
def comps(alpha,minfrac=0.15):
    lab,n=nd.label(nd.binary_dilation(alpha,iterations=1))
    lab=lab*alpha
    objs=nd.find_objects(lab); res=[]
    for i,sl in enumerate(objs):
        if sl is None: continue
        area=int((lab[sl]==i+1).sum())
        if area<3: continue
        res.append(dict(id=i+1,x0=sl[1].start,x1=sl[1].stop,y0=sl[0].start,y1=sl[0].stop,area=area))
    mx=max(c['area'] for c in res)
    main=[c for c in res if c['area']>=minfrac*mx]; small=[c for c in res if c['area']<minfrac*mx]
    return lab,main,small
def frames_from(img,lab,main,small,order='x',drop_outside=True):
    if order=='x': main.sort(key=lambda c:c['x0'])
    else: main.sort(key=lambda c:(round(c['y0']/max(1,(c['y1']-c['y0'])*0.8)),c['x0']))
    groups=[[c] for c in main]
    dropped=[]
    for s in small:
        cx=(s['x0']+s['x1'])/2
        hit=[g for g in groups if g[0]['x0']<=cx<=g[0]['x1'] and not (s['y0']>g[0]['y1']+10 or s['y1']<g[0]['y0']-200)]
        if hit: hit[0].append(s)
        else: dropped.append(s)
    fr=[]
    for g in groups:
        ids=[c['id'] for c in g]
        x0=min(c['x0'] for c in g);x1=max(c['x1'] for c in g);y0=min(c['y0'] for c in g);y1=max(c['y1'] for c in g)
        sub=img[y0:y1,x0:x1].copy(); keep=np.isin(lab[y0:y1,x0:x1],ids); sub[~keep]=0
        fr.append(sub)
    return fr,dropped
def pad(frames,anchor='bottom'):
    W=max(f.shape[1] for f in frames); H=max(f.shape[0] for f in frames); res=[]
    for f in frames:
        o=np.zeros((H,W,4),np.uint8); h,w=f.shape[:2]; x=(W-w)//2
        y=H-h if anchor=='bottom' else (H-h)//2
        o[y:y+h,x:x+w]=f; res.append(o)
    return res
META={}
def save(key,arr,src,anchor,note=''):
    Image.fromarray(arr,'RGBA').save(f'{OUT}/frames/{key}.png',optimize=True)
    META[key]=dict(file=f'frames/{key}.png',w=arr.shape[1],h=arr.shape[0],anchor=anchor,source=src,note=note)
