"""Lightweight fleet entry point; full real outputs load only for analysis views."""
import json
from pathlib import Path

def write_catalog(path:Path):
 data=json.loads(path.read_text());catalog={k:v for k,v in data.items() if k not in ['engines','testResiduals']};catalog['summary']=True
 catalog['engines']=[{**{k:v for k,v in e.items() if k!='points'},'points':[],'snapshot':{k:v for k,v in e['points'][e['current']-1].items() if k!='whatIf'}} for e in data['engines']]
 destination=path.with_name(path.name.replace('demo','catalog',1));destination.write_text(json.dumps(catalog,separators=(',',':'),allow_nan=False))
if __name__=='__main__':
 for path in (Path(__file__).resolve().parents[1]/'public').glob('demo*.json'):write_catalog(path)
