from _shared import *
import zipfile
from swa_appworld.bundle import validate_ready

comp=ROOT/'LOCAL_ONLY_OUTPUT/compiled'
validate_ready(comp,ROOT)
out=ROOT/'LOCAL_ONLY_OUTPUT/appworld_swa_formal_ready.zip'
staging=out.with_suffix('.zip.tmp')
with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(comp.rglob('*')):
        if p.is_file():
            relative=p.relative_to(comp)
            if relative.parts[0]=='sealed':
                name=Path('SEALED').joinpath(*relative.parts[1:])
            else:
                name=relative
            z.write(p,name)
    hashes=json.loads((comp/'source_hashes.json').read_text())
    for name in sorted(hashes):
        z.write(ROOT/name,Path('SOURCE')/name)
with zipfile.ZipFile(staging) as z:
    if z.testzip() is not None: raise ValueError('Corrupt archive')
    if len(z.namelist())!=len(set(z.namelist())): raise ValueError('Duplicate archive entries')
staging.replace(out)
print('WROTE',out)
