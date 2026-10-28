# Pixmo depalletizing environment

This implementation follows [the warehouse plan](warehouse_plan.md) within the existing Dell rack workspace. It uses the existing `dell-rack-sim` container, installed Isaac Sim 6.0.1 release candidate, PhysX, NVIDIA Lula IK, native Isaac controls, noVNC desktop, and artifact server. No infrastructure replacement or new Isaac installation is needed.

[Acceptance results and evidence](pixmo_acceptance.md): the final reference run passes all 29 checks and three physical box transfers. The scene is left open on the existing desktop. Current artifacts are in `artifacts/pixmo-validation015/`.

## Run in the existing container

From the `dell-rack` directory on the VM:

```bash
# Build all reusable USD layers, then exit.
sudo docker exec dell-rack-sim bash /workspace/pixmo/run.sh \
  --headless --build-only --output /workspace/artifacts/pixmo-build-new

# Full physical acceptance: at least three joint-commanded transfers, base motion,
# independent component reopening and an isolated deterministic rebuild.
sudo docker exec dell-rack-sim bash /workspace/pixmo/run.sh \
  --headless --validate --check-reproducible \
  --output /workspace/artifacts/pixmo-validation-new

# Reopen the saved scene and render all five views without rebuilding.
sudo docker exec dell-rack-sim bash /workspace/pixmo/run.sh \
  --headless --reuse --render-only --output /workspace/artifacts/pixmo-reopen-new

# Interactive desktop, using the existing noVNC service. Close another GUI
# simulation before starting this one. Give every run a new output directory.
sudo docker exec -d dell-rack-sim bash -c \
  'bash /workspace/pixmo/run.sh --reuse --output /workspace/artifacts/pixmo-live-new > /workspace/artifacts/logs/pixmo-live-new.log 2>&1'
```

The output directory must be new; this prevents stale screenshots or reports from being reused as fresh evidence. Every launch preserves the Python source and input configuration before starting Isaac. The run's `source_manifest.json` identifies tested code, and `config.json` contains effective parameters. Logs must contain `PIXMO_READY`; a process launch alone is not acceptance. `validation.json` includes `completed`, `validation_scope`, errors, individually measured checks and successful transfers. Only a completed passing **three_box_task** report proves task acceptance. Render-only reports have a narrower explicit scope.

The existing Mac connection remains `bash scripts/connect.sh`. On the VM the existing services listen at `127.0.0.1:6080` (desktop) and `127.0.0.1:8080` (artifacts); the existing tunnel forwards them to `16080` and `18080`. No new public services are opened. Each live run writes `live.png` and `live-state.json` under its output directory. Those are viewable through the existing artifact server.

The native **Pixmo depalletizing controls** window exposes camera presets, a known-box pick cycle, world-frame suction target, six individual arm joint targets, X/Y/yaw base velocity controls, Stop base, suction release, Pause and Resume. All arm motion uses joint drive commands. A rejected or unreachable target appears as a control error. Base position is held by a force-limited planar servo when its commanded velocity is zero. The GUI does not implement a proprietary perception stack.

## Generated assets and implementation

| Artifact | Purpose |
|---|---|
| `assets/robots/pixmo/pixmo.usd` | Assembled mobile articulation, original six-axis FANUC arm, massed tool, planar constraint |
| `assets/robots/pixmo/mobile_base.usd` | Reusable parameterized blue chassis, fixed riser, mast, separate visual/collision geometry |
| `assets/robots/pixmo/vacuum_gripper.usd` | Massed manifold, flange, twelve green cup bellows, hoses, physical contact lips and semantic contact plane |
| `assets/robots/pixmo/vendor/fanuc/crx30ia/` | Pinned original manufacturer USD package, MDL files, metadata and licenses |
| `assets/robots/pixmo/fanuc_kinematics.urdf` | Lula-only kinematic description derived from the original USD frames |
| `assets/environments/pixmo_depalletizing/depalletizing_environment.usd` | Robot-independent warehouse, static pallets, dynamic cartons, powered conveyor and its own physics scene |
| `assets/environments/pixmo_depalletizing/pixmo_depalletizing.usd` | Complete scene with USD references, physics, lighting, render cameras and robot instances |
| `assets/environments/pixmo_depalletizing/objects.json` | Semantic object paths, pallet membership, dimensions, masses, layer and SKU |
| `configs/depalletizing_scene.json` | Reference layout and physical/visual parameters |
| `references/pixmo/reference_scene_spec.md` | Footage observations, estimated dimensions and confidence |
| `references/pixmo/asset_sources.md` | Discovery results, component provenance, licenses and approximations |

`pixmo/builder.py` supplies `build_robot`, `build_environment`, and `build_scene`. Import these only after the installed `SimulationApp` has started. `pixmo/config.py` provides deterministic layout generation independent of Isaac. `pixmo/runtime.py` supplies the reusable `Simulation` and `Suction` interfaces. `Suction.assess`, `attach`, and `release` are the replacement boundary for future per-cup pressure/contact models.

The source boxes have independent rigid bodies, cuboid colliders, positive configurable mass, friction, gravity, tape, labels and printed detail. Three deterministic cardboard textures and a concrete PBR color map are generated locally; no external image service is needed. A visual service hose follows the measured arm link poses. Pallets reuse NVIDIA's wooden visual mesh, normalized using its actual authored bounds; separate static slats preserve fork openings. The conveyor uses the installed `PhysxSurfaceVelocityAPI` on a kinematic contact surface, with visible rollers. Cartons travel through contact friction, without setting carton transforms or velocities. A released sleeping carton is explicitly awakened so gravity acts immediately.

The original arm masses/inertias remain intact. The separate 3.2 kg tool and 350 kg chassis are simulation estimates; the service hose is visual geometry, without pneumatic or cable dynamics. The 0.08 m wrist standoff prevents the wide manifold from contacting the original wrist housing, without filtering that collision away. Its total wrist-to-suction offset is 0.30 m.

To recover missing source assets and reference frames, run `sudo docker exec dell-rack-sim python3 /workspace/pixmo/fetch_assets.py`. FANUC downloads use the pinned revision documented in the manifest. This downloads assets, not Isaac Sim. The delivered local USD/texture package works without network access after these files are present.

## Configure and extend

All lengths are meters, Z is up, the conveyor/pallet line follows X, source stacks are on +Y and the conveyor is on -Y. The robot's arm mount is measured from its base ground origin. Actual arm scale and joint geometry are preserved.

Edit a copy of `configs/depalletizing_scene.json`, then pass `--config /workspace/configs/my_scene.json`. Supported parameters include robot count/poses/yaws, base size and mount, tool mass and payload limit, pallet count/positions, box dimensions/masses, stack pattern and grid, conveyor location/size/speed, warehouse size, lights, cameras and random seed. Each pallet can specify `box_count` up to its grid capacity for partial depalletization. Patterns are `grid`, `bond`, `mixed`, `irregular`, and `partial`; `perturbation_m` adds bounded positional variations. Mixed-size columns retain support rather than creating intersecting random cartons.

Multiple robot entries reference the same `pixmo.usd` at distinct `/World/Robots/Pixmo_00`, `Pixmo_01`, etc. Their relative joint/body targets remap through USD composition. Space additional robots clear of pallets and the conveyor. The deterministic task controller operates the first robot; other instances remain independently articulated and braced. Their poses and semantic access support later Isaac Lab integration; no reinforcement learning framework is included.

```bash
# Randomized scene outputs go into this run's assets/ directory, preserving the
# reference assets and reference configuration.
sudo docker exec dell-rack-sim bash /workspace/pixmo/run.sh \
  --headless --randomized --seed 29 --build-only \
  --output /workspace/artifacts/pixmo-random-new

# Optional explicit destination for generated assets.
sudo docker exec dell-rack-sim bash /workspace/pixmo/run.sh \
  --headless --config /workspace/configs/my_scene.json --build-only \
  --asset-root /workspace/assets/my_pixmo_layout \
  --output /workspace/artifacts/pixmo-custom-new
```

The default scene is an observed-layout approximation, not manufacturer CAD for the entire robot. Exact base dimensions, cup count and riser travel are not public measurements. The riser is modeled at a fixed working height. Hidden wheel mechanics are not invented; the operational X/Y/yaw servo represents omnidirectional positioning. Warehouse equipment is limited to what is visible, with estimated spacing. See the reference specification for confidence levels.

The gripper uses a contact/reach-validated dynamic fixed joint, not vacuum pressure simulation. Attachment requires all modeled cup extents to fit the top face, near-normal approach, a small configured gap tolerance and a payload within the limit. The box remains dynamic while held. Release removes the joint and wakes the box. The controller uses Lula IK, deterministic elevated waypoints and a conservative arm-versus-carton clearance screen; it is not a general-purpose collision-complete planner. Arbitrary randomized layouts may require new task waypoints or motion planning.

The finite conveyor has an open downstream end. During long runs, transferred cartons can leave it and fall onto the modeled warehouse floor; those impacts are included in physical validation. The reference conveyor continues beyond the camera crop. Extend `conveyor.length` and the modeled room as needed for a longer downstream process, or integrate the outlet with a subsequent material-handling scene.

## Validation and visual comparison

Run the inexpensive layout invariants with:

```bash
sudo docker exec -w /workspace dell-rack-sim python3 -m unittest pixmo.test_layouts -v
```

Physical validation checks original joint axes/frames/limits, six controllable joints, the articulation root, separate massed wrist tool, independent boxes, resolved asset dependencies, settling heights/drift, initial self-collision, suction reach and payload rejection, measured lift and wrist following, gravity and conveyor motion after release, stationary pallets, braced base, separate X/Y/yaw motion, numerical stability, joint limits and at least three successful placements. `--check-reproducible` separately reopens component USDs and rebuilds into a different directory, comparing composed geometry fingerprints.

Five render cameras are separate from the physical sensor mast: `wide`, `profile`, `source`, `action`, `gripper`. Per-cycle pickup and placement screenshots are also captured. Generate the footage comparison sheet after a successful task run:

```bash
sudo docker exec dell-rack-sim python3 /workspace/pixmo/compare_views.py \
  --renders /workspace/artifacts/pixmo-validation-new
```

`reference_comparison.jpg` places actual Wistia frames next to the simulator. Camera matching is approximate and explicitly labeled. The official FANUC geometry, blue chassis, green suction array, pallet line and roller conveyor should be assessed together. The reference video contains more background warehouse detail, different individual carton graphics and a more detailed custom chassis; these remain documented fidelity limits.
