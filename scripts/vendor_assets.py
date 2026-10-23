from pathlib import Path
import concurrent.futures, io, re, subprocess, tarfile
# Run with: python -m pip install fonttools brotli; python scripts/vendor_assets.py
root=Path(__file__).resolve().parents[1]/'docs/assets/vendor'
root.mkdir(parents=True,exist_ok=True)
def download(url):
 r=subprocess.run(['curl','-fL','--retry','2','--max-time','60','-sS',url],capture_output=True,check=True)
 return r.stdout
packages=[('katex','https://registry.npmjs.org/katex/-/katex-0.19.0.tgz'),('lxgw','https://registry.npmjs.org/lxgw-wenkai-screen-webfont/-/lxgw-wenkai-screen-webfont-1.1.0.tgz')]
def vendor(item):
 name,url=item;data=download(url)
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
  for m in tar.getmembers():
   if not m.isfile():continue
   rel=m.name.removeprefix('package/')
   target=None
   if name=='katex':
    if rel in ('dist/katex.min.js','dist/katex.min.css','dist/contrib/auto-render.min.js'):target=root/'katex'/Path(rel).name
    elif rel.startswith('dist/fonts/'):target=root/'katex'/'fonts'/Path(rel).name
    elif rel=='LICENSE':target=root/'katex/LICENSE'
   elif rel=='lxgwwenkaiscreen.css':target=root/'fonts/lxgw.css'
   elif rel.startswith('files/lxgwwenkaiscreen-subset-') and rel.endswith('.woff2'):target=root/'fonts/files'/Path(rel).name
   elif 'license' in rel.lower() or 'ofl' in rel.lower():target=root/'fonts'/('LXGW-'+Path(rel).name)
   if target:
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(m).read())
 return name,len(data)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 for result in ex.map(vendor,packages):print(result,flush=True)
# Existing font endpoints provide full fonts; subset the decorative title face
# to this site's text. Body text remains covered by the complete LXGW subsets.
from fontTools import subset
chars=''.join(p.read_text(errors='ignore') for p in (root.parents[1]).rglob('*.md'))+''.join(chr(i) for i in range(32,127))+'“”‘’…↗✦'
css=download('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&display=swap').decode()
urls=list(dict.fromkeys(re.findall(r'url\((https[^)]+)\)',css)))
for i,url in enumerate(urls):
 original=Path('/tmp')/f'xmin-noto-{i}.ttf';original.write_bytes(download(url))
 font=subset.load_font(str(original),subset.Options())
 opt=subset.Options();opt.flavor='woff2'
 sub=subset.Subsetter(options=opt);sub.populate(text=chars);sub.subset(font)
 subset.save_font(font,str(root/'fonts'/f'noto-serif-sc-{400 if i==0 else 700}.woff2'),opt)
 print('noto',i,flush=True)
# JetBrains' official package supplies small latin WOFF2 faces.
data=download('https://registry.npmjs.org/@fontsource/jetbrains-mono/-/jetbrains-mono-5.2.8.tgz')
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
 for m in tar.getmembers():
  rel=m.name.removeprefix('package/')
  if rel in ('files/jetbrains-mono-latin-400-normal.woff2','files/jetbrains-mono-latin-700-normal.woff2'):
   (root/'fonts'/Path(rel).name).write_bytes(tar.extractfile(m).read())
  elif rel=='LICENSE':(root/'fonts/JetBrains-LICENSE').write_bytes(tar.extractfile(m).read())
# Noto Serif is distributed under the SIL Open Font License.
(root/'fonts/Noto-OFL.txt').write_bytes(download('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Serif/LICENSE'))
(root/'fonts/fonts.css').write_text((root/'fonts/lxgw.css').read_text()+'''\n@font-face{font-family:"Noto Serif SC";font-style:normal;font-weight:400;font-display:swap;src:url("noto-serif-sc-400.woff2") format("woff2")}\n@font-face{font-family:"Noto Serif SC";font-style:normal;font-weight:700;font-display:swap;src:url("noto-serif-sc-700.woff2") format("woff2")}\n@font-face{font-family:"JetBrains Mono";font-style:normal;font-weight:400;font-display:swap;src:url("jetbrains-mono-latin-400-normal.woff2") format("woff2")}\n@font-face{font-family:"JetBrains Mono";font-style:normal;font-weight:700;font-display:swap;src:url("jetbrains-mono-latin-700-normal.woff2") format("woff2")}\n''')
(root/'fonts/lxgw.css').unlink()
print('vendor bytes',sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),flush=True)
