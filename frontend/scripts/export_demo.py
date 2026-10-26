"""Export portable trajectories. Default predictions are explicitly illustrative.
Run from repo root using .venv/bin/python frontend/scripts/export_demo.py.
Optional --bundle MODEL=RUN_DIR (repeat) uses the unchanged FastAPI pipeline.
"""
from pathlib import Path
import argparse, json, math, sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from rul_pm.data.io import read_cmapss_table, COLUMNS

ROOT = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--bundle', action='append', default=[], help='MODEL=RUN_DIR; must match metadata.json')
p.add_argument('--subset', default='FD004', choices=['FD001','FD004'])
p.add_argument('--output', type=Path, default=ROOT/'frontend/public/demo.json')
a = p.parse_args()
models=['xgboost','lstm','gru','transformer']
bundles={}
for spec in a.bundle:
 name,path=spec.split('=',1)
 if name not in models: p.error('Unknown model '+name)
 path=Path(path).resolve()
 if json.loads((path/'metadata.json').read_text())['model'] != name: p.error('Artifact model mismatch')
 bundles[name]=path
path=ROOT/'data/raw/CMAPSSData'/f'train_{a.subset}.txt'
frame=read_cmapss_table(path) if path.exists() else None
if bundles and frame is None: p.error('Real data is required to export trained predictions')
clients={}
if bundles:
 import os
 from fastapi.testclient import TestClient
 from rul_pm.api.app import create_app
 for name,path in bundles.items():
  os.environ['RULPM_ARTIFACT_DIR']=str(path)
  clients[name]=TestClient(create_app())
sensors=[2,3,4,7,9,11,12,14,15,20,21]
engines=[]
for i in range(1,13):
 if frame is not None:
  f=frame[frame.unit_number==i]; raw=f.to_dict(orient='records')
 else:
  raw=[dict(zip(COLUMNS,[i,c,0,0,100,*[round(s+0.008*c*s+math.sin(c/13+s)*.03,5) for s in range(1,22)]])) for c in range(1,211+i*4)]
 end=len(raw); points=[]
 for idx,row in enumerate(raw):
  cycle=int(row['time_in_cycles']); actual=min(125,end-cycle)
  predictions={}
  for j,name in enumerate(models):
   if name in clients:
    response=clients[name].post('/predict',json={'rows':raw[max(0,idx-29):idx+1]}); response.raise_for_status()
    predictions[name]=round(response.json()['predictions'][0]['predicted_rul'],3)
   elif not bundles: predictions[name]=round(max(0,min(125,actual+math.sin(cycle/19+i+j)* (5+j*2)+j*1.5)),2)
  points.append({'cycle':cycle,'actual':actual,**predictions,'sensors':{str(s):row[f'sensor_{s}'] for s in sensors},'row':row})
 engines.append({'id':i,'name':f'ENG-{i:03d}','cycles':end,'current':max(1,end-(15+i*17)%145),'points':points})
correlation=[]
if frame is not None:
 corr=frame[[f'sensor_{s}' for s in sensors]].corr().fillna(0)
 correlation=[[round(float(v),2) for v in row] for row in corr.to_numpy()]
metrics={s:json.loads((ROOT/f'results/{s}/model_comparison.json').read_text())['comparison'] for s in ['FD001','FD004']}
result={'schemaVersion':1,'subset':a.subset,'predictionSource':'trained artifacts' if bundles else 'illustrative simulation — not trained predictions','trajectorySource':f'C-MAPSS {a.subset} run-to-failure training trajectories' if frame is not None else 'synthetic trajectories — raw dataset unavailable','models':list(bundles) if bundles else models,'sensors':sensors,'engines':engines,'correlation':correlation,'metrics':metrics}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,separators=(',',':'),allow_nan=False))
print(f'Exported {len(engines)} engines to {a.output}; {result["predictionSource"]}')
