"""Export real checkpoints, permutation importance and exact single-sensor what-if predictions.
Run from repository root after scripts/portfolio/train.py. No synthetic fallback.
"""
from pathlib import Path
import sys,json,argparse,hashlib,os,shutil
import numpy as np,pandas as pd,torch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from rul_pm.data.io import read_cmapss_table
from model_bundle import Bundle
ROOT=Path(__file__).resolve().parents[2]
MODELS=['xgboost','lstm','gru','transformer'];SENSORS=[2,3,4,7,9,11,12,14,15,20,21]
def export(subset,engines,output):
 raw=read_cmapss_table(ROOT/f'data/raw/CMAPSSData/train_{subset}.txt')
 paths={m:ROOT/f'artifacts/portfolio/{subset}/{m}/seed_42' for m in MODELS}
 bundles={m:Bundle(paths[m]) for m in MODELS}
 validation=bundles['xgboost'].metadata['val_units']
 assert all(b.metadata['val_units']==validation for b in bundles.values())
 units=sorted(validation)[:engines];selected=raw[raw.unit_number.isin(units)].copy()
 lengths=raw.groupby('unit_number').time_in_cycles.max().to_dict()
 actual={(int(row.unit_number),int(row.time_in_cycles)):min(125,int(lengths[row.unit_number]-row.time_in_cycles)) for row in selected.itertuples()}
 predictions={};whatif={};importance={};parity={}
 for name,bundle in bundles.items():
  print('EXPORT',subset,name,flush=True)
  pred,meta=bundle.frame(selected);predictions[name]=dict(zip(meta,pred.tolist()));whatif[name]={}
  importance[name]=bundle.importance(selected,actual,list(range(1,22)))
  for sensor in [2,4,11]:
   whatif[name][str(sensor)]={}
   for adjustment in [-10,-5,5,10]:
    changed=selected.copy();changed[f'sensor_{sensor}']*=1+adjustment/100
    values,keys=bundle.frame(changed);whatif[name][str(sensor)][str(adjustment)]=dict(zip(keys,values.tolist()))
  # Independent route-level checks: batch path must match actual serving at padded/full windows.
  from fastapi.testclient import TestClient
  from rul_pm.api.app import create_app
  os.environ['RULPM_ARTIFACT_DIR']=str(paths[name]);client=TestClient(create_app());first=selected[selected.unit_number==units[0]]
  errors=[]
  for cycle in [1,29,30,len(first)]:
   rows=first.iloc[max(0,cycle-30):cycle].to_dict(orient='records');response=client.post('/predict',json={'rows':rows});response.raise_for_status()
   result=response.json()['predictions'][0]['predicted_rul'];expected=predictions[name][(units[0],cycle)];errors.append(abs(result-expected));assert abs(result-expected)<.001,(subset,name,cycle,result,expected)
  # Also verify a perturbed window rather than only baseline predictions.
  cycle=min(80,len(first));rows=first.iloc[cycle-30:cycle].copy();rows['sensor_4']*=1.1
  response=client.post('/predict',json={'rows':rows.to_dict(orient='records')});response.raise_for_status()
  error=abs(response.json()['predictions'][0]['predicted_rul']-whatif[name]['4']['10'][(units[0],cycle)]);errors.append(error);assert error<.001
  parity[name]=max(errors);client.close()
 records=[]
 for unit in units:
  frame=selected[selected.unit_number==unit];points=[]
  for row in frame.to_dict(orient='records'):
   cycle=int(row['time_in_cycles']);key=(int(unit),cycle)
   points.append({'cycle':cycle,'actual':actual[key],'row':row,'sensors':{str(s):row[f'sensor_{s}'] for s in SENSORS},**{m:round(predictions[m][key],5) for m in MODELS},'whatIf':{m:{str(s):{str(v):round(whatif[m][str(s)][str(v)][key],5) for v in [-10,-5,5,10]} for s in [2,4,11]} for m in MODELS}})
  end=len(points);records.append({'id':int(unit),'name':f'ENG-{unit:03d}','cycles':end,'current':max(1,end-(15+len(records)*17)%145),'points':points})
 metrics={};sources={};test_residuals={}
 for sub in ['FD001','FD002','FD003','FD004']:
  metrics[sub]=[];test_residuals[sub]={}
  for model in MODELS:
   run=ROOT/f'artifacts/portfolio/{sub}/{model}/seed_42';r=json.loads((run/'test_metrics.json').read_text());mt=r['test_metrics'];metrics[sub].append({'model':model,'mae_mean':mt['mae'],'rmse_mean':mt['rmse'],'nasa_score_mean':mt['nasa_score'],'rmse_std':None})
   test_residuals[sub][model]=pd.read_csv(run/'test_predictions.csv').to_dict(orient='records')
  metrics[sub].sort(key=lambda r:r['rmse_mean']);sources[sub]='Reduced-budget checkpoints · seed 42 · one run/model (no variance estimate)'
 corr=raw[[f'sensor_{s}' for s in SENSORS]].corr().fillna(0).round(4).values.tolist()
 result={'schemaVersion':1,'subset':subset,'predictionSource':'real reduced-budget trained checkpoints · seed 42','trajectorySource':f'C-MAPSS {subset} held-out validation engines (not fitted; used for checkpoint selection)','models':MODELS,'sensors':SENSORS,'engines':records,'correlation':corr,'metrics':metrics,'metricSources':sources,'importance':importance,'importanceSource':'Permutation Δ MAE (cycles), one seeded permutation, up to 512 validation windows from preview engines; negative values are retained. Not causal attribution.','apiParityMaxAbsError':parity,'testResiduals':test_residuals,'checkpointPaths':{m:str(p.relative_to(ROOT)) for m,p in paths.items()},'datasetManifestSha256':hashlib.sha256((ROOT/'docs/data/cmapss-manifest.json').read_bytes()).hexdigest()}
 output.write_text(json.dumps(result,separators=(',',':'),allow_nan=False))
 print('WROTE',output,len(records),parity,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--subset',choices=['FD001','FD002','FD003','FD004']);p.add_argument('--engines',type=int,default=12);a=p.parse_args();torch.set_num_threads(2)
 for subset in [a.subset] if a.subset else ['FD001','FD002','FD003','FD004']:
  export(subset,a.engines,ROOT/f'frontend/public/demo-{subset}.json')
 shutil.copy2(ROOT/'frontend/public/demo-FD004.json',ROOT/'frontend/public/demo.json')
