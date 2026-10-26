"""Data provenance and serving parity for the real portable research demo."""
import hashlib,json,os
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
SUBSETS=['FD001','FD002','FD003','FD004']
MODELS=['xgboost','lstm','gru','transformer']

def test_all_checkpoints_match_committed_manifest():
 manifest=json.loads((ROOT/'results/portfolio/manifest.json').read_text())
 assert {(r['subset'],r['model']) for r in manifest['runs']}=={(s,m) for s in SUBSETS for m in MODELS}
 for record in manifest['runs']:
  for name,expected in record['sha256'].items():assert hashlib.sha256((ROOT/record['run_dir']/name).read_bytes()).hexdigest()==expected

def test_source_manifest_covers_all_twelve_files():
 manifest=json.loads((ROOT/'docs/data/cmapss-manifest.json').read_text())
 assert set(manifest['files'])=={f'{prefix}_{subset}.txt' for subset in SUBSETS for prefix in ['train','test','RUL']}
 assert manifest['commit']=='2b562334f2114d9dadfc0861dededc16cf2550d9'

@pytest.mark.parametrize('subset',SUBSETS)
def test_real_export_has_no_fitted_engines_or_synthetic_predictions(subset):
 d=json.loads((ROOT/f'frontend/public/demo-{subset}.json').read_text())
 assert 'real' in d['predictionSource'] and len(d['engines'])==12
 for model in MODELS:
  metadata=json.loads((ROOT/d['checkpointPaths'][model]/'metadata.json').read_text())
  assert {e['id'] for e in d['engines']}<=set(metadata['val_units'])
  assert not {e['id'] for e in d['engines']}&set(metadata['train_units'])
  assert d['apiParityMaxAbsError'][model]<.001
  assert len(d['importance'][model])==21
  for e in d['engines']:
   assert all(np.isfinite(p[model]) and 0<=p[model]<=125 for p in e['points'])
   assert all(np.isfinite(p['whatIf'][model]['4']['10']) for p in e['points'])

@pytest.mark.parametrize('subset',SUBSETS)
@pytest.mark.parametrize('model',MODELS)
def test_static_prediction_and_perturbation_match_real_api(subset,model,monkeypatch):
 from fastapi.testclient import TestClient
 from rul_pm.api.app import create_app
 d=json.loads((ROOT/f'frontend/public/demo-{subset}.json').read_text());engine=d['engines'][0];p=engine['points'][79]
 monkeypatch.setenv('RULPM_ARTIFACT_DIR',str(ROOT/d['checkpointPaths'][model]))
 with TestClient(create_app()) as client:
  rows=[dict(point['row']) for point in engine['points'][50:80]]
  response=client.post('/predict',json={'rows':rows});assert response.status_code==200,response.text
  np.testing.assert_allclose(response.json()['predictions'][0]['predicted_rul'],p[model],atol=.001,rtol=0)
  for row in rows:row['sensor_4']*=1.1
  response=client.post('/predict',json={'rows':rows});assert response.status_code==200,response.text
  np.testing.assert_allclose(response.json()['predictions'][0]['predicted_rul'],p['whatIf'][model]['4']['10'],atol=.001,rtol=0)
