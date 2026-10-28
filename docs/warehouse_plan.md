# Task: Recreate Anyware Robotics' Pixmo Depalletizing Demo in Isaac Sim

## Objective

Recreate the robot, physical environment, and depalletizing scene shown in:

https://anyware-robotics.wistia.com/s/3rxu71f7qd5fn8f

Deliver a complete, reusable, physics-enabled Isaac Sim environment that visually resembles the reference and supports robot manipulation, navigation, and depalletizing.

**Scope:** Environment and robot creation only. The repository, Isaac Sim installation, and general project infrastructure already exist. Inspect and reuse them. Do not create a new repository, install Isaac Sim, or rebuild unrelated infrastructure.

The final deliverable must include:

1. A visually faithful model of the Pixmo mobile manipulator.
2. A physically articulated FANUC arm built from public official assets.
3. A custom modeled mobile base and suction gripper.
4. A recreated depalletizing environment based on the footage.
5. Physics-enabled pallets and individual cardboard boxes.
6. A reusable scene-building and configuration interface.
7. A minimal scripted demonstration showing a box being picked and transferred.
8. A saved USD stage that opens correctly in Isaac Sim.
9. Screenshots and validation results.

Prioritize physical correctness, asset reuse, and visual fidelity over superficial decoration.

---

## Phase 0 — Analyze the reference video

Reference title: **Pixmo Mobile Depalletizing**.

Before constructing the environment, attempt to inspect the actual footage.

1. Try retrieving the video using Wistia's publicly accessible embed metadata/player.
2. Identify accessible video media and extract representative frames.
3. Sample important moments: initial establishing shot, robot close-ups, arm movement, box pickup, box transfer, and final placement.
4. Save selected frames locally under a reference directory.
5. Build a scene specification from observed geometry.

Identify:

- Robot location, orientation, appearance, and dimensions.
- Number and relative positions of pallets.
- Stacking patterns and approximate box dimensions.
- Warehouse floor, walls, columns, shelves, loading equipment, and any conveyors actually present.
- The source pallet and destination area.
- Lighting and camera positions.
- Robot motion sequence and relevant obstacles.

Estimate geometry from known object sizes, including standard pallet dimensions and published FANUC arm geometry. Use multiple reference images to reduce perspective errors.

**Do not invent scene-specific details when the video cannot be accessed.** Use clearly labeled approximate dimensions and public images as fallback references.

Create `reference_scene_spec.md` including:

- Observed features.
- Measurements and estimates.
- Source references.
- Confidence for each estimated dimension.
- Assumptions requiring later visual verification.

Public supplementary references:

- https://anyware-robotics.com/solution/
- https://anyware-robotics.com/
- https://spectrum.ieee.org/anyware-robotics-pixmo
- https://www.linkedin.com/posts/anyware-robotics_warehouseautomation-logistics-activity-7198745675843473409-11lU

The footage remains the primary reference when available.

---

## Phase 1 — Find and reuse existing robot assets

**Do not model a robot component before searching for an appropriate public asset.**

### 1.1 FANUC manipulator

Pixmo has been shown using the FANUC CRX-25iA collaborative arm.

FANUC officially recommends its CRX-30iA robot description for CRX-25iA deployments.

Start with:

https://huggingface.co/datasets/FANUC-CORPORATION/SimReady-Assets

Look for:

`crx30ia/`

This is the preferred source because it contains official simulation-ready OpenUSD assets, including physics variants.

Fallback:

https://github.com/FANUC-CORPORATION/fanuc_description

Use the `fanuc_crx_description` package and `crx30ia` description.

Official model mapping:

https://fanuc-corporation.github.io/fanuc_driver_doc/main/docs/environment/supported_models.html

Also inspect the robot assets already available in the installed Isaac Sim version.

Selection priority:

1. Official FANUC CRX-30iA SimReady USD.
2. Official FANUC CRX-30iA URDF and meshes, imported to USD.
3. Other appropriately licensed, geometrically accurate CRX-25iA/30iA assets.
4. A custom recreation of the arm only as a last resort.

Preserve the original robot geometry, kinematic structure, joint axes, and limits.

Check the actual pose and link proportions against Pixmo reference images.

### 1.2 Mobile base

Search for a downloadable Pixmo mobile base CAD, URDF, STEP, STL, or USD model.

Possible sources:

- Anyware Robotics' website and public repositories.
- Manufacturer-provided assets, if the underlying base can be identified.
- Public CAD libraries.
- Isaac Sim asset libraries.

If no accurate model exists, build a custom approximation from geometric primitives and meshes.

Reference characteristics:

- Dark-blue, industrial, enclosed rectangular base.
- Approximately pallet-sized footprint.
- Omnidirectional movement.
- Flat upper mounting platform.
- White robotic arm mounted toward one end of the base.
- Recessed lower wheel/drive system.
- Emergency-stop buttons, access panels, lights, and sensor housings.
- Anyware/Pixmo appearance.

Use a parameterized model instead of a single monolithic mesh.

The mobile base should have separate visual and collision geometry.

Implement an operational planar holonomic base model. A velocity-controlled planar representation is acceptable for the initial scene; actual wheel geometry and dynamics are a later fidelity improvement unless public specifications are found.

Do not claim the real robot uses mecanum wheels or a particular steering mechanism without evidence.

### 1.3 End effector

Recreate Pixmo's vacuum gripper.

It appears to use a rectangular suction array with multiple green suction cups.

Search for existing vacuum-gripper CAD assets and reuse suitable components if possible.

Otherwise model:

- Wrist adapter/flange.
- Vacuum manifold.
- Rectangular suction array.
- Individual suction cup geometry.
- Flexible tube routing.
- Vacuum contact plane.

Build a physically usable box-attachment mechanism.

For the first version, use a validated attach/detach mechanism compatible with Isaac Sim physics, such as a dynamically managed fixed joint.

Keep the suction cups as visible contact geometry and expose an interface for replacing the attachment approximation with per-cup contact and pressure simulation later.

Attachment must require a valid contact/reach condition and must respect a configurable payload limit.

### Deliverable

`pixmo.usd` containing the assembled arm, base, and gripper.

The robot must be properly articulated, with individually controllable arm joints and a movable planar base.

Document component provenance, original licenses, and approximations.

---

## Phase 2 — Build the depalletizing environment

Recreate the scene visible in the Wistia footage.

Use a world coordinate system with meters and Z-up. Define a consistent reference frame and document all coordinates.

### 2.1 Warehouse

Create the visible portion of the industrial warehouse.

Depending on the footage, this may include:

- Concrete industrial floor.
- Pallet staging areas.
- Structural columns.
- Warehouse walls.
- Industrial lights.
- Background storage.
- Safety markings.
- Warehouse equipment.

Use existing Isaac Sim warehouse assets when appropriate and when licenses permit.

Only model geometry necessary for visual matching, collision, and robot operation.

The room should be sized using the reference footage, with enough navigable space for the mobile base.

### 2.2 Pallets

First search Isaac Sim's asset collections for reusable pallets.

Prefer accurate wooden pallet meshes with usable collision geometry.

Use a standard pallet size only as a starting point if measurements are unavailable.

For example, 1.2192 m × 1.016 m for a standard 48 × 40-inch pallet.

Build:

- Source pallet.
- Destination pallet or drop surface, as appropriate.
- Pallet collision geometry.
- Configurable pallet placement.

### 2.3 Cardboard boxes

Build individual physics-enabled cardboard boxes.

Required properties:

- Configurable dimensions.
- Configurable masses.
- Realistic visual materials.
- Collision geometry.
- Contact friction.
- Gravity.
- Stable stacking behavior.

Model several visually distinct cardboard textures if the video shows multiple SKUs.

Include seams, tape, labels, and printed markings where useful for visual fidelity.

Use box collision cuboids with visual detail separated from collision.

Implement parameterized pallet arrangements:

- Regular grid stacking.
- Brick/bond stacking.
- Mixed-size boxes.
- Irregular stacks.
- Small pose perturbations.
- Partially depalletized stacks.

The default arrangement must match the reference video as closely as possible.

Avoid relying on rigidly grouped stacks: boxes must be independent physics objects.

### 2.4 Placement zones

Identify the target destination from the reference footage.

If a conveyor is present, create a functioning conveyor using existing simulation components or a suitable velocity-based physics implementation.

If the task transfers boxes to another pallet, model that pallet and its stacking area instead.

Do not add a conveyor solely because other Pixmo demos use one.

### Deliverable

`depalletizing_environment.usd`

This must be usable independently of the robot asset.

---

## Phase 3 — Assemble the complete Pixmo scene

Create:

`pixmo_depalletizing.usd`

Use USD composition/references to assemble:

- Warehouse environment.
- Pixmo robot.
- Pallets.
- Boxes.
- Destination equipment.
- Lighting.
- Cameras.

Maintain separate asset layers where possible so individual components can be replaced without rebuilding the entire environment.

Position the robot relative to the source pallet according to the footage.

Ensure the entire manipulation area lies within the robot's actual reachable workspace.

Verify the physical arm's mounting height and position rather than adjusting the scene to conceal an incorrect robot model.

Configure:

- Physics scene.
- Gravity.
- Collision filtering.
- Contact properties.
- Articulation drives.
- Joint limits.
- Mass and inertia.
- Solver settings as needed for stable stacking.

Avoid excessive contact approximation that permits boxes to interpenetrate or levitate.

---

## Phase 4 — Implement a functional depalletizing demonstration

We do not need to reproduce Anyware's proprietary motion-planning or perception system.

Implement a minimal deterministic sequence to verify the constructed environment and robot.

Required sequence:

1. Initialize the scene.
2. Locate a known box in the source stack.
3. Compute a reachable top-face suction grasp.
4. Move the FANUC arm to a pre-grasp pose.
5. Approach the box.
6. Activate suction attachment.
7. Lift the box.
8. Transfer it to the destination.
9. Lower and release.
10. Return to a safe pose.
11. Repeat for several boxes.

Use existing Isaac Sim IK and motion-generation capabilities where available.

A scripted controller or supported motion-planning library is sufficient.

The arm must be moved through joint commands rather than directly teleporting its end effector.

The box must participate in physics after release.

A kinematic attachment approximation is acceptable only while the box is grasped, with documented limitations.

Do not teleport boxes from pallet to destination to fake successful manipulation.

Support a simple scripted movement of the mobile base as a separate demonstration of omnidirectional positioning.

The minimum demonstration should include at least three successful box transfers.

---

## Phase 5 — Visual fidelity

Compare rendered screenshots to the reference footage.

Include several matching camera perspectives:

- Wide establishing shot.
- Robot profile.
- Gripper close-up.
- Source-pallet view.
- Task-action perspective.

Match, to the extent possible:

- Base dimensions and proportions.
- Arm geometry and mounting.
- Gripper scale.
- Pallet spacing.
- Box stack height and pattern.
- Material colors.
- Lighting.
- Camera framing.

Use PBR materials for important visible surfaces.

Keep collision meshes reasonably simple, even when using higher-detail visual meshes.

Generate a contact sheet comparing reference frames and simulator screenshots if the source video can be downloaded.

If not, create a contact sheet against the available official Pixmo photographs.

Keep the render camera configuration separate from physical robot sensors.

---

## Phase 6 — Parameterization and reproducibility

Implement an environment configuration that supports changing:

- Number of robots.
- Robot initial poses.
- Number and arrangement of pallets.
- Number of boxes.
- Box dimensions and masses.
- Pallet stack patterns.
- Source and destination locations.
- Lighting.
- Camera positions.
- Random seed.

The default configuration must faithfully reproduce the reference layout.

Provide optional randomized layouts for future robot-learning experiments without changing the reference configuration.

Support multiple instances of Pixmo by referencing the same robot USD asset under distinct prim paths.

Do not build a reinforcement-learning training framework as part of this task.

However, expose semantic prim names and basic scene-object access so the environment can be integrated into Isaac Lab later.

---

## Phase 7 — Validation

Perform both structural and physical validation.

### Robot validation

- Correct number of FANUC arm joints.
- Valid articulation root.
- Joint limits respected.
- Correct joint axes.
- Reachable grasp poses.
- Gripper properly attached to wrist.
- No self-collision in the initial configuration.
- Mobile base can move in X, Y, and yaw.
- Arm can move while the base remains stationary.

### Physics validation

- Boxes settle onto pallets.
- No persistent interpenetration.
- No unstable stacks under normal simulation conditions.
- Pallets remain stationary.
- A grasped box moves with the end effector.
- Released boxes respond to gravity and contacts.
- No unexpected simulation explosions or large numerical instabilities.

### Task validation

- At least three successful grasp-and-place cycles.
- Boxes begin and end in physically valid locations.
- Controller handles a reachable box without manual intervention.

### Asset validation

- Saved USD can be reopened.
- No missing asset references.
- No unexpected external runtime dependencies.
- Asset license information preserved.
- Scene builder produces consistent geometry from the same configuration.

### Visual validation

- Render multiple camera views.
- Compare against reference footage where available.
- Document remaining differences.

---

## Suggested project structure

Adapt the paths to the existing repository conventions.

```text
assets/
  robots/
    pixmo/
      pixmo.usd
      mobile_base.usd
      vacuum_gripper.usd
      fanuc_crx30ia.usd
  environments/
    pixmo_depalletizing/
      warehouse.usd
      depalletizing_environment.usd
      pixmo_depalletizing.usd
  objects/
    pallets/
    cardboard_boxes/
  materials/

configs/
  pixmo_robot.yaml
  depalletizing_scene.yaml

scripts/
  build_pixmo_robot.py
  build_depalletizing_scene.py
  demo_depalletizing.py
  validate_scene.py
  render_reference_views.py

references/
  reference_scene_spec.md
  asset_sources.md
  screenshots/

docs/
  pixmo_environment.md
```

Do not unnecessarily restructure the repository.

---

## Acceptance criteria

The task is complete when:

1. The scene opens in the existing Isaac Sim installation.
2. The robot looks recognizably like Pixmo.
3. The arm uses a real, accurate FANUC articulation from an official/public asset.
4. The robot base and gripper are represented as separate reusable components.
5. The warehouse and depalletizing arrangement visually match the reference as closely as available evidence permits.
6. All boxes and pallets have valid physics.
7. The robot can pick and transfer multiple boxes.
8. The entire scene can be generated and configured programmatically.
9. The scene is saved as reusable USD assets.
10. Validation screenshots and results are produced.

## Execution instructions

Work through the phases in order.

First inspect the existing repository and current Isaac Sim version, then perform asset discovery.

Implement the scene directly rather than stopping after writing design documentation.

Prefer public, manufacturer-verified robot geometry over handmade approximations.

Do not recreate components with suitable public assets.

Prioritize, in order:

1. Correct articulated robot and asset reuse.
2. Correct environment geometry.
3. Stable box/pallet physics.
4. Functional manipulation.
5. Visual polish.

Where the source video or vendor specifications are inaccessible, document the limitation and proceed using the best substantiated approximation.

**Final objective: a working, reusable Pixmo-style depalletizing environment in Isaac Sim, not just a rendered imitation of a warehouse.**
