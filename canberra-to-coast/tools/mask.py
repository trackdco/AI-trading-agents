from PIL import Image, ImageFilter
import numpy as np

SRC='/tmp/claude-0/-home-user-AI-trading-agents/c93c1dc3-9da6-5a2e-865c-5bd96a2ad7df/images/11.webp'
OUT='/tmp/claude-0/-home-user-AI-trading-agents/c93c1dc3-9da6-5a2e-865c-5bd96a2ad7df/scratchpad/c2c/site/fence/'

im=Image.open(SRC).convert('RGB')
W,H=im.size
a=np.asarray(im).astype(np.float32)

# the fence + gate outline, traced off the grid overlay (fractions of width/height)
POLY=[(0,.250),(.10,.268),(.20,.283),(.292,.296),(.300,.356),(.42,.360),(.55,.358),(.65,.356),(.75,.354),(.808,.352),
      (.812,.630),(.75,.638),(.70,.643),(.60,.652),(.50,.660),(.42,.670),(.335,.698),(.300,.714),
      (.245,.725),(.20,.737),(.12,.790),(.05,.838),(0,.874)]
from PIL import ImageDraw
poly=Image.new('L',(W,H),0)
ImageDraw.Draw(poly).polygon([(x*W,y*H) for x,y in POLY],fill=255)
region=np.asarray(poly).astype(np.float32)/255.0

r,g,b=a[...,0],a[...,1],a[...,2]
mx=a.max(axis=2); mn=a.min(axis=2)
sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1),0)
lum=0.2126*r+0.7152*g+0.0722*b

# inside the outline, keep the steel: warm, not green, not near-black
warm   = (r>=g-4)&(g>=b-6)                 # cream/tan: red >= green >= blue
notgreen = ~((g>r+6)&(g>b+10))             # vine leaves
notsky = ~((b>r+18)&(b>100))               # any sky showing through
bright = lum>52                            # deep shadow gaps, the latch, dirt
lowsat = sat<0.52                          # saturated foliage / red signage
keep=(warm&notgreen&notsky&bright&lowsat).astype(np.float32)*region

m=Image.fromarray((keep*255).astype(np.uint8))
m=m.filter(ImageFilter.MedianFilter(5))            # drop speckle
m=m.filter(ImageFilter.GaussianBlur(1.2))          # soft edge so recolouring does not alias
mask=np.asarray(m).astype(np.float32)/255.0
np.save(OUT+'mask.npy',mask)
Image.fromarray((mask*255).astype(np.uint8)).save(OUT+'mask.png')

# preview: paint the mask green over the photo so I can see what got caught
prev=a.copy(); prev[...,1]=np.clip(prev[...,1]+mask*110,0,255); prev[...,0]=np.clip(prev[...,0]-mask*40,0,255)
Image.fromarray(prev.astype(np.uint8)).save(OUT+'mask-preview.jpg',quality=85)
sel=mask>0.5
print('masked pixels: %.1f%% of image'%(100*sel.mean()))
print('fence luminance: min %.0f  p5 %.0f  mean %.0f  p95 %.0f  max %.0f'%(lum[sel].min(),np.percentile(lum[sel],5),lum[sel].mean(),np.percentile(lum[sel],95),lum[sel].max()))
