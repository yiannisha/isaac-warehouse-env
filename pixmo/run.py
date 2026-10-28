"""Build, reopen, render, and exercise Pixmo using the existing Isaac runtime."""
import argparse
import json
import sys
import traceback
import os
import shutil
import hashlib
import datetime
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
parser=argparse.ArgumentParser()
parser.add_argument('--headless',action='store_true')
parser.add_argument('--build-only',action='store_true')
parser.add_argument('--render-only',action='store_true',help='Reopen and render inspection views, then exit')
parser.add_argument('--audit-only',action='store_true',help='Audit saved components without simulating')
parser.add_argument('--check-reproducible',action='store_true',help='Rebuild in isolation and compare composed geometry')
parser.add_argument('--reuse',action='store_true',help='Reopen saved USD instead of rebuilding')
parser.add_argument('--validate',action='store_true')
parser.add_argument('--keep-open',action='store_true')
parser.add_argument('--cycles',type=int,default=3)
parser.add_argument('--config',type=Path)
parser.add_argument('--randomized',action='store_true')
parser.add_argument('--seed',type=int)
parser.add_argument('--asset-root',type=Path,help='Output asset directory; randomized layouts default to the run directory')
parser.add_argument('--output',type=Path)
args,_=parser.parse_known_args()
workspace=Path(os.environ.get('PIXMO_WORKSPACE',Path(__file__).resolve().parents[1]))
os.environ['PIXMO_WORKSPACE']=str(workspace)
args.output=(args.output or workspace/'artifacts'/('pixmo-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))).resolve()
args.output.mkdir(parents=True,exist_ok=False)
snapshot=args.output/'source';hashes={}
for package in ['pixmo','rack_sim']:
    for source in (workspace/package).glob('*.py'):
        target=snapshot/package/source.name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        hashes[str(source.relative_to(workspace))]=hashlib.sha256(target.read_bytes()).hexdigest()
(args.output/'source_manifest.json').write_text(json.dumps(hashes,indent=2))
config_source=(args.config or workspace/'configs/depalletizing_scene.json').resolve()
shutil.copy2(config_source,args.output/'config-input.json')
args.config=args.output/'config-input.json'
sys.path.insert(0,str(snapshot))
from isaacsim import SimulationApp
app=SimulationApp({'headless':args.headless,'width':1280,'height':800,
                   'window_width':1600,'window_height':1000,'multi_gpu':False,
                   'limit_cpu_threads':8,
                   'renderer':'RaytracedLighting','anti_aliasing':3})
try:
    from pixmo.config import load
    from pixmo import builder
    if args.asset_root or args.randomized:
        if args.reuse and not args.asset_root:raise ValueError('--reuse --randomized requires --asset-root')
        builder.configure_output(args.asset_root or args.output/'assets')
    cfg=load(args.config,args.randomized,args.seed)
    (args.output/'config.json').write_text(json.dumps(cfg,indent=2))
    if not args.reuse:
        scene,objects=builder.build_scene(cfg)
        print('PIXMO_BUILT',scene,flush=True)
    else:
        scene=builder.ENV_DIR/'pixmo_depalletizing.usd'
    if args.audit_only or args.check_reproducible:
        from pixmo.audit import audit
        audit(cfg,args.output,args.check_reproducible)
    if not (args.build_only or args.audit_only):
        from pixmo.runtime import run
        run(app,args,cfg,scene)
except Exception:
    traceback.print_exc()
    app.close()
    sys.exit(1)
app.close()
