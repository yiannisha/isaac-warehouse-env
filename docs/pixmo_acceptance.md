# Warehouse plan acceptance — 2026-10-28

The final reference scene is built under `assets/environments/pixmo_depalletizing/` and the reusable robot under `assets/robots/pixmo/`. The existing `dell-rack-sim` installation and desktop services are reused. The implementation reused the existing workspace and Isaac installation; Git tracking was added afterward at the user's request.

Selected reports and simulator renders are included in Git. Reference media, the comparison sheet, the delivery archive and historical runs remain VM-local; see [repository contents](repository.md).

## Verified evidence

- [Final task report](../artifacts/pixmo-validation015/validation.json): **29/29 checks passed**, with three distinct source cartons grasped, lifted, moved, released under gravity, and transported by conveyor contact.
- [Saved asset audit](../artifacts/pixmo-validation015/asset_audit.json): all seven authored component/scene USD files reopen; FANUC license/notices remain present; an isolated rebuild has the same composed geometry fingerprint.
- [Fresh-process reopen](../artifacts/pixmo-reopen002/validation.json): the final saved scene opens and renders in another Isaac process; all 46 independent cartons settle correctly.
- [Randomized two-robot scene](../artifacts/pixmo-multi002/validation.json): two referenced robot instances, 12 total FANUC revolute joints, and 37 independently simulated cartons. This is scene/physics validation, not a second robot task controller.
- [Native desktop controls](../artifacts/pixmo-validation015/gui-smoke.json): actual X11 camera, base velocity, pause and resume input passed, with independently observed simulation telemetry. This uses the desktop served by existing noVNC; it is not a claim of a separate Mac browser-input test.
- [Tested source comparison](../artifacts/pixmo-validation015/source_delivery.json): all 25 snapshotted Python files match the delivered workspace.
- [Delivery audit](../artifacts/pixmo-validation015/delivery_audit.json): the [USD/source bundle](../artifacts/pixmo-usd-assets.tar.gz) is extracted into an isolated directory and opens with **zero missing references and zero references outside the bundle**. The original pallet's MDL dependency is included locally; no built-in shader exception is needed.
- [Reference comparison sheet](../artifacts/pixmo-validation015/reference_comparison.jpg), [desktop capture](../artifacts/pixmo-validation015/desktop-controls.png), and five inspection views: [wide](../artifacts/pixmo-validation015/wide.png), [profile](../artifacts/pixmo-validation015/profile.png), [source](../artifacts/pixmo-validation015/source.png), [action](../artifacts/pixmo-validation015/action.png), [gripper](../artifacts/pixmo-validation015/gripper.png).

The five CPU layout tests pass, including no overlap/overhang across all patterns and seeds, deterministic reconstruction, explicit carton counts, invalid-layout rejection, and bond courses spanning the lower course's seams. They run with `sudo docker exec -w /workspace dell-rack-sim python3 -m unittest pixmo.test_layouts -v`.

## Acceptance criteria mapped to current artifacts

| Warehouse-plan requirement | Current evidence |
|---|---|
| Scene opens in existing Isaac Sim | `pixmo-reopen002/validation.json`, all five views rendered from saved USD in a fresh process |
| Recognizable Pixmo appearance | Actual video retrieved; blue chamfered base, short riser, sensor mast, original white FANUC arm, green cup array and following service hose; comparison sheet |
| Official accurate articulated arm | Pinned FANUC CRX-30iA SimReady package; exact original axes, frames and limits compared in the task report; six runtime DOFs |
| Reusable base and gripper | `mobile_base.usd`, `vacuum_gripper.usd`, assembled `pixmo.usd`; separate 3.2 kg wrist tool and 350 kg estimated chassis |
| Reference warehouse/depalletizing layout | Gray industrial warehouse crop, yellow rail, pallet line and actual roller-conveyor destination; observation/confidence specification and comparison sheet |
| Valid box and pallet physics | 46 independent positive-mass frictional cartons; compound static pallet slats; measured settling and stationary pallets |
| Multiple successful transfers | Three distinct top-layer cartons, including a far-row grasp; measured 0.28 m lifts, wrist following, gravity and 0.187 m conveyor displacement after release |
| Programmatic generation/configuration | `pixmo/builder.py`, JSON configuration, five layout patterns, bounded perturbations and count control; randomized two-instance run |
| Saved reusable USD | Seven authored layers/components plus intact original FANUC package; all dependencies resolve locally and all components reopen |
| Screenshots and validation | Final task/asset/reopen/GUI reports, sampled video frames, five camera views, pickup/placement images and reference comparison sheet |

## Physical measurements

The final task report records zero joint-limit violations, zero self-contact reports, zero pallet movement and approximately 2.6 micrometers of base drift during arm manipulation. Separate X and Y moves each travel approximately 30 mm, followed by approximately 0.04 radians of yaw. The largest reported contact penetration over 220,514 contact reports is **0.031 mm**. The independent stack-height check is within **0.512 mm** of configured supported positions. No box position or velocity is set to fake a transfer; the only carton attachment is a validated, removable physical fixed joint.

The final default includes true interlocking bond courses on the staging pallet, so its carton count is 46. Earlier development runs with a split-carton pattern had 48 and are not the final reference geometry. Failed development reports and their logs remain separate; reports 001/002 retain their original versions alongside explicit corrections to avoid treating preliminary checks as a successful task.

## Scope and remaining approximations

The arm geometry, articulation and inertia come from the official asset. Base/tool dimensions, cup count, chassis/tool masses, riser height, warehouse details and camera calibration remain substantiated approximations, with confidence and provenance in [the scene specification](../references/pixmo/reference_scene_spec.md) and [asset sources](../references/pixmo/asset_sources.md). The current manufacturer's green arm rings differ from the dark wrist/joint accents in the supplied footage; original manufacturer geometry is retained.

Suction uses geometric seal/reach checks and a payload cap followed by a fixed joint; there is no pneumatic pressure simulation. The mobile base is a force-driven planar X/Y/yaw model, without invented wheel mechanics. The riser is fixed at the modeled working height. The service hose is visual. The task uses deterministic IK waypoints and a carton-clearance screen, not Anyware perception/planning or a general collision-complete planner. The modeled conveyor has an open outlet; downstream cartons can fall onto the floor after leaving the camera crop, and those impacts are included in validation. No reinforcement learning framework is introduced.

See [the reproduction guide](pixmo_environment.md) for commands, configurations, component replacement and existing viewer access.
