"""Native Isaac controls on the existing Dell rack noVNC desktop."""
import json
import time
import shutil
import numpy as np
import omni.ui as ui
from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport
from rack_sim.camera_guard import protect_perspective
from .runtime import pose


class Viewer:
    def __init__(self,sim):
        import omni.timeline
        timeline=omni.timeline.get_timeline_interface()
        self.sim=sim;self.pending=None;self.busy=False;self.last_capture=0;self.frames=0
        self.message='Ready';self.lock=ui.SimpleBoolModel(True)
        self.window=ui.Window('Pixmo depalletizing controls',width=460,height=660)
        self.window.position_x=1110;self.window.position_y=60
        self.joints=[];self.xyz=[]
        with self.window.frame:
            with ui.VStack(spacing=5):
                self.status=ui.Label('Pixmo — starting',height=28)
                with ui.HStack(height=28):
                    for name in sim.cfg['cameras']:
                        ui.Button(name,clicked_fn=lambda n=name:get_active_viewport().set_active_camera('/World/Cameras/'+n))
                with ui.HStack(height=30):
                    ui.Button('Pick next box',clicked_fn=self.pick)
                    ui.Button('Home arm',clicked_fn=lambda:self.queue(lambda:sim.move_tcp([.6,0,1.9],3)))
                ui.Label('Arm target in world coordinates (meters)',height=22)
                for label,value in zip(['X','Y','Z'],[0,1.0,1.55]):
                    with ui.HStack(height=24):
                        ui.Label(label,width=80)
                        m=ui.SimpleFloatModel(value);self.xyz.append(m)
                        ui.FloatDrag(m,min=-2,max=3,step=.01)
                ui.Button('Move suction face to target',height=28,
                          clicked_fn=lambda:self.queue(lambda:sim.move_tcp([m.as_float for m in self.xyz],3)))
                ui.Label('Individual joint targets (degrees)',height=22)
                for i in range(6):
                    with ui.HStack(height=24):
                        ui.Label(f'J{i+1}',width=80)
                        value=float(np.degrees(sim.robot.get_joint_positions()[sim.indices[i]]))
                        model=ui.SimpleFloatModel(value);self.joints.append(model)
                        ui.FloatDrag(model,min=-270,max=270,step=.5)
                ui.Button('Move arm joints',height=28,clicked_fn=lambda:self.queue(
                    lambda:sim.move_joints(np.radians([m.as_float for m in self.joints]),3)))
                ui.Label('Base velocity — click Stop base when positioned',height=22)
                with ui.HStack(height=28):
                    for name,v in [('X+',(.08,0,0)),('X-',(-.08,0,0)),('Y+',(0,.08,0)),('Y-',(0,-.08,0))]:
                        ui.Button(name,clicked_fn=lambda velocity=v:self.drive(velocity,0))
                with ui.HStack(height=28):
                    ui.Button('Yaw +',clicked_fn=lambda:self.drive((0,0,0),.10))
                    ui.Button('Yaw -',clicked_fn=lambda:self.drive((0,0,0),-.10))
                    ui.Button('Stop base',clicked_fn=lambda:self.drive((0,0,0),0))
                with ui.HStack(height=28):
                    ui.Button('Release suction',clicked_fn=sim.suction.release)
                    # World.pause/play can update Kit recursively inside a UI
                    # callback. Match the existing rack viewer's timeline API.
                    ui.Button('Pause',clicked_fn=timeline.pause)
                    ui.Button('Resume',clicked_fn=timeline.play)
                with ui.HStack(height=24):
                    ui.CheckBox(self.lock,width=24);ui.Label('Keep 3D perspective')
                ui.Label('Live preview and results use the existing artifact server.',height=24)

    def queue(self,fn):
        if not self.busy:self.pending=fn

    def drive(self,velocity,yaw):
        if not self.busy:
            self.sim.base_velocity=np.array(velocity,dtype=float);self.sim.yaw_velocity=yaw

    def pick(self):
        done={t['box'] for t in self.sim.transfers}
        boxes=[b for b in self.sim.objects if b['pallet']=='Source' and b['path'] not in done]
        boxes.sort(key=lambda b:(-pose(self.sim.stage,b['path'])[0][2],b['position'][1],b['position'][0]))
        if boxes:self.queue(lambda:self.sim.cycle(boxes[0]))

    def update(self):
        viewport=get_active_viewport()
        presets={'/World/Cameras/'+name for name in self.sim.cfg['cameras']}
        if str(viewport.camera_path) not in presets:protect_perspective(viewport,self.lock.as_bool)
        self.status.text=f'{self.message} | transfers: {len(self.sim.transfers)} | suction: {bool(self.sim.suction.attached)}'
        if self.pending and not self.busy:
            action=self.pending;self.pending=None;self.busy=True;self.message='Moving'
            self.sim.base_velocity[:]=0;self.sim.yaw_velocity=0
            try:action();self.message='Ready'
            except Exception as exc:self.message=str(exc);print('PIXMO_CONTROL_ERROR',exc,flush=True)
            finally:self.busy=False
        if time.monotonic()-self.last_capture>1:
            capture_viewport_to_file(viewport,str(self.sim.output/f'live-{self.frames%2}.png'))
            previous=self.sim.output/f'live-{(self.frames+1)%2}.png'
            if previous.exists():
                shutil.copyfile(previous,self.sim.output/'live.png')
                (self.sim.output/'live.png').chmod(0o644)
            self.frames+=1;self.last_capture=time.monotonic()
            (self.sim.output/'live-state.json').write_text(json.dumps({
                'frame':self.frames,'sim_time_s':self.sim.ticks*self.sim.cfg['physics_dt'],
                'joints_rad':self.sim.robot.get_joint_positions()[self.sim.indices].tolist(),
                'base':pose(self.sim.stage,self.sim.robot_path+'/Base')[0].tolist(),
                'base_orientation':pose(self.sim.stage,self.sim.robot_path+'/Base')[1].tolist(),
                'active_camera':str(viewport.camera_path),
                'transfers':len(self.sim.transfers),'message':self.message}))
