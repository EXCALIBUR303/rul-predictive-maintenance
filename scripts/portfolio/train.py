"""Reproducible reduced-budget portfolio training, independent of published runs."""
import json,sys,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
import torch
from rul_pm.config import load_config,save_config,config_hash
from rul_pm.experiment import train_one_model,evaluate_run

torch.set_num_threads(2)
ROOT=Path(__file__).resolve().parents[2]
models=['xgboost','lstm','gru','transformer']
runs=[]
for subset in ['FD001','FD002','FD003','FD004']:
 config=load_config(ROOT/'configs/fd004.yaml')
 config['experiment'].update(subset=subset,output_dir='artifacts/portfolio',seeds=[42])
 config['data']['n_regimes']=1 if subset in ['FD001','FD003'] else 6
 config['training'].update(max_epochs=3,patience=3,batch_size=256,learning_rate=.003,loss='mse')
 config['neural'].update(hidden_size=32,num_layers=1,d_model=32,nhead=4,dim_feedforward=64,dropout=.1)
 config['xgboost'].update(n_estimators=120,max_depth=4,learning_rate=.08,early_stopping_rounds=15,n_jobs=2)
 save_config(config,ROOT/f'configs/portfolio/{subset.lower()}.yaml')
 for model in models:
  run=ROOT/f'artifacts/portfolio/{subset}/{model}/seed_42'
  completion=run/'portfolio_complete.json'
  if completion.exists() and config_hash(load_config(run/"config.yaml"))!=config_hash(config):
   raise RuntimeError(f"Existing checkpoint settings mismatch: {run}; use a new versioned run directory")
  if not completion.exists():
   print('TRAIN',subset,model,flush=True)
   train_one_model(config,model,42)
   completion.write_text(json.dumps({'settings':'configs/portfolio/'+subset.lower()+'.yaml','completed':True}))
  else:print('REUSE',subset,model,flush=True)
  runs.append(run)
# Test files are first used only after all 16 training/selection runs finish.
manifest={'seed':42,'protocol':'reduced-budget single seed; not the published three-seed benchmark','runs':[]}
for run in runs:
 print('EVALUATE',run,flush=True)
 result=evaluate_run(run)
 meta=json.loads((run/'metadata.json').read_text()); model=meta['model'];subset=meta['subset']
 artifacts=['config.yaml','metadata.json','preprocessor.joblib','training_summary.json','feature_list.json','test_metrics.json','test_predictions.csv']+(['model.joblib','xgb_feature_names.json'] if model=='xgboost' else ['best.pt','training_log.csv'])
 hashes={name:hashlib.sha256((run/name).read_bytes()).hexdigest() for name in artifacts}
 manifest['runs'].append({'subset':subset,'model':model,'run_dir':str(run.relative_to(ROOT)),'sha256':hashes,'evaluation':result})
 destination=ROOT/'results/portfolio'/subset/model;destination.mkdir(parents=True,exist_ok=True)
 for name in ['test_metrics.json','test_predictions.csv','training_summary.json']:
  shutil.copy2(run/name,destination/name)
(ROOT/'results/portfolio/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('ALL 16 CHECKPOINTS TRAINED AND EVALUATED',flush=True)
