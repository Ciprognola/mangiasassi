exec(open('pipe.py').read())
allf=[];names=[]
for f,h1,keys in [('Algidone_idle___throw.png',1376,['fa_alg_idle0','fa_alg_idle1','fa_alg_throw0','fa_alg_throw1','fa_alg_throw2','fa_alg_throw3']),
                  ('Eating___Hungry.png',2032,['fa_alg_eat0','fa_alg_eat1','fa_alg_eat2','fa_alg_angry0','fa_alg_angry1']),
                  ('Algidone_kicked_out.png',2012,['fa_alg_kick0','fa_alg_kick1','fa_alg_kick2'])]:
    a,m,bg=load(f); b=h1/128
    rgb,al=snap(a,m,b); img=quant(to_img(rgb,al),64)
    lab,main,small=comps(al)
    fr,dr=frames_from(img,lab,main,small)
    print(f,'b',round(b,2),'frames',len(fr),[x.shape[:2] for x in fr],'dropped',[(d['x0'],d['y0'],d['area']) for d in dr])
    assert len(fr)==len(keys)
    allf+=fr;names+=[(k,f) for k in keys]
padded=pad(allf,'bottom')
for (k,f),p in zip(names,padded): save(k,p,f,'bottom-center')
import json;json.dump(META,open('/home/claude/fa/meta_alg.json','w'))
# preview
W=sum(p.shape[1] for p in padded)+4*len(padded); H=padded[0].shape[0]
pv=Image.new('RGBA',(W,H),(60,60,70,255));x=0
for p in padded: pv.alpha_composite(Image.fromarray(p),(x,0)); x+=p.shape[1]+4
pv.resize((W*2,H*2),Image.NEAREST).save('/home/claude/fa/pv_alg.png')
