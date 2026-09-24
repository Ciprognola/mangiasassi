exec(open('pipe.py').read())
import json
def sheet(f,b,ox,oy,minfrac=0.15,order='x'):
    a,m,bg=load(f); rgb,al=snap(a,m,b,ox,oy); img=quant(to_img(rgb,al),48)
    lab,main,small=comps(al,minfrac); fr,dr=frames_from(img,lab,main,small,order)
    print(f,len(fr),[x.shape[:2] for x in fr],'dropped',[(d['x0'],d['y0'],d['area']) for d in dr])
    return fr,img
# flame+grill
fr,_=sheet('Flame___Grill.png',22.95,19.9,6.1)
fl=pad(fr[:4]);gr=pad(fr[4:6])
for i,p in enumerate(fl): save(f'fa_fiamma{i}',p,'Flame___Grill.png','bottom-center')
save('fa_griglia0',gr[0],'Flame___Grill.png','bottom-center','braci spente')
save('fa_griglia1',gr[1],'Flame___Grill.png','bottom-center','braci accese')
# meat
fr,_=sheet('Meat_Items.png',22.95,20.1,9.6,minfrac=0.1)
for x in fr: pass
sal=np.asarray(Image.fromarray(fr[0]).transpose(Image.ROTATE_270))
save('fa_salsiccia',sal,'Meat_Items.png','center','ruotata di 90° in orizzontale; la rotazione mentre rotola si fa in codice')
save('fa_porchetta0',fr[2],'Meat_Items.png','center','rotolo intero (principale)')
save('fa_porchetta1',fr[1],'Meat_Items.png','center','variante con fetta tagliata davanti — alternativa, non un vero frame di "schiacciamento"')
c=pad([fr[3],fr[4]])
save('fa_carne0',c[0],'Meat_Items.png','bottom-center','normale'); save('fa_carne1',c[1],'Meat_Items.png','bottom-center','schiacciata (atterraggio)')
# stock
fr,_=sheet('Stock_pile.png',22.95,20.4,9.1,order='row')
top=pad(fr[:4]); bot=pad(fr[4:])
for i,p in enumerate(top): save(f'fa_scorte{i}',p,'Stock_pile.png','bottom-center',['piena','2/3','1/3','vuota'][i])
for i,p in enumerate(bot): save(f'fa_scorte_b{i}',p,'Stock_pile.png','bottom-center','variante alternativa (riga inferiore del foglio)')
# buildings
def whole(f,b,ox,oy,key,note=''):
    a,m,bg=load(f); rgb,al=snap(a,m,b,ox,oy); img=quant(to_img(rgb,al),96)
    ys,xs=np.nonzero(al); img=img[ys.min():ys.max()+1,xs.min():xs.max()+1]
    save(key,img,f,'bottom-center',note); print(key,img.shape)
whole('Coccia_Building.png',15,14.4,6.1,'fa_bld_coccia')
whole('Macelleria.png',22.95,20.4,9.1,'fa_bld_macelleria','furgone incluso; bordo superiore dell edificio tagliato dal foglio originale')
whole('Fabbrica_di_salsiccie.png',15,14.4,6.1,'fa_bld_fabbrica')
# backdrops
def bgd(f,key,crop=None,note=''):
    im=Image.open(U+f).convert('RGB')
    if crop: im=im.crop(crop)
    im=im.resize((360,640),Image.BOX)
    im=im.quantize(128,method=Image.Quantize.MEDIANCUT).convert('RGB')
    arr=np.dstack([np.asarray(im),np.full((640,360),255,np.uint8)])
    save(key,arr,f,'fill',note)
bgd('Coccia_Backdrop.png','fa_bg_coccia')
bgd('Fabbrica_backdrop.png','fa_bg_fabbrica')
# macelleria landscape -> provisional 9:16 crop around door + carcasses
W,H=5504,3072; cw=int(H*9/16); x0=700
bgd('Macelleria_Backdrop.png','fa_bg_macelleria',(x0,0,x0+cw,H),'PROVVISORIO: il foglio originale era orizzontale 16:9; ritaglio verticale da rigenerare in 9:16')
json.dump(META,open('meta_items.json','w'))
