"""Saved-component, provenance and deterministic reconstruction checks."""
import hashlib
import json
from pathlib import Path
from pxr import Usd,UsdGeom,UsdPhysics,Sdf
from . import builder


def geometry_fingerprint(scene):
    stage=Usd.Stage.Open(str(scene))
    digest=hashlib.sha256()
    for prim in stage.Traverse():
        values=[]
        for attr in prim.GetAttributes():
            if attr.GetTypeName() in (Sdf.ValueTypeNames.Asset,Sdf.ValueTypeNames.AssetArray):continue
            values.append((attr.GetName(),str(attr.Get())))
        values.sort()
        digest.update(repr((str(prim.GetPath()),prim.GetTypeName(),values)).encode())
    return digest.hexdigest()


def audit(cfg,output,rebuild=False):
    robot_dir=builder.ROBOT_DIR;env_dir=builder.ENV_DIR
    files=[robot_dir/name for name in ['pixmo.usd','mobile_base.usd','vacuum_gripper.usd']]
    files += [env_dir/name for name in ['warehouse.usd','pallet.usd','depalletizing_environment.usd','pixmo_depalletizing.usd']]
    checks=[]
    for path in files:
        s=Usd.Stage.Open(str(path))
        checks.append({'name':'reopen_'+path.name,'passed':bool(s and s.GetDefaultPrim()) and
                       UsdGeom.GetStageMetersPerUnit(s)==1 and UsdGeom.GetStageUpAxis(s)=='Z'})
    official=robot_dir/'vendor/fanuc/crx30ia/simready_usd/licenses'
    if not official.exists():official=builder.FANUC_FILE.parent/'licenses'
    checks.append({'name':'original_fanuc_license_and_notices','passed':all((official/n).stat().st_size>100
                  for n in ['LICENSE.txt','THIRD_PARTY_NOTICES.txt'])})
    original=geometry_fingerprint(env_dir/'pixmo_depalletizing.usd')
    duplicate=None
    if rebuild:
        builder.configure_output(output/'rebuild_assets')
        path,_=builder.build_scene(cfg)
        duplicate=geometry_fingerprint(path)
        checks.append({'name':'deterministic_composed_geometry','passed':original==duplicate,
                       'original_sha256':original,'rebuild_sha256':duplicate})
        builder.ROBOT_DIR=robot_dir;builder.ENV_DIR=env_dir
    report={'passed':all(c['passed'] for c in checks),'checks':checks}
    (output/'asset_audit.json').write_text(json.dumps(report,indent=2))
    print('PIXMO_ASSET_AUDIT',json.dumps(report),flush=True)
    if not report['passed']:raise RuntimeError('Saved asset audit failed')
    return report
