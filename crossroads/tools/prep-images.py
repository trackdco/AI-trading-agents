# How the photos in assets/img were made from the originals on the old site.
# Not needed to build or deploy: the converted webp files are committed.
# Expects the downloaded originals in photos/, more/, big/, posters/ next to it.
from PIL import Image, ImageOps, ImageDraw
import os, glob
OUT=__import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'assets', 'img') + '/'
idx={l.split()[1].split('_')[0]:'photos/'+l.split()[1] for l in open('photo-index.txt')}
def src(id):
    g=glob.glob(f'big/{id}_*')
    if g: return g[0]
    if id in idx: return idx[id]
    g=glob.glob(f'more/{id}_*'); return g[0]
def load(p):
    im=Image.open(p); im=ImageOps.exif_transpose(im)
    if im.mode in ('RGBA','LA','P'):
        im=im.convert('RGBA'); bg=Image.new('RGBA',im.size,(27,26,23,255)); bg.alpha_composite(im); im=bg
    return im.convert('RGB')
def save(im,name,widths,q=80,ratio=None,anchor=0.5):
    if ratio:
        w,h=im.size; tr=ratio
        if w/h>tr: nw=int(h*tr); x0=int((w-nw)*0.5); im=im.crop((x0,0,x0+nw,h))
        else: nh=int(w/tr); y0=int((h-nh)*anchor); im=im.crop((0,y0,w,y0+nh))
    for W in widths:
        if W>=im.size[0] and W!=widths[0]: continue
        r=im.copy(); r.thumbnail((W,100000),Image.LANCZOS)
        f=f'{OUT}{name}-{W}.webp' if len(widths)>1 else f'{OUT}{name}.webp'
        r.save(f,'WEBP',quality=q,method=6)
        print(f.split('img/')[1], r.size, os.path.getsize(f)//1024,'KB')
# hero
save(load(src('13373919')),'hero-canberra',[2400,1600,1000],q=78)
# services
save(load(src('17650752')),'north',[1600,900],ratio=3/2)
save(load(src('17650517')),'belconnen',[1600,900],ratio=3/2)
save(load(src('24179989')),'city',[1600,900],ratio=3/2)
save(load(src('8560585')),'lake-g',[1600,900],ratio=3/2)
save(load(src('16509567')),'sunday-wide',[2000,1200],q=78)
save(load(src('17650782')),'north-2',[1200],ratio=3/2)
save(load(src('17650592')),'belconnen-2',[1200],ratio=3/2)
save(load(src('24180024')),'city-2',[1200],ratio=3/2)
save(load(src('17650842')),'city-group',[1200],ratio=3/2)
save(load(src('4406187')),'hall',[1600,900])
save(load(src('4396841')),'worship',[1600,900])
# kids/youth
save(load(src('4060792')),'kids',[1600,900],ratio=3/2)
save(load(src('4813005')),'kids-2',[1600,900],ratio=3/2)
save(load(src('4035907')),'youth-sunset',[1600,900],ratio=16/9)
save(load(src('17650842')),'youth-group',[1200],ratio=3/2)
save(load(src('4186541')),'youth-outdoor',[1200],ratio=3/2)
# connect
save(load(src('4186381')),'serving-food',[1600,900],ratio=3/2)
save(load(src('4335426')),'conversation',[1200],ratio=3/2)
save(load(src('22949726')),'connect-lunch',[1600,900])
save(load(src('7009674')),'lunch-outdoor',[1200],ratio=3/2)
save(load(src('4186466')),'notebooks',[1200],ratio=3/2)
save(load(src('4186601')),'seedlings',[900],ratio=1)
save(load(src('4336091')),'growth-group',[1600,900],ratio=3/2)
save(load(src('4335604')),'jol-room',[1600,900],ratio=16/9)
save(load(src('4728355')),'jol-stage',[1600,900],ratio=3/2)
save(load(src('4335819')),'two-women',[1200],ratio=3/2)
save(load(src('586043')),'english',[1200],ratio=3/2)
# teaching
save(load(src('4336026')),'preach-1',[1600,900],ratio=16/9)
save(load(src('4814175')),'preach-2',[1600,900],ratio=3/2)
save(load(src('4337335')),'bible-open',[1600,900],ratio=3/2)
save(load(src('4336401')),'bible-desk',[1200],ratio=3/2)
save(load(src('4186486')),'books',[1200],ratio=3/2)
save(load(src('18928122')),'word-to-life',[1200],ratio=3/2)
save(load(src('16509577')),'interview',[1600,900],ratio=3/2)
save(load(src('4912796')),'stage-two',[1600,900],ratio=3/2)
save(load(src('6191063')),'stage-chat',[1200],ratio=3/2)
save(load(src('4109264')),'listening',[1200],ratio=3/2)
# about
save(load(src('4396776')),'25-years',[1600,900],ratio=3/2)
save(load(src('4396786')),'1996',[1600,900])
save(load(src('25693677')),'moore-news',[1600])
save(load(src('13672469')),'globe',[1200],ratio=1)
save(load(src('2647129')),'giving',[1600,900],ratio=3/2)
save(load(src('2708051')),'canberra-bw',[2000,1200],ratio=16/9)
save(load(src('11824958')),'prayer',[1200],ratio=3/2)
save(load(src('5092520')),'story-woman',[1200],ratio=3/2)
save(load(src('4150107')),'story-crowd',[1200],ratio=3/2)
save(load(src('14441873')),'ministry-centre',[1600,900],ratio=3/2)
save(load(src('19380169')),'ministry-centre-2',[900],ratio=3/2)
save(load(src('18517727')),'parking-map',[1600,1000],q=85)
save(load(src('4472011')),'welcome-hall',[900],ratio=3/2)
# staff 4:5
for id,n in [('22931427','marcus-reeves'),('4800435','kerryn-rudder'),('23545164','owen-chadwick'),('17341836','simon-nixey'),('23545159','revin-blanchard'),('23545189','sarah-rootes'),('23545184','andy-copeman'),('21376679','annabel-nixey'),('23545174','cassandra-buttsworth')]:
    save(load(src(id)),'staff/'+n,[640],q=82,ratio=4/5,anchor=0.35)
for id,n in [('21429670','amy-wiles'),('17312079','emily-gates'),('17312094','aisha-dunkley'),('12991616','willis-lo'),('12991761','alice-gerty'),('8342767','wira-wibowo'),('8342712','caleb-dallos'),('8342687','andy-rowlands'),('8342737','davey-lovell'),('4449188','jennifer-tait'),('4424338','ming-en-chin'),('9592876','caitlin-roberts'),('8342667','lizzy-hammond')]:
    save(load(src(id)),'mts/'+n,[640],q=82,ratio=4/5,anchor=0.3)
save(load(src('21429696')),'mts/trainees-2026',[1200])
for id,n in [('13672530','phil-lil-west-asia'),('13672557','wilsons-italy'),('13672587','dave-jenny-west-africa'),('13672597','grocotts-romania'),('13672714','hickels-germany'),('13672719','kelly-nicholas-japan'),('13672749','jemma-phen-sydney'),('13672794','m-1'),('13672799','m-2')]:
    save(load(src(id)),'partners/'+n,[800],q=82)
# posters
for f in glob.glob('posters/*.jpg'):
    save(load(f),'posters/'+os.path.basename(f)[:-4],[960],q=76)
# FIEC logo, keep alpha as png
im=Image.open(src('5777149')).convert('RGBA'); im.thumbnail((600,600)); im.save(OUT+'fiec.png',optimize=True)
# logos from the white stacked lockup 19549674
lg=Image.open('more/19549674_1366x427_500.png').convert('RGBA')
a=lg.getchannel('A')
for name,col in [('logo-white',(255,255,255)),('logo-ink',(27,26,23))]:
    o=Image.new('RGBA',lg.size,col+(0,)); o.putalpha(a); o.save(OUT+name+'.png',optimize=True)
    print(name,lg.size)
# X mark icon from 19391455 (yellow X on black?) -> check alpha
x=Image.open(src('19391455')); print('xmark mode',x.mode,x.size, x.getextrema() if x.mode!='P' else '')

# X mark: yellow on transparent -> app icons + favicon png
x=Image.open(src('19391455')).convert('RGBA')
bb=x.getbbox(); x=x.crop(bb)
def icon(size,pad,bg,name):
    c=Image.new('RGBA',(size,size),bg)
    m=x.copy(); m.thumbnail((size-2*pad,size-2*pad),Image.LANCZOS)
    c.alpha_composite(m,((size-m.size[0])//2,(size-m.size[1])//2))
    c.convert('RGB').save(OUT+name,optimize=True); print(name,size)
icon(512,72,(27,26,23,255),'icon-512.png'); icon(192,26,(27,26,23,255),'icon-192.png'); icon(180,26,(27,26,23,255),'apple-touch-icon.png')
m=x.copy(); m.thumbnail((640,640)); m.save(OUT+'xmark.png',optimize=True); print('xmark',m.size)
# social share image 1200x630 from hero
h=load(src('13373919')); w,hh=h.size; tr=1200/630; nh=int(w/tr); h=h.crop((0,(hh-nh)//2,w,(hh-nh)//2+nh)); h.thumbnail((1200,630)); h.save(OUT+'share.jpg',quality=80); print('share',h.size)
