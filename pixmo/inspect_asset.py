from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "renderer": "RaytracedLighting"})
from pxr import Usd, UsdPhysics, UsdGeom
from pathlib import Path
s = Usd.Stage.Open('/workspace/assets/robots/pixmo/vendor/fanuc/crx30ia/simready_usd/crx30ia.usd')
p = s.GetDefaultPrim()
print('VARIANTS', [(v,p.GetVariantSet(v).GetVariantNames()) for v in p.GetVariantSets().GetNames()], flush=True)
for v in p.GetVariantSets().GetNames():
    if 'PhysX' in p.GetVariantSet(v).GetVariantNames(): p.GetVariantSet(v).SetVariantSelection('PhysX')
    if 'Physx' in p.GetVariantSet(v).GetVariantNames(): p.GetVariantSet(v).SetVariantSelection('Physx')
Path('/workspace/references/pixmo/arm_structure.usda').write_text(s.Flatten().ExportToString())
for x in s.Traverse():
    if x.GetTypeName() in ('Xform','PhysicsRevoluteJoint','PhysicsFixedJoint','PhysicsScene'):
        print('PRIM', x.GetPath(), x.GetTypeName(), flush=True)
        if x.IsA(UsdPhysics.Joint):
            print([(a.GetName(),str(a.Get())) for a in x.GetAttributes()],flush=True)
app.close()
