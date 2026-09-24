import numpy as np,sys
from PIL import Image
def edges(a,axis):
    d=(np.abs(np.diff(a,axis=axis)).sum(2)>60)
    return np.nonzero(d.sum(axis=1-axis if axis==1 else 1))[0] if False else d
def fit(pos,weights,lo,hi):
    best=(0,0,0)
    for b in np.arange(lo,hi,0.05):
        ph=(pos%b)
        # histogram of phases
        nb=int(np.ceil(b*4))
        h,_=np.histogram(ph,bins=nb,range=(0,b),weights=weights)
        # circular window of +-1px
        w=4*1; hh=np.concatenate([h,h[:2*w]])
        s=np.convolve(hh,np.ones(2*w+1),'valid')[:nb]
        i=s.argmax(); sc=s[i]/weights.sum()
        # penalise small b (always fits) by expected random fraction
        sc-= (2*1+1)/b
        if sc>best[0]: best=(sc,b,(i+0.5)/4)
    return best
def est(f,lo=8,hi=32):
    a=np.asarray(Image.open(f).convert('RGB')).astype(int)
    dx=(np.abs(np.diff(a,axis=1)).sum(2)>60).sum(0).astype(float)
    dy=(np.abs(np.diff(a,axis=0)).sum(2)>60).sum(1).astype(float)
    px=np.arange(len(dx))+1; py=np.arange(len(dy))+1
    return fit(px[dx>0],dx[dx>0],lo,hi),fit(py[dy>0],dy[dy>0],lo,hi)
for f in sys.argv[1:]:
    (sx,bx,ox),(sy,by,oy)=est(f)
    print(f'{f}: bx={bx:.2f} ox={ox:.1f} sc={sx:.2f} | by={by:.2f} oy={oy:.1f} sc={sy:.2f}')
