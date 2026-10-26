"""Load a trusted local run once and batch the same preprocessing/window/model pipeline as /predict."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import json,numpy as np,pandas as pd,torch
from rul_pm.config import load_config
from rul_pm.data.preprocess import CmapssPreprocessor
from rul_pm.data.windows import WindowArrays,left_pad,_window_stats
from rul_pm.models.xgb_model import XGBoostRulModel
from rul_pm.models.torch_models import build_torch_model
class Bundle:
 def __init__(self,path):
  self.path=Path(path);self.config=load_config(self.path/'config.yaml');self.metadata=json.loads((self.path/'metadata.json').read_text());self.name=self.metadata['model']
  self.pre=CmapssPreprocessor.load(self.path/'preprocessor.joblib');self.window=int(self.config['data']['window_length']);self.cap=float(self.config['data']['rul_cap'])
  if self.name=='xgboost':self.model=XGBoostRulModel.load(self.path/'model.joblib')
  else:
   ck=torch.load(self.path/'best.pt',map_location='cpu',weights_only=False);self.model=build_torch_model(self.name,ck['input_size'],ck['config']);self.model.load_state_dict(ck['state_dict']);self.model.eval()
 def inputs(self,raw):
  raw=raw.copy();columns=[c for c in raw if c.startswith(('sensor_','op_setting_'))];raw[columns]=raw[columns].astype(float)
  frame=self.pre.transform(raw);xs=[];masks=[];regimes=[];meta=[]
  for unit,group in frame.sort_values(['unit_number','time_in_cycles']).groupby('unit_number',sort=True):
   values=group[self.pre.feature_columns].to_numpy(dtype=np.float32)
   for i,(_,row) in enumerate(group.iterrows()):
    x,mask=left_pad(values[max(0,i-self.window+1):i+1],self.window);xs.append(x);masks.append(mask);regimes.append(row['regime_id']);meta.append((int(unit),int(row.time_in_cycles)))
  xs=np.asarray(xs,dtype=np.float32);masks=np.asarray(masks,dtype=bool)
  if self.name=='xgboost':
   x=np.asarray([_window_stats(v[m]) for v,m in zip(xs,masks)],dtype=np.float32)
   if self.config['data'].get('n_regimes',1)>1:x=np.column_stack([x,np.asarray(regimes,dtype=np.float32)])
  else:x=xs
  return x,masks,meta
 def predict(self,x,masks):
  if self.name=='xgboost':return np.clip(self.model.predict(x),0,self.cap)
  with torch.inference_mode():
   out=[self.model(torch.from_numpy(x[i:i+256]),torch.from_numpy(masks[i:i+256])).numpy() for i in range(0,len(x),256)]
  return np.clip(np.concatenate(out),0,self.cap)
 def frame(self,raw):
  x,mask,meta=self.inputs(raw);return self.predict(x,mask),meta
 def importance(self,raw,actual,sensors):
  x,mask,meta=self.inputs(raw);indices=np.linspace(0,len(x)-1,min(512,len(x)),dtype=int);x=x[indices];mask=mask[indices];y=np.array([actual[meta[i]] for i in indices]);base=np.abs(self.predict(x,mask)-y).mean();order=np.random.default_rng(42).permutation(len(x));result=[]
  for sensor in sensors:
   column=f'sensor_{sensor}'
   if column not in self.pre.feature_columns:result.append({'sensor':sensor,'deltaMae':0.0,'retained':False});continue
   j=self.pre.feature_columns.index(column);changed=x.copy()
   if self.name=='xgboost':
    features=len(self.pre.feature_columns);cols=[j+k*features for k in range(7)];changed[:,cols]=x[order][:,cols]
   else:changed[:,:,j]=x[order,:,j]
   delta=float(np.abs(self.predict(changed,mask)-y).mean()-base)
   result.append({'sensor':sensor,'deltaMae':round(delta,5),'retained':True})
  return sorted(result,key=lambda r:r['deltaMae'],reverse=True)
