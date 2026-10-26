"""Download/verify all four subsets against the frozen pinned-mirror manifest."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def download(destination:Path, subsets:list[str]):
 manifest=json.loads((ROOT/'docs/data/cmapss-manifest.json').read_text())
 destination.mkdir(parents=True,exist_ok=True)
 for name,record in manifest['files'].items():
  if not any(s in name for s in subsets):continue
  path=destination/name
  content=path.read_bytes() if path.exists() else urllib.request.urlopen(f'https://raw.githubusercontent.com/PunVas/nasa-c-mapss/{manifest["commit"]}/{name}',timeout=60).read()
  if hashlib.sha256(content).hexdigest()!=record['sha256']:raise RuntimeError(f'SHA-256 mismatch: {name}; existing files are never silently replaced')
  if hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()!=record['git_blob_sha1']:raise RuntimeError(f'Git blob mismatch: {name}')
  if not path.exists():
   temporary=path.with_suffix('.verified.tmp');temporary.write_bytes(content);temporary.replace(path)
  print('Verified',name,record['sha256'])
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path,default=ROOT/'data/raw/CMAPSSData');p.add_argument('--subset',action='append',choices=['FD001','FD002','FD003','FD004']);a=p.parse_args();download(a.destination,a.subset or ['FD001','FD002','FD003','FD004'])
