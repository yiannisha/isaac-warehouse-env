"""Layered USD construction. Import after SimulationApp has started."""
import json
import math
import os
import shutil
from pathlib import Path
from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade, PhysxSchema
from rack_sim.geometry import box, xform, material, cylinder, curve, bind, rigid, collision
from .config import ROOT, boxes_for_pallet

ROBOT_DIR = ROOT / 'assets/robots/pixmo'
ENV_DIR = ROOT / 'assets/environments/pixmo_depalletizing'
FANUC_FILE=ROBOT_DIR/'vendor/fanuc/crx30ia/simready_usd/crx30ia.usd'


def configure_output(asset_root):
    global ROBOT_DIR,ENV_DIR
    ROBOT_DIR=Path(asset_root)/'robots/pixmo'
    ENV_DIR=Path(asset_root)/'environments/pixmo_depalletizing'


def configure_physics(s,cfg):
    scene=UsdPhysics.Scene.Define(s,'/World/PhysicsScene')
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81)
    physx=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    physx.CreateEnableCCDAttr(True);physx.CreateEnableStabilizationAttr(True)
    physx.CreateEnableGPUDynamicsAttr(False);physx.CreateBroadphaseTypeAttr('MBP');physx.CreateSolverTypeAttr('TGS')
    physx.CreateTimeStepsPerSecondAttr(round(1/cfg['physics_dt']))


def stage_file(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    s = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageUpAxis(s, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(s, 1)
    s.SetDefaultPrim(UsdGeom.Xform.Define(s, '/World').GetPrim())
    return s


def reference(s, path, file, pos=(0, 0, 0), yaw=0):
    p = xform(s, path, pos)
    relative = os.path.relpath(file, Path(s.GetRootLayer().realPath).parent)
    p.GetPrim().GetReferences().AddReference(relative)
    if yaw: p.AddRotateZOp().Set(yaw)
    return p.GetPrim()


def save(s):
    s.GetRootLayer().Save()


def physics_material(s, name, friction=.7, restitution=0):
    m = UsdShade.Material.Define(s, '/World/Materials/' + name)
    p = UsdPhysics.MaterialAPI.Apply(m.GetPrim())
    p.CreateStaticFrictionAttr(friction)
    p.CreateDynamicFrictionAttr(friction * .85)
    p.CreateRestitutionAttr(restitution)
    return m


def friction(prim, mat):
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat, materialPurpose='physics')


def color_texture(s,mat,file):
    base=str(mat.GetPath())
    shader=UsdShade.Shader.Get(s,base+'/Surface')
    tex=UsdShade.Shader.Define(s,base+'/Texture');tex.CreateIdAttr('UsdUVTexture')
    tex.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(file))
    tex.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
    tex.CreateInput('wrapS',Sdf.ValueTypeNames.Token).Set('repeat')
    tex.CreateInput('wrapT',Sdf.ValueTypeNames.Token).Set('repeat')
    uv=UsdShade.Shader.Define(s,base+'/UV');uv.CreateIdAttr('UsdPrimvarReader_float2')
    uv.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st')
    tex.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(uv.ConnectableAPI(),'result')
    shader.GetInput('diffuseColor').ConnectToSource(tex.ConnectableAPI(),'rgb')


def hose_points(s,root='/World'):
    inverse=UsdGeom.Xformable(s.GetPrimAtPath(root)).ComputeLocalToWorldTransform(0).GetInverse()
    anchors=[]
    for name,offset in [('Arm/base_link',(-.15,.18,.1)),('Arm/J1_link',(-.12,.18,0)),
                        ('Arm/J3_link',(-.08,.16,.16)),('Arm/J5_link',(0,.10,.13)),('Tool',(.02,.10,.12))]:
        m=UsdGeom.Xformable(s.GetPrimAtPath(root+'/'+name)).ComputeLocalToWorldTransform(0)
        anchors.append(inverse.Transform(m.Transform(Gf.Vec3d(*offset))))
    points=[]
    padded=[anchors[0],*anchors,anchors[-1]]
    for i in range(1,len(padded)-2):
        a,b,c,d=padded[i-1:i+3]
        for k in range(10):
            t=k/10
            points.append(Gf.Vec3f((b*2+(c-a)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5))
    points.append(Gf.Vec3f(anchors[-1]))
    return points


def build_base(cfg):
    s = stage_file(ROBOT_DIR / 'mobile_base.usd')
    l, w, h = cfg['robot']['base_size']
    blue = material(s, 'PixmoBlue', (.035, .065, .23), .35, .29)
    black = material(s, 'Rubber', (.012, .015, .019), .05, .65)
    silver = material(s, 'Aluminum', (.42, .46, .5), .8, .25)
    red = material(s, 'EmergencyRed', (.65, .01, .008), .0, .3)
    yellow = material(s, 'SafetyYellow', (.9, .67, .008), .1, .4)
    led = material(s, 'StatusLight', (.55, .8, 1), .1, .2, (.55, .8, 1))
    xform(s, '/World/Visual')
    box(s, '/World/Visual/LowerSkirt', (0, 0, .105), (l-.08, w-.06, .15), black)
    # Chamfered housing with sloped upper shoulders, separately from collision.
    outline = [(-l/2+.07,-w/2), (l/2-.07,-w/2), (l/2,-w/2+.07),
               (l/2,w/2-.07),(l/2-.07,w/2),(-l/2+.07,w/2),
               (-l/2,w/2-.07),(-l/2,-w/2+.07)]
    pts = [(x,y,z) for z in (.17,h-.08) for x,y in outline]
    pts += [(x*.94,y*.94,h) for x,y in outline]
    faces = [tuple(range(7,-1,-1)), tuple(range(16,24))]
    for level in range(2):
        faces += [(level*8+i,level*8+(i+1)%8,(level+1)*8+(i+1)%8,(level+1)*8+i) for i in range(8)]
    mesh = UsdGeom.Mesh.Define(s, '/World/Visual/Housing')
    mesh.CreatePointsAttr(pts); mesh.CreateFaceVertexCountsAttr([len(f) for f in faces])
    mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]); mesh.CreateSubdivisionSchemeAttr('none')
    bind(mesh.GetPrim(), blue)
    for side in (-1,1):
        for i in range(2):
            x = -.31 + i*.62
            box(s,f'/World/Visual/Panel_{side}_{i}'.replace('-','m'),(x,side*(w/2+.002),.37),(.55,.006,.32),blue)
            box(s,f'/World/Visual/Handle_{side}_{i}'.replace('-','m'),(x,side*(w/2+.008),.43),(.095,.012,.014),silver)
            box(s,f'/World/Visual/LED_{side}_{i}'.replace('-','m'),(x,side*(w/2+.012),.30),(.09,.008,.012),led)
        cylinder(s,f'/World/Visual/EstopRing_{side}'.replace('-','m'),(.5,side*(w/2+.01),.46),.035,.012,yellow,axis='Y')
        cylinder(s,f'/World/Visual/Estop_{side}'.replace('-','m'),(.5,side*(w/2+.024),.46),.021,.025,red,axis='Y')
    mount = cfg['robot']['mount']
    box(s,'/World/Visual/Riser',(mount[0],mount[1],(h+mount[2])/2),(.4,.38,mount[2]-h),black)
    for i in range(9):
        box(s,f'/World/Visual/Bellows_{i}',(mount[0],mount[1],h+i*(mount[2]-h)/9),(.43,.41,.013),black)
    box(s,'/World/Visual/SensorMast',(-.4,.26,1.12),(.07,.07,.96),black)
    box(s,'/World/Visual/SensorHead',(-.4,.26,1.63),(.12,.11,.22),black)
    box(s,'/World/Visual/SensorLight',(-.4,.20,1.66),(.07,.008,.13),led)
    for i,y in enumerate([-.26,.26]):
        box(s,f'/World/Visual/EndHandle_{i}',(l/2+.003,y,.43),(.014,.09,.012),silver)
        box(s,f'/World/Visual/EndStatus_{i}',(l/2+.008,y,.34),(.008,.085,.012),led)
    box(s,'/World/Visual/EndPanel',(l/2+.004,0,.32),(.008,.17,.22),black)
    for i in range(5):box(s,f'/World/Visual/EndVent_{i}',(l/2+.009,0,.25+i*.027),(.008,.11,.006),silver)
    cylinder(s,'/World/Visual/EndEstopRing',(l/2+.014,.28,.51),.034,.014,yellow,axis='X')
    cylinder(s,'/World/Visual/EndEstop',(l/2+.028,.28,.51),.021,.025,red,axis='X')
    col = box(s,'/World/Collision',(0,0,h/2), (l-.02,w-.02,h),collide=True)
    col.CreateVisibilityAttr('invisible')
    save(s)


def cup(s, path, y, z, mat):
    # Bellows rings and an open lip; cup mouth lies at X=.22 m.
    points=[]; counts=[]; indices=[]
    profile=[(.13,.015),(.15,.023),(.16,.018),(.18,.029),(.19,.021),(.213,.036),(.22,.037),(.22,.029)]
    n=32
    for xx,r in profile:
        points.extend([(xx,y+r*math.cos(i*2*math.pi/n),z+r*math.sin(i*2*math.pi/n)) for i in range(n)])
    for k in range(len(profile)-1):
        for i in range(n):
            counts.append(4); indices.extend([k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i])
    m=UsdGeom.Mesh.Define(s,path);m.CreatePointsAttr(points);m.CreateFaceVertexCountsAttr(counts)
    m.CreateFaceVertexIndicesAttr(indices);m.CreateSubdivisionSchemeAttr('none');m.CreateDoubleSidedAttr(True)
    bind(m.GetPrim(),mat)


def build_gripper(cfg):
    s=stage_file(ROBOT_DIR/'vacuum_gripper.usd')
    silver=material(s,'ToolAluminum',(.4,.44,.47),.8,.24)
    green=material(s,'SuctionGreen',(.07,.5,.20),.0,.55)
    black=material(s,'HoseRubber',(.018,.023,.024),.0,.7)
    cylinder(s,'/World/Flange',(.025,0,0),.058,.05,silver,axis='X')
    adapter=cfg['robot'].get('wrist_adapter_m',.08)
    cylinder(s,'/World/WristStandoff',(-adapter/2,0,0),.045,adapter,silver,axis='X')
    box(s,'/World/Adapter',(.075,0,0),(.06,.16,.14),silver)
    box(s,'/World/Manifold',(.115,0,0),(.035,.44,.28),silver,True)
    for row,y in enumerate([-.16,-.0533,.0533,.16]):
        for col,z in enumerate([-.09,0,.09]):
            cup(s,f'/World/Cup_{row}_{col}',y,z,green)
            lip=cylinder(s,f'/World/ContactLip_{row}_{col}',(.216,y,z),.035,.008,green,axis='X')
            collision(lip.GetPrim(),.001);lip.CreateVisibilityAttr('invisible')
    for side in (-1,1):
        curve(s,f'/World/VacuumHose_{side}'.replace('-','m'),[(0,0,0),(.0,side*.25,.2),(.1,side*.28,.15),(.115,side*.18,.09)],.014,black)
    xform(s,'/World/ContactPlane',(.22,0,0))
    s.GetDefaultPrim().SetCustomDataByKey('payload_kg',cfg['robot']['payload_kg'])
    s.GetDefaultPrim().SetCustomDataByKey('attachment_model','Contact-validated fixed joint; no pressure simulation')
    mass=cfg['robot'].get('gripper_mass_kg',3.2)
    rigid(s.GetDefaultPrim(),mass)
    PhysxSchema.PhysxRigidBodyAPI(s.GetDefaultPrim()).CreateSolverPositionIterationCountAttr(32)
    PhysxSchema.PhysxRigidBodyAPI(s.GetDefaultPrim()).CreateSolverVelocityIterationCountAttr(4)
    api=UsdPhysics.MassAPI(s.GetDefaultPrim())
    api.CreateCenterOfMassAttr(Gf.Vec3f(.115,0,0))
    api.CreateDiagonalInertiaAttr(Gf.Vec3f(mass*(.44**2+.28**2)/12,
        mass*(.22**2+.28**2)/12,mass*(.22**2+.44**2)/12))
    save(s)


def build_robot(cfg):
    build_base(cfg);build_gripper(cfg)
    s=stage_file(ROBOT_DIR/'pixmo.usd')
    base=xform(s,'/World/Base').GetPrim();rigid(base,350)
    PhysxSchema.PhysxRigidBodyAPI(base).CreateSolverPositionIterationCountAttr(32)
    PhysxSchema.PhysxRigidBodyAPI(base).CreateSolverVelocityIterationCountAttr(4)
    reference(s,'/World/Base/Body',ROBOT_DIR/'mobile_base.usd')
    arm=reference(s,'/World/Arm',FANUC_FILE,cfg['robot']['mount'])
    arm.GetVariantSet('PhysX').SetVariantSelection('Enabled')
    arm.GetVariantSet('Newton').SetVariantSelection('Disabled')
    arm.GetVariantSet('Sensor').SetVariantSelection('None')
    # The original six joints, axes, frames, limits, meshes and inertias remain intact.
    root=s.GetPrimAtPath('/World/Arm/root_joint')
    root.RemoveAPI(UsdPhysics.ArticulationRootAPI)
    root.RemoveAPI(PhysxSchema.PhysxArticulationAPI)
    j=UsdPhysics.FixedJoint(root)
    j.CreateBody0Rel().SetTargets(['/World/Base'])
    j.CreateLocalPos0Attr(Gf.Vec3f(*cfg['robot']['mount']))
    UsdPhysics.ArticulationRootAPI.Apply(s.GetDefaultPrim())
    a=PhysxSchema.PhysxArticulationAPI.Apply(s.GetDefaultPrim())
    a.CreateEnabledSelfCollisionsAttr(True)
    a.CreateSolverPositionIterationCountAttr(64);a.CreateSolverVelocityIterationCountAttr(8)
    # External planar constraint: X/Y/yaw free, Z/roll/pitch locked.
    planar=UsdPhysics.Joint.Define(s,'/World/PlanarConstraint')
    planar.CreateBody1Rel().SetTargets(['/World/Base'])
    planar.CreateExcludeFromArticulationAttr(True)
    for axis in ['transZ','rotX','rotY']:
        lim=UsdPhysics.LimitAPI.Apply(planar.GetPrim(),axis);lim.CreateLowAttr(1);lim.CreateHighAttr(-1)
    for axis in ['transX','transY','rotZ']:
        d=UsdPhysics.DriveAPI.Apply(planar.GetPrim(),axis)
        d.CreateTypeAttr('force');d.CreateStiffnessAttr(1e7);d.CreateDampingAttr(1e5)
        d.CreateMaxForceAttr(2e5);d.CreateTargetPositionAttr(0)
    for i in range(1,7):
        joint=UsdPhysics.RevoluteJoint.Get(s,f'/World/Arm/joints/J{i}')
        drive=UsdPhysics.DriveAPI.Get(joint.GetPrim(),'angular')
        drive.CreateStiffnessAttr(40000);drive.CreateDampingAttr(1000)
    # A separately massed tool preserves all original FANUC link inertias.
    wrist=s.GetPrimAtPath('/World/Arm/J6_link')
    wrist_matrix=UsdGeom.Xformable(wrist).ComputeLocalToWorldTransform(0)
    adapter=cfg['robot'].get('wrist_adapter_m',.08)
    reference(s,'/World/Tool',ROBOT_DIR/'vacuum_gripper.usd',wrist_matrix.Transform(Gf.Vec3d(adapter,0,0)))
    tool_joint=UsdPhysics.FixedJoint.Define(s,'/World/WristToolJoint')
    tool_joint.CreateBody0Rel().SetTargets(['/World/Arm/J6_link'])
    tool_joint.CreateBody1Rel().SetTargets(['/World/Tool'])
    tool_joint.CreateLocalPos0Attr(Gf.Vec3f(adapter,0,0))
    tool_joint.CreateCollisionEnabledAttr(False)
    sheath=material(s,'ServiceHoseRubber',(.012,.016,.02),.0,.6)
    curve(s,'/World/ServiceHose',hose_points(s),.022,sheath)
    s.GetPrimAtPath('/World/Arm/physicsScene').SetActive(False) if s.GetPrimAtPath('/World/Arm/physicsScene') else None
    # Disable any imported secondary physics scenes.
    for p in list(s.Traverse()):
        if p.IsA(UsdPhysics.Scene): p.SetActive(False)
    friction(base,physics_material(s,'BaseContact',.6))
    for p in s.Traverse():
        if p.HasAPI(UsdPhysics.RigidBodyAPI):
            PhysxSchema.PhysxContactReportAPI.Apply(p).CreateThresholdAttr(0)
    save(s)
    build_kinematics(s,cfg)


def build_kinematics(s,cfg):
    """Lula URDF derived from the original USD frames; no substituted kinematics."""
    import xml.etree.ElementTree as ET
    robot=ET.Element('robot',name='fanuc_crx30ia')
    for name in ['base_link']+[f'J{i}_link' for i in range(1,7)]+['suction_tcp']:
        ET.SubElement(robot,'link',name=name)
    for i in range(1,7):
        j=UsdPhysics.RevoluteJoint.Get(s,f'/World/Arm/joints/J{i}')
        r0=Gf.Rotation(j.GetLocalRot0Attr().Get());r1=Gf.Rotation(j.GetLocalRot1Attr().Get())
        # All official rest link rotations are identity; preserve rotated joint axes.
        rot=r0*r1.GetInverse()
        if rot.GetAngle()>1e-4: raise ValueError('Expected identity rest-link rotation')
        axis={'X':Gf.Vec3d(1,0,0),'Y':Gf.Vec3d(0,1,0),'Z':Gf.Vec3d(0,0,1)}[j.GetAxisAttr().Get()]
        axis=r1.TransformDir(axis)
        origin=j.GetLocalPos0Attr().Get()-j.GetLocalPos1Attr().Get()
        joint=ET.SubElement(robot,'joint',name=f'J{i}',type='revolute')
        ET.SubElement(joint,'parent',link='base_link' if i==1 else f'J{i-1}_link')
        ET.SubElement(joint,'child',link=f'J{i}_link')
        ET.SubElement(joint,'origin',xyz=' '.join(map(str,origin)),rpy='0 0 0')
        ET.SubElement(joint,'axis',xyz=' '.join(map(str,axis)))
        ET.SubElement(joint,'limit',lower=str(math.radians(j.GetLowerLimitAttr().Get())),
                      upper=str(math.radians(j.GetUpperLimitAttr().Get())),effort='150',velocity='1.2')
    j=ET.SubElement(robot,'joint',name='suction_mount',type='fixed')
    ET.SubElement(j,'parent',link='J6_link');ET.SubElement(j,'child',link='suction_tcp')
    ET.SubElement(j,'origin',xyz=f"{.22+cfg['robot'].get('wrist_adapter_m',.08)} 0 0",rpy='0 0 0')
    ET.indent(robot)
    ET.ElementTree(robot).write(ROBOT_DIR/'fanuc_kinematics.urdf')
    (ROBOT_DIR/'lula_robot_description.yaml').write_text('''api_version: 1.0
cspace: [J1, J2, J3, J4, J5, J6]
default_q: [0, -0.4, -1.5, 0, -1.2, 0]
acceleration_limits: [2, 2, 2, 2, 2, 2]
jerk_limits: [10, 10, 10, 10, 10, 10]
cspace_to_urdf_rules: []
collision_spheres: []
''')


def build_pallet(cfg):
    dest=ENV_DIR/'vendor/pallet';dest.mkdir(parents=True,exist_ok=True)
    refs=ROOT/'references/pixmo'
    shutil.copy2(refs/'nvidia_pallet.usd',dest/'pallet.usd')
    license_file=Path('/isaac-sim/LICENSE.txt')
    if license_file.exists():shutil.copy2(license_file,dest/'LICENSE-Isaac-Sim.txt')
    # Preserve the original pallet's MDL reference as a local dependency too,
    # even though the portable PreviewSurface material overrides its binding.
    shutil.copytree(FANUC_FILE.parent/'materials/mdl',dest,dirs_exist_ok=True)
    tex=dest/'Materials/Textures';tex.mkdir(parents=True,exist_ok=True)
    shutil.copy2(refs/'pallet_diffuse.tga',tex/'FOF_Map_Palette_A_D.tga')
    shutil.copy2(refs/'pallet_normal.tga',tex/'FOF_Map_Palette_A_N.tga')
    s=stage_file(ENV_DIR/'pallet.usd')
    prim=reference(s,'/World/Visual',dest/'pallet.usd')
    # Normalize the actual authored dimensions, which differ from the file metadata.
    bounds=UsdGeom.BBoxCache(0,['default']).ComputeWorldBound(prim).ComputeAlignedBox()
    size=bounds.GetSize();target=cfg['pallet_size']
    UsdGeom.Xformable(prim).AddScaleOp().Set(Gf.Vec3f(*[target[i]/size[i] for i in range(3)]))
    for p in Usd.PrimRange(prim):
        if p.HasAPI(UsdPhysics.CollisionAPI):UsdPhysics.CollisionAPI(p).CreateCollisionEnabledAttr(False)
    wood=material(s,'Wood',(.48,.33,.16),.0,.8)
    shader=UsdShade.Shader.Get(s,'/World/Materials/Wood/Surface')
    texture=UsdShade.Shader.Define(s,'/World/Materials/Wood/Texture');texture.CreateIdAttr('UsdUVTexture')
    texture.CreateInput('file',Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath('vendor/pallet/Materials/Textures/FOF_Map_Palette_A_D.tga'))
    texture.CreateInput('sourceColorSpace',Sdf.ValueTypeNames.Token).Set('sRGB')
    uv=UsdShade.Shader.Define(s,'/World/Materials/Wood/UV');uv.CreateIdAttr('UsdPrimvarReader_float2')
    uv.CreateInput('varname',Sdf.ValueTypeNames.Token).Set('st')
    texture.CreateInput('st',Sdf.ValueTypeNames.Float2).ConnectToSource(uv.ConnectableAPI(),'result')
    shader.GetInput('diffuseColor').ConnectToSource(texture.ConnectableAPI(),'rgb')
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(wood,bindingStrength=UsdShade.Tokens.strongerThanDescendants)
    # Static compound slats, avoiding a convex hull that fills the fork openings.
    l,w,h=target
    for i in range(7):box(s,f'/World/Colliders/Top_{i}',(0,-w/2+(i+.5)*w/7,h-.011),(l,w/7-.02,.022),collide=True)
    for i in range(3):
        y=(i-1)*(w/2-.055)
        box(s,f'/World/Colliders/Stringer_{i}',(0,y,h/2),(l,.075,h-.04),collide=True)
        box(s,f'/World/Colliders/Foot_{i}',(0,y,.01),(l,.10,.02),collide=True)
    UsdGeom.Imageable(s.GetPrimAtPath('/World/Colliders')).CreateVisibilityAttr('invisible')
    friction(s.GetDefaultPrim(),physics_material(s,'WoodContact',.75))
    save(s)


def build_warehouse(cfg):
    s=stage_file(ENV_DIR/'warehouse.usd')
    concrete=material(s,'Concrete',(.31,.33,.32),.05,.65)
    color_texture(s,concrete,'textures/concrete.png')
    wall=material(s,'Wall',(.42,.43,.42),.05,.8)
    steel=material(s,'StructuralSteel',(.15,.17,.16),.6,.4)
    yellow=material(s,'SafetyYellow',(.83,.78,.015),.15,.4)
    silver=material(s,'ElectricalCabinet',(.38,.41,.39),.5,.35)
    l,w,h=cfg['warehouse']['size'];wy=cfg['warehouse']['wall_y']
    floor=box(s,'/World/Floor',(0,0,-.10),(l,w,.2),concrete,True)
    # Large falling cartons need an anticipatory contact skin; the rack helper's
    # 50 micrometer default is intended for millimeter-scale connector mechanics.
    collision(floor.GetPrim(),.02)
    UsdGeom.PrimvarsAPI(floor.GetPrim()).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,'faceVarying').Set(
        [(0,0),(24,0),(24,24),(0,24)]*6)
    friction(s.GetPrimAtPath('/World/Floor'),physics_material(s,'FloorContact',.65))
    box(s,'/World/RearWall',(0,wy,h/2),(l,.16,h),wall,True)
    for i,x in enumerate([-7,-3.5,3.5,7]):
        box(s,f'/World/Column_{i}',(x,wy-.22,h/2),(.25,.3,h),steel,True)
        box(s,f'/World/Beam_{i}',(x,0,h-.25),(.13,w,.25),steel)
    for i,x in enumerate([-5.0,-2.0,2.0,5.0]):
        box(s,f'/World/DockPanel_{i}',(x,wy-.1,2.2),(2.3,.06,3.8),silver)
        for k in range(7):box(s,f'/World/DockSeam_{i}_{k}',(x,wy-.14,.6+k*.5),(2.3,.01,.012),steel)
        box(s,f'/World/ControlCabinet_{i}',(x+.9,wy-.35,1.3),(.38,.25,.8),silver,True)
    for i,x in enumerate([-6,-4,-2,0,2,4,6]):
        cylinder(s,f'/World/RailPost_{i}',(x,wy-.9,.53),.04,1.06,yellow,axis='Z')
        if i<6:box(s,f'/World/SafetyRail_{i}',(x+1,wy-.9,.9),(1.95,.06,.08),yellow,True)
        curve(s,f'/World/WallConduit_{i}',[(x,wy-.2,1.6),(x,wy-.2,4),(x+.1,wy-.2,5.6)],.012,silver)
    save(s)


def build_environment(cfg):
    from .textures import generate
    generate(ENV_DIR/'textures')
    build_pallet(cfg);build_warehouse(cfg)
    s=stage_file(ENV_DIR/'depalletizing_environment.usd')
    configure_physics(s,cfg)
    reference(s,'/World/Warehouse',ENV_DIR/'warehouse.usd')
    cardboard=[material(s,f'Cardboard_{i}',color,.0,.85) for i,color in enumerate([(.55,.40,.22),(.64,.48,.28),(.49,.35,.19)])]
    for i,mat in enumerate(cardboard):color_texture(s,mat,f'textures/cardboard_{i}.png')
    tape=material(s,'PackingTape',(.60,.46,.28),.05,.35)
    label=material(s,'PaperLabel',(.85,.85,.79),.0,.8)
    ink=material(s,'CartonInk',(.075,.055,.035),.0,.9)
    carton_contact=physics_material(s,'CardboardContact',.65)
    records=[]
    for pindex,p in enumerate(cfg['pallets']):
        path='/World/Pallets/'+p['name']
        reference(s,path,ENV_DIR/'pallet.usd',p['position'])
        for b in boxes_for_pallet(p,cfg['pallet_size'],cfg['seed']+pindex):
            bp=f"/World/Boxes/{p['name']}/{b['name']}"
            root=xform(s,bp,b['position']).GetPrim();rigid(root,b['mass']);friction(root,carton_contact)
            PhysxSchema.PhysxRigidBodyAPI(root).CreateSolverPositionIterationCountAttr(32)
            PhysxSchema.PhysxRigidBodyAPI(root).CreateSolverVelocityIterationCountAttr(4)
            PhysxSchema.PhysxContactReportAPI.Apply(root).CreateThresholdAttr(0)
            root.SetCustomDataByKey('semantic:class','cardboard_box')
            root.SetCustomDataByKey('semantic:source',p['name'])
            root.SetCustomDataByKey('box_size',Gf.Vec3d(*b['size']))
            sx,sy,sz=b['size']
            carton=box(s,bp+'/Carton',(0,0,0),b['size'],cardboard[b['sku']],True)
            collision(carton.GetPrim(),.002)
            UsdGeom.PrimvarsAPI(carton.GetPrim()).CreatePrimvar('st',Sdf.ValueTypeNames.TexCoord2fArray,'faceVarying').Set(
                [(0,0),(1,0),(1,1),(0,1)]*6)
            box(s,bp+'/Tape',(0,0,sz/2+.0003),(sx,.045,.0006),tape)
            for sign in (-1,1):
                suffix='Front' if sign<0 else 'Back'
                box(s,bp+'/Label'+suffix,(sx*.28,sign*(sy/2+.0005),-.035),(.065,.001,.047),label)
                for k in range(5):box(s,bp+f'/Print{suffix}_{k}',(-sx*.22,sign*(sy/2+.0005),sz*.23-k*.012),(.11-k*.009,.001,.003),ink)
                for k in range(9):box(s,bp+f'/Barcode{suffix}_{k}',(sx*.28-.025+k*.006,sign*(sy/2+.0012),-.035),(.002,.0005,.028),ink)
            records.append(dict(b,path=bp,pallet=p['name']))
    c=cfg['conveyor'];cx,cy,cz=c['center'];l=c['length'];w=c['width']
    steel=material(s,'ConveyorFrame',(.025,.03,.035),.65,.35)
    roller=material(s,'RollerSteel',(.55,.59,.63),.9,.22)
    for i,side in enumerate([-1,1]):
        box(s,f'/World/Conveyor/Rail_{i}',(cx,cy+side*(w/2+.03),cz-.04),(l,.06,.12),steel,True)
    for i in range(int(l/.075)):
        cylinder(s,f'/World/Conveyor/Roller_{i:03d}',(cx-l/2+.04+i*.075,cy,cz-.027),.027,w,roller,axis='Y')
    for i,x in enumerate([-4,-2,0,2,4]):
        for j,side in enumerate([-1,1]):box(s,f'/World/Conveyor/Leg_{i}_{j}',(cx+x,cy+side*w*.4,(cz-.1)/2),(.055,.055,cz-.1),steel,True)
    # Existing PhysX surface-velocity component drives boxes through contact forces.
    deck=box(s,'/World/Conveyor/ContactSurface',(cx,cy,cz-.008),(l,w,.016),collide=True)
    deck.CreateVisibilityAttr('invisible')
    collision(deck.GetPrim(),.002)
    UsdPhysics.RigidBodyAPI.Apply(deck.GetPrim()).CreateKinematicEnabledAttr(True)
    vel=PhysxSchema.PhysxSurfaceVelocityAPI.Apply(deck.GetPrim())
    vel.CreateSurfaceVelocityAttr(Gf.Vec3f(c['speed_m_s'],0,0))
    vel.CreateSurfaceVelocityLocalSpaceAttr(False)
    friction(deck.GetPrim(),physics_material(s,'ConveyorContact',.8))
    s.GetDefaultPrim().SetCustomDataByKey('scene:coordinates','meters; Z-up; conveyor along X; source +Y; destination -Y')
    save(s)
    (ENV_DIR/'objects.json').write_text(json.dumps(records,indent=2))
    return records


def build_scene(cfg):
    build_robot(cfg);objects=build_environment(cfg)
    s=stage_file(ENV_DIR/'pixmo_depalletizing.usd')
    reference(s,'/World/Environment',ENV_DIR/'depalletizing_environment.usd')
    s.GetPrimAtPath('/World/Environment/PhysicsScene').SetActive(False)
    for i,pose in enumerate(cfg['robots']):
        robot=reference(s,f'/World/Robots/Pixmo_{i:02d}',ROBOT_DIR/'pixmo.usd',pose['position'],pose['yaw_deg'])
        # World anchors are expressed in the global scene frame.
        j=UsdPhysics.Joint.Get(s,str(robot.GetPath())+'/PlanarConstraint')
        j.CreateLocalPos0Attr(Gf.Vec3f(*pose['position']))
        j.CreateLocalRot0Attr(Gf.Quatf(Gf.Rotation(Gf.Vec3d(0,0,1),pose['yaw_deg']).GetQuat()))
    configure_physics(s,cfg)
    light=UsdLux.DomeLight.Define(s,'/World/Lighting/Ambient');light.CreateIntensityAttr(cfg['lighting']['dome_intensity'])
    light.CreateColorAttr(Gf.Vec3f(.87,.92,1))
    for i,(x,y) in enumerate([(-4,-1),(0,-1),(4,-1),(-4,3),(0,3),(4,3)]):
        l=UsdLux.RectLight.Define(s,f'/World/Lighting/Overhead_{i}')
        l.AddTranslateOp().Set(Gf.Vec3d(x,y,6))
        l.CreateWidthAttr(2);l.CreateHeightAttr(1);l.CreateIntensityAttr(cfg['lighting']['overhead_intensity'])
    for name,cam in cfg['cameras'].items():
        c=UsdGeom.Camera.Define(s,'/World/Cameras/'+name)
        c.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*cam['eye']),Gf.Vec3d(*cam['target']),Gf.Vec3d(0,0,1)).GetInverse())
        c.CreateClippingRangeAttr(Gf.Vec2f(.01,100));c.CreateFocalLengthAttr(24)
    save(s)
    return ENV_DIR/'pixmo_depalletizing.usd',objects
