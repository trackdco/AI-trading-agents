from PIL import Image
import numpy as np, os

SRC='/tmp/claude-0/-home-user-AI-trading-agents/c93c1dc3-9da6-5a2e-865c-5bd96a2ad7df/images/11.webp'
HERE=os.path.dirname(os.path.abspath(__file__))+'/'
im=Image.open(SRC).convert('RGB'); a=np.asarray(im).astype(np.float32)
mask=np.load(HERE+'mask.npy'); sel=mask>0.35
lum=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
meanL=float(np.median(lum[sel]))
hi=float(np.percentile(lum[sel],97))
spec=np.clip((lum-hi)/max(255-hi,1),0,1)**1.3          # blown highlights / lens flare stay white

def recolour(hexcol):
    t=np.array([int(hexcol[i:i+2],16) for i in (1,3,5)],dtype=np.float32)
    Lt=float(0.2126*t[0]+0.7152*t[1]+0.0722*t[2])
    tone=t/max(Lt,1.0)                                  # the colour's hue and chroma, lightness removed
    contrast=0.55+0.45*(Lt/255.0)                       # dark steel varies less in absolute terms
    Lnew=np.clip(Lt+(lum-meanL)*contrast,2,255)
    out=Lnew[...,None]*tone[None,None,:]
    out=out+(255-out)*(spec[...,None]*0.8)
    m=mask[...,None]
    return np.clip(a*(1-m)+np.clip(out,0,255)*m,0,255).astype(np.uint8)

if __name__=='__main__':
    tests=[('monument','#323233'),('surfmist','#E4E2D5'),('nightsky','#0B0B0C'),('paleeucalypt','#7C846A'),
           ('deepocean','#364152'),('classiccream','#E9DCB8')]
    ims=[]
    for name,hx in tests:
        img=Image.fromarray(recolour(hx)).resize((680,510),Image.LANCZOS); ims.append(img)
    w,h=ims[0].size; sheet=Image.new('RGB',(w*3,h*2))
    for i,img in enumerate(ims): sheet.paste(img,((i%3)*w,(i//3)*h))
    sheet.save(HERE+'test-sheet.jpg',quality=88)
    print('median fence luminance',round(meanL),' p97',round(hi))
