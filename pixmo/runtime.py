"""Joint-commanded manipulation, measured suction, planar drive, validation."""
import json
import math
import time
from pathlib import Path
import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, PhysxSchema
from .builder import ROOT, ROBOT_DIR, ENV_DIR


def world_matrix(stage,path):
    return UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(Usd.TimeCode.Default())


def pose(stage,path):
    m=world_matrix(stage,path)
    q=m.ExtractRotationQuat()
    return np.array(m.ExtractTranslation()),np.array([q.GetReal(),*q.GetImaginary()])


class Suction:
    """Replaceable approximation: validated top-face seal, then dynamic fixed joint.

    The box is never made kinematic or teleported. Both bodies remain dynamic.
    """
    def __init__(self,stage,robot_path,cfg):
        self.stage=stage;self.robot_path=robot_path;self.cfg=cfg
        self.wrist=robot_path+'/Arm/J6_link'
        self.tool=robot_path+'/Tool'
        self.tcp=robot_path+'/Tool/ContactPlane'
        self.joint_path=robot_path+'/SuctionAttachment'
        self.attached=None;self.events=[]

    def assess(self,box_path):
        s=self.stage
        p=s.GetPrimAtPath(box_path)
        size=np.array(p.GetCustomDataByKey('box_size'))
        mass=UsdPhysics.MassAPI(p).GetMassAttr().Get()
        bm=world_matrix(s,box_path);wm=world_matrix(s,self.tool)
        inv=bm.GetInverse()
        normal=np.array(inv.TransformDir(wm.TransformDir(Gf.Vec3d(1,0,0))))
        errors=[];inside=True
        # Outer cup extents must lie within the observed top-face footprint.
        for y in [-.197,.197]:
            for z in [-.127,.127]:
                point=np.array(inv.Transform(wm.Transform(Gf.Vec3d(.22,y,z))))
                errors.append(float(point[2]-size[2]/2))
                inside=inside and abs(point[0])<size[0]/2-.002 and abs(point[1])<size[1]/2-.002
        result={'box':box_path,'mass_kg':mass,'cup_plane_gaps_m':errors,
                'normal_dot_down':float(-normal[2]),'footprint_inside':bool(inside)}
        result['valid']=bool(inside and mass<=self.cfg['robot']['payload_kg'] and
            -normal[2]>math.cos(math.radians(8)) and
            max(abs(e) for e in errors)<=self.cfg['robot']['cup_contact_tolerance_m'])
        return result

    def attach(self,box_path):
        if self.attached: raise RuntimeError('Suction already holding a box')
        contact=self.assess(box_path)
        if not contact['valid']: raise RuntimeError('Invalid suction contact: '+json.dumps(contact))
        bm=world_matrix(self.stage,box_path);wm=world_matrix(self.stage,self.wrist)
        # Match existing frames exactly. Creating the joint adds no pose discontinuity.
        relative=bm*wm.GetInverse()
        j=UsdPhysics.FixedJoint.Define(self.stage,self.joint_path)
        j.CreateBody0Rel().SetTargets([self.wrist]);j.CreateBody1Rel().SetTargets([box_path])
        j.CreateLocalPos0Attr(Gf.Vec3f(relative.ExtractTranslation()))
        j.CreateLocalRot0Attr(Gf.Quatf(relative.ExtractRotationQuat()))
        j.CreateLocalPos1Attr(Gf.Vec3f(0));j.CreateLocalRot1Attr(Gf.Quatf(1))
        j.CreateExcludeFromArticulationAttr(True)
        j.CreateBreakForceAttr(self.cfg['robot']['payload_kg']*9.81*3)
        self.attached=box_path
        self.events.append(dict(contact,event='attach'))
        return contact

    def release(self):
        box=self.attached
        if box:
            UsdPhysics.Joint.Get(self.stage,self.joint_path).GetJointEnabledAttr().Set(False)
            self.stage.RemovePrim(self.joint_path)
            # PhysX may put an externally constrained carton to sleep while the
            # wrist rests. Removing that joint does not automatically wake it.
            import omni.usd
            from omni.physx import get_physx_simulation_interface
            from pxr import PhysicsSchemaTools
            get_physx_simulation_interface().wake_up(omni.usd.get_context().get_stage_id(),
                                                    PhysicsSchemaTools.sdfPathToInt(Sdf.Path(box)))
            self.events.append({'event':'release','box':box,'position':pose(self.stage,box)[0].tolist()})
        self.attached=None
        return box


class Simulation:
    def __init__(self,app,cfg,output):
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.types import ArticulationAction
        from isaacsim.core.utils.extensions import enable_extension
        enable_extension('isaacsim.robot_motion.motion_generation')
        from isaacsim.robot_motion.motion_generation import LulaKinematicsSolver
        self.app=app;self.cfg=cfg;self.output=output
        self.Action=ArticulationAction
        self.stage=omni.usd.get_context().get_stage()
        from omni.physx import get_physx_simulation_interface
        self.contact_count=0;self.self_contact_count=0;self.max_penetration=0.
        self.contact_pairs={};self.contacts_enabled=True
        self.penetration_pairs={};self.recent_penetration=[]
        self.contact_subscription=get_physx_simulation_interface().subscribe_contact_report_events(self.on_contacts)
        self.world=World(physics_dt=cfg['physics_dt'],rendering_dt=1/60,
                         stage_units_in_meters=1,physics_prim_path='/World/PhysicsScene')
        self.robots=[]
        for i in range(len(cfg['robots'])):
            a=SingleArticulation(f'/World/Robots/Pixmo_{i:02d}',name=f'pixmo_{i}')
            self.world.scene.add(a);self.robots.append(a)
        self.world.reset()
        self.robot=self.robots[0];self.robot_path='/World/Robots/Pixmo_00'
        print('DOFS',self.robot.dof_names,flush=True)
        self.indices=np.array([self.robot.get_dof_index(f'J{i}') for i in range(1,7)])
        self.ik=LulaKinematicsSolver(str(ROBOT_DIR/'lula_robot_description.yaml'),str(ROBOT_DIR/'fanuc_kinematics.urdf'))
        self.suction=Suction(self.stage,self.robot_path,cfg)
        self.ticks=0;self.base_velocity=np.zeros(3);self.yaw_velocity=0.
        self.base_target=np.zeros(3)
        self.base_drives={axis:UsdPhysics.DriveAPI.Get(self.stage.GetPrimAtPath(self.robot_path+'/PlanarConstraint'),axis)
                          for axis in ['transX','transY','rotZ']}
        self.checks=[];self.trajectory=[];self.transfers=[]
        self.max_joint_limit_violation=0.;self.finite_state=True;self.max_box_speed=0.
        self.viewer=None
        self.objects=json.loads((ENV_DIR/'objects.json').read_text())
        for b in self.objects:b['path']=b['path'].replace('/World/','/World/Environment/',1)
        self.initial_boxes={b['path']:pose(self.stage,b['path'])[0].copy() for b in self.objects}
        self.initial_base=pose(self.stage,self.robot_path+'/Base')[0].copy()
        self.target_q=self.robot.get_joint_positions()[self.indices].copy()
        self.previous_boxes={p:v.copy() for p,v in self.initial_boxes.items()}
        self.limits=np.array([[math.radians(getattr(UsdPhysics.RevoluteJoint.Get(self.stage,
            self.robot_path+f'/Arm/joints/J{i}'),attr)().Get()) for attr in ['GetLowerLimitAttr','GetUpperLimitAttr']]
            for i in range(1,7)])
        self.initial_pallets={p['name']:pose(self.stage,'/World/Environment/Pallets/'+p['name'])[0] for p in cfg['pallets']}

    def check(self,name,passed,**metrics):
        record=dict(name=name,passed=bool(passed),**metrics)
        self.checks.append(record);print('CHECK',json.dumps(record),flush=True)
        return bool(passed)

    def on_contacts(self,headers,data):
        from pxr import PhysicsSchemaTools
        for h in headers:
            if not h.num_contact_data:continue
            a=str(PhysicsSchemaTools.intToSdfPath(h.actor0));b=str(PhysicsSchemaTools.intToSdfPath(h.actor1))
            self.contact_count+=1
            if a.startswith('/World/Robots/') and b.startswith('/World/Robots/'):
                self.self_contact_count+=1
                pair=' | '.join(sorted([a,b]))
                self.contact_pairs[pair]=self.contact_pairs.get(pair,0)+1
            for c in data[h.contact_data_offset:h.contact_data_offset+h.num_contact_data]:
                self.max_penetration=max(self.max_penetration,-c.separation)
                if -c.separation>.001:
                    pair=' | '.join(sorted([a,b]))
                    self.penetration_pairs[pair]=max(self.penetration_pairs.get(pair,0.),-c.separation)
                self.recent_penetration.append((getattr(self,'ticks',0),max(0.,-c.separation)))
        if len(self.recent_penetration)>10000:
            tick=getattr(self,'ticks',0)
            self.recent_penetration=[p for p in self.recent_penetration if p[0]>tick-480]

    def step(self,n=1):
        for _ in range(n):
            while not self.world.is_playing() and self.app.is_running():
                self.world.render()
                time.sleep(.01)
            if not self.app.is_running():return
            # A velocity command is integrated into a force-driven planar servo.
            # This also braces the base against arm reaction forces at zero velocity.
            yaw=math.radians(self.cfg['robots'][0]['yaw_deg'])
            local_v=np.array([math.cos(yaw)*self.base_velocity[0]+math.sin(yaw)*self.base_velocity[1],
                              -math.sin(yaw)*self.base_velocity[0]+math.cos(yaw)*self.base_velocity[1]])
            self.base_target[:2]+=local_v*self.cfg['physics_dt']
            self.base_target[2]+=self.yaw_velocity*self.cfg['physics_dt']
            for axis,value in zip(['transX','transY','rotZ'],
                                  [*self.base_target[:2],math.degrees(self.base_target[2])]):
                self.base_drives[axis].GetTargetPositionAttr().Set(float(value))
            self.world.step(render=False)
            if self.ticks%4==0:
                from .builder import hose_points
                for i in range(len(self.robots)):
                    root=f'/World/Robots/Pixmo_{i:02d}'
                    hose=UsdGeom.BasisCurves.Get(self.stage,root+'/ServiceHose')
                    if hose:hose.GetPointsAttr().Set(hose_points(self.stage,root))
                self.world.render()
                if self.viewer:self.viewer.update()
            if self.ticks%24==0:
                q=self.robot.get_joint_positions()[self.indices]
                self.finite_state=self.finite_state and bool(np.all(np.isfinite(q)))
                self.max_joint_limit_violation=max(self.max_joint_limit_violation,
                    float(np.max(np.maximum(self.limits[:,0]-q,q-self.limits[:,1]))))
                self.trajectory.append({'time_s':self.ticks*self.cfg['physics_dt'],
                    'joints_rad':self.robot.get_joint_positions()[self.indices].tolist(),
                    'base':pose(self.stage,self.robot_path+'/Base')[0].tolist(),
                    'tcp':pose(self.stage,self.suction.tcp)[0].tolist(),
                    'held_box':self.suction.attached})
            if self.ticks%120==0:
                for b in self.objects:
                    p=pose(self.stage,b['path'])[0]
                    self.finite_state=self.finite_state and bool(np.all(np.isfinite(p)))
                    self.max_box_speed=max(self.max_box_speed,float(np.linalg.norm(p-self.previous_boxes[b['path']])/(120*self.cfg['physics_dt'])))
                    self.previous_boxes[b['path']]=p
            self.ticks+=1

    def sync_ik_base(self):
        pos,q=pose(self.stage,self.robot_path+'/Arm/base_link')
        self.ik.set_robot_base_pose(pos,q)

    def solve(self,target,warm=None):
        self.sync_ik_base()
        warm=self.target_q if warm is None else warm
        active=[b for b in self.objects if b['path']!=self.suction.attached]
        self.clearance_centers=np.array([pose(self.stage,b['path'])[0] for b in active])
        self.clearance_halves=np.array([np.array(b['size'])/2 for b in active])
        seeds=[warm]
        # Lula IK has multiple branches. Reject solutions whose arm crosses a
        # carton; a converged end-effector pose alone is not collision avoidance.
        for yaw in [math.atan2(target[1],target[0]-.22),math.atan2(target[1],target[0]-.22)-math.pi]:
            for shoulder,elbow in [(.4,1.8),(-.4,-1.8),(1.1,1.8),(-1.1,-1.8)]:
                seeds.append(np.array([yaw,shoulder,elbow,0,1.5,0]))
        candidates=[]
        for seed in seeds:
            q,success=self.ik.compute_inverse_kinematics('suction_tcp',np.array(target,dtype=float),
                np.array([math.sqrt(.5),0,math.sqrt(.5),0]),warm_start=seed,
                position_tolerance=.0008,orientation_tolerance=.003)
            if success and self.arm_clear(q):
                candidates.append(q)
                if np.linalg.norm(q-warm)<.4:return q
        if not candidates:raise RuntimeError(f'No collision-free IK solution for suction pose {target}')
        return min(candidates,key=lambda q:float(np.linalg.norm(q-warm)))

    def arm_clear(self,q):
        points=[self.ik.compute_forward_kinematics(name,q)[0] for name in ['J2_link','J3_link','J5_link','J6_link']]
        for a,b,r in [(points[0],points[1],.11),(points[1],points[2],.095),(points[2],points[3],.065)]:
            samples=a[None,:]+(b-a)[None,:]*np.linspace(0,1,25)[:,None]
            delta=np.abs(samples[:,None,:]-self.clearance_centers[None,:,:])
            if np.any(np.all(delta<self.clearance_halves[None,:,:]+r,axis=2)):return False
        return True

    def move_joints(self,q,seconds=2.,settle=120):
        for i,value in enumerate(q):
            j=UsdPhysics.RevoluteJoint.Get(self.stage,self.robot_path+f'/Arm/joints/J{i+1}')
            if not math.radians(j.GetLowerLimitAttr().Get())<=value<=math.radians(j.GetUpperLimitAttr().Get()):
                raise ValueError(f'J{i+1} target exceeds manufacturer limits')
        start=self.robot.get_joint_positions()[self.indices].copy()
        duration=max(seconds,float(np.max(np.abs(q-start)))/.45)
        n=math.ceil(duration/self.cfg['physics_dt'])
        for i in range(n):
            a=(i+1)/n;a=a*a*(3-2*a)
            self.target_q=start+(q-start)*a
            self.command(self.target_q)
            self.step()
        self.target_q=np.array(q)
        self.command(self.target_q)
        self.step(settle)
        if settle:
            for _ in range(30):
                if np.max(np.abs(self.robot.get_joint_positions()[self.indices]-self.target_q))<.004:break
                self.step(24)

    def command(self,q):
        self.robot.apply_action(self.Action(joint_positions=np.array(q),joint_indices=self.indices))

    def move_tcp(self,target,seconds=2.,linear=False):
        if not linear:
            self.move_joints(self.solve(target),seconds)
        else:
            start=pose(self.stage,self.suction.tcp)[0]
            points=max(2,math.ceil(np.linalg.norm(np.array(target)-start)/.025))
            for i in range(points):
                p=start+(np.array(target)-start)*(i+1)/points
                self.move_joints(self.solve(p),seconds/points,settle=120 if i==points-1 else 0)
        actual=pose(self.stage,self.suction.tcp)[0]
        error=float(np.linalg.norm(actual-target))
        print('TCP',list(target),'actual',actual.tolist(),'error',error,flush=True)
        if error>.018:
            print('TRACKING_DIAGNOSTIC',self.target_q.tolist(),self.robot.get_joint_positions()[self.indices].tolist(),
                  self.contact_pairs,flush=True)
            self.capture('tracking_failure','profile')
            raise RuntimeError(f'Arm tracking error {error:.4f} m')

    def capture(self,name,camera=None):
        from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
        viewport=get_active_viewport()
        if camera:viewport.set_active_camera('/World/Cameras/'+camera)
        viewport.set_texture_resolution((1280,800))
        self.step(24)
        capture_viewport_to_file(viewport,str(self.output/(name+'.png')))
        self.step(24)
        image=self.output/(name+'.png')
        if image.exists():image.chmod(0o644)

    def cycle(self,box):
        path=box['path'];start=pose(self.stage,path)[0].copy()
        top=start+np.array([0,0,box['size'][2]/2+.003])
        # Far-row cartons are reachable, but not with the same high hover as the
        # near row. Find a reachable pre-grasp without changing robot/scene scale.
        hover=None
        for height in np.linspace(max(top[2]+.4,1.95),top[2]+.24,7):
            try:hover=self.solve([top[0],top[1],height]);break
            except RuntimeError:continue
        if hover is None:raise RuntimeError('No reachable collision-free pre-grasp for '+path)
        self.move_joints(hover,2.)
        self.move_tcp(top+[0,0,.24],1.5,linear=True)
        self.move_tcp(top,1.5,linear=True)
        if not self.transfers:
            payload=self.cfg['robot']['payload_kg']
            self.cfg['robot']['payload_kg']=box['mass']/2
            self.check('overweight_suction_rejected',not self.suction.assess(path)['valid'])
            self.cfg['robot']['payload_kg']=payload
        contact=self.suction.attach(path);self.step(60)
        relative_before=world_matrix(self.stage,path)*world_matrix(self.stage,self.suction.wrist).GetInverse()
        self.capture(f'pick_{len(self.transfers)+1:02d}','action')
        self.move_tcp(top+[0,0,.28],1.8,linear=True)
        lifted=pose(self.stage,path)[0].copy()
        self.check('box_lifted_'+box['name'],lifted[2]-start[2]>.20,lift_m=float(lifted[2]-start[2]))
        relative_after=world_matrix(self.stage,path)*world_matrix(self.stage,self.suction.wrist).GetInverse()
        joint_gap=float((relative_after.ExtractTranslation()-relative_before.ExtractTranslation()).GetLength())
        self.check('box_follows_wrist_'+box['name'],joint_gap<.003,relative_drift_m=joint_gap)
        # Lift clear of all source stacks and base before crossing to the conveyor.
        clearance=max(top[2]+.28,1.90)
        # Retract through the depalletized near-side space before lifting higher.
        # At full extension the far-row wrist cannot reach the highest hover.
        self.move_tcp([top[0],min(top[1],.75),top[2]+.28],1.5,linear=True)
        self.move_tcp([top[0],min(top[1],.75),clearance],1.5,linear=True)
        c=self.cfg['conveyor'];x=c['center'][0];y=c['center'][1]
        self.move_tcp([x,y,clearance],3.)
        release_top=np.array([x,y,c['center'][2]+box['size'][2]+.025])
        self.move_tcp(release_top+[0,0,.20],1.8,linear=True)
        self.move_tcp(release_top,1.2,linear=True)
        before=pose(self.stage,path)[0].copy()
        self.suction.release();self.step(240)
        after=pose(self.stage,path)[0].copy()
        expected_z=c['center'][2]+box['size'][2]/2
        placed=self.check('released_box_'+box['name'],abs(after[2]-expected_z)<.010 and before[2]-after[2]>.012 and
            abs(after[1]-y)<c['width']/2-box['size'][1]/2 and after[0]>before[0]+.02,
            before=before.tolist(),after=after.tolist(),expected_z=expected_z)
        if not placed:raise RuntimeError('Released box failed gravity/contact/conveyor validation')
        self.transfers.append({'box':path,'start':start.tolist(),'lift':lifted.tolist(),
                               'release':before.tolist(),'settled':after.tolist(),'contact':contact})
        self.capture(f'placed_{len(self.transfers):02d}','action')
        self.move_tcp(release_top+[0,0,.30],1.5,linear=True)
        self.move_tcp([.6,0,1.9],2.5)


def structural_validation(sim):
    s=sim.stage
    joints=[p for p in s.Traverse() if p.IsA(UsdPhysics.RevoluteJoint)]
    sim.check('six_fanuc_joints_per_robot',len(joints)==6*len(sim.cfg['robots']),count=len(joints))
    axes=[UsdPhysics.RevoluteJoint.Get(s,sim.robot_path+f'/Arm/joints/J{i}').GetAxisAttr().Get() for i in range(1,7)]
    sim.check('official_joint_axes',axes==['Z','Y','Y','X','Y','X'],axes=axes)
    sim.check('articulation_root',s.GetPrimAtPath(sim.robot_path).HasAPI(UsdPhysics.ArticulationRootAPI))
    sim.check('six_runtime_dofs',len(sim.robot.dof_names)==6,names=sim.robot.dof_names)
    box_ok=True
    for b in sim.objects:
        p=s.GetPrimAtPath(b['path'])
        box_ok=box_ok and p.HasAPI(UsdPhysics.RigidBodyAPI) and UsdPhysics.MassAPI(p).GetMassAttr().Get()>0
        box_ok=box_ok and s.GetPrimAtPath(b['path']+'/Carton').HasAPI(UsdPhysics.CollisionAPI)
        box_ok=box_ok and bool(p.GetRelationship('material:binding:physics').GetTargets())
    sim.check('independent_boxes_mass_collision_friction',box_ok,count=len(sim.objects))
    tool=s.GetPrimAtPath(sim.robot_path+'/Tool')
    joint=UsdPhysics.FixedJoint.Get(s,sim.robot_path+'/WristToolJoint')
    sim.check('separate_massed_gripper_on_wrist',tool.HasAPI(UsdPhysics.RigidBodyAPI) and
        joint.GetBody0Rel().GetTargets()==[Sdf.Path(sim.robot_path+'/Arm/J6_link')] and
        joint.GetBody1Rel().GetTargets()==[tool.GetPath()],mass_kg=UsdPhysics.MassAPI(tool).GetMassAttr().Get())
    from .builder import FANUC_FILE
    official=Usd.Stage.Open(str(FANUC_FILE))
    preserved=True
    for i in range(1,7):
        a=s.GetPrimAtPath(sim.robot_path+f'/Arm/joints/J{i}')
        b=official.GetPrimAtPath(f'/crx30ia/joints/J{i}')
        for attr in ['axis','localPos0','localPos1','localRot0','localRot1','lowerLimit','upperLimit']:
            preserved=preserved and a.GetAttribute('physics:'+attr).Get()==b.GetAttribute('physics:'+attr).Get()
    sim.check('official_joint_frames_and_limits_preserved',preserved)
    from pxr import UsdUtils
    layers,assets,missing=UsdUtils.ComputeAllDependencies(str(ENV_DIR/'pixmo_depalletizing.usd'))
    sim.check('asset_dependencies_resolve',not missing,missing=[str(m) for m in missing],layers=len(layers))


def run(app,args,cfg,scene):
    import omni.usd
    assert omni.usd.get_context().open_stage(str(scene))
    for _ in range(30):app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0:app.update()
    sim=Simulation(app,cfg,args.output)
    completed=False
    error=None
    def persist():
        report={'passed':completed and error is None and bool(sim.checks) and all(c['passed'] for c in sim.checks),
                'completed':completed,'error':error,
                'validation_scope':'three_box_task' if args.validate else 'scene_and_render',
                'checks':sim.checks,'transfers':sim.transfers,'suction_events':sim.suction.events,
                'physics_steps':sim.ticks,'physics_dt':cfg['physics_dt'],'scene':str(scene)}
        report['contact_statistics']={'reports':sim.contact_count,'self_contact_reports':sim.self_contact_count,
                                      'pairs':sim.contact_pairs,'max_penetration_m':sim.max_penetration,
                                      'penetration_pairs':sim.penetration_pairs}
        (args.output/'validation.json').write_text(json.dumps(report,indent=2))
        (args.output/'trajectory.json').write_text(json.dumps(sim.trajectory,indent=2))
        return report
    try:
        structural_validation(sim)
        sim.step(480)
        settled={b['path']:pose(sim.stage,b['path'])[0] for b in sim.objects}
        drift=max(float(np.linalg.norm(settled[p][:2]-start[:2])) for p,start in sim.initial_boxes.items())
        sim.check('stacks_settle_stably',drift<.015 and all(v[2]>.14 for v in settled.values()),
                  max_horizontal_drift_m=drift,box_count=len(settled))
        max_height_error=max(abs(settled[p][2]-(start[2]-.001)) for p,start in sim.initial_boxes.items())
        sim.check('boxes_rest_on_pallets_without_levitation',max_height_error<.003,max_height_error_m=float(max_height_error))
        sim.check('initial_no_self_collision',sim.self_contact_count==0,contact_pairs=dict(sim.contact_pairs))
        sim.check('out_of_reach_suction_rejected',not sim.suction.assess(sim.objects[0]['path'])['valid'])
        sim.move_tcp([.6,0,1.9],3.)
        for camera in cfg['cameras']:sim.capture(camera,camera)
        source=[b for b in sim.objects if b['pallet']=='Source']
        source.sort(key=lambda b:(-b['layer'],b['position'][1],b['position'][0]))
        if args.validate:
            for b in source[:args.cycles]:sim.cycle(b)
            base=pose(sim.stage,sim.robot_path+'/Base')[0]
            sim.check('base_stationary_during_arm_motion',np.linalg.norm(base-sim.initial_base)<.005,
                      drift_m=float(np.linalg.norm(base-sim.initial_base)))
            before=pose(sim.stage,sim.robot_path+'/Base')
            for velocity,yaw in [(np.array([.06,0,0]),0),(np.array([0,.06,0]),0),(np.zeros(3),.08)]:
                sim.base_velocity=velocity;sim.yaw_velocity=yaw;sim.step(120)
            sim.base_velocity=np.zeros(3);sim.yaw_velocity=0;sim.step(120)
            after=pose(sim.stage,sim.robot_path+'/Base')
            sim.check('planar_x_y_yaw_drive',after[0][0]>before[0][0]+.02 and after[0][1]>before[0][1]+.02
                      and np.linalg.norm(after[1]-before[1])>.01,before=[v.tolist() for v in before],after=[v.tolist() for v in after])
            sim.check('three_successful_transfers',len(sim.transfers)>=3,count=len(sim.transfers))
            pallet_drift=max(np.linalg.norm(pose(sim.stage,'/World/Environment/Pallets/'+name)[0]-initial)
                             for name,initial in sim.initial_pallets.items())
            sim.check('pallets_remain_stationary',pallet_drift<1e-6,max_drift_m=float(pallet_drift))
            sim.check('joint_limits_respected',sim.max_joint_limit_violation<.003,
                      max_violation_rad=sim.max_joint_limit_violation)
            sim.check('finite_stable_physics',sim.finite_state and sim.max_box_speed<10,
                      max_box_speed_m_s=sim.max_box_speed)
            sim.check('contacts_observed_no_deep_interpenetration',sim.contact_count>0 and sim.max_penetration<.005,
                      contact_reports=sim.contact_count,max_penetration_m=sim.max_penetration)
        completed=True
        report=persist()
        if not report['passed']:raise RuntimeError('Pixmo validation failed')
        print('PIXMO_READY',flush=True)
        if args.keep_open or not (args.validate or args.render_only):
            from .viewer import Viewer
            sim.viewer=Viewer(sim)
            while app.is_running():sim.step(4)
    except Exception as exc:
        error=str(exc)
        raise
    finally:
        report=persist()
        print('PIXMO_REPORT',json.dumps(report),flush=True)
    if not report['passed']:raise RuntimeError('Pixmo validation failed')
