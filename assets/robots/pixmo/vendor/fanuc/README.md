---
license: apache-2.0
---

# FANUC SimReady Assets

SimReady-packaged OpenUSD assets of FANUC industrial robots,
contributed by FANUC CORPORATION to the NVIDIA SimReady Central catalog.
Robot series are added to this dataset over time.

- **Owner / namespace:** FANUC-CORPORATION
- **Dataset:** FANUC-CORPORATION/SimReady-Assets
- **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)
- **Validation profile:** Robot-Body
- **Discovery (after NVIDIA review + merge + indexing):** Isaac Sim Content Browser, the simready-search pip package, and the SimReady search API.

## Assets

| Asset folder | Package name | Description |
|---|---|---|
| `crx3ia/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx3ia` | FANUC Robot CRX-3iA (CRX/3-7A) |
| `crx5ia/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx5ia` | FANUC Robot CRX-5iA (CRX/5-10A) |
| `crx10ia/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx10ia` | FANUC Robot CRX-10iA (CRX/10-12A) |
| `crx10ia_l/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx10ia_l` | FANUC Robot CRX-10iA/L (CRX/10-14A) |
| `crx10ia_lp/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx10ia_lp` | FANUC Robot CRX-10iA/L Paint |
| `crx20ia_l/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx20ia_l` | FANUC Robot CRX-20iA/L (CRX/20-14A) |
| `crx30ia/` | `simready.hf.FANUC-CORPORATION.SimReady-Assets.crx30ia` | FANUC Robot CRX-30iA (CRX/30-18A) |

## Physics variants

All assets share the same physics setup.
Both physics variant sets on the root prim default to `Disabled`, so the robot loads without physics:

| Variant set | Default | Other choice |
|---|---|---|
| PhysX | Disabled | Enabled |
| Newton | Disabled | Enabled |

To simulate the robot, select `PhysX: Enabled` (or `Newton: Enabled`).
Enable only one physics variant at a time.

## Package contents

### crx3ia

```text
crx3ia/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx3ia.usd.png
│   │   └── 256x256/
│   │       └── crx3ia.usd.png
│   ├── configuration/
│   │   ├── crx3ia_base.usd
│   │   ├── crx3ia_meshes.usd
│   │   ├── crx3ia_physics.usd
│   │   ├── crx3ia_robot.usd
│   │   └── crx3ia_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx3ia.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx3ia`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx3ia`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx3ia`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx3ia`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx5ia

```text
crx5ia/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx5ia.usd.png
│   │   └── 256x256/
│   │       └── crx5ia.usd.png
│   ├── configuration/
│   │   ├── crx5ia_base.usd
│   │   ├── crx5ia_meshes.usd
│   │   ├── crx5ia_physics.usd
│   │   ├── crx5ia_robot.usd
│   │   └── crx5ia_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx5ia.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx5ia`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx5ia`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx5ia`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx5ia`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx10ia

```text
crx10ia/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx10ia.usd.png
│   │   └── 256x256/
│   │       └── crx10ia.usd.png
│   ├── configuration/
│   │   ├── crx10ia_base.usd
│   │   ├── crx10ia_meshes.usd
│   │   ├── crx10ia_physics.usd
│   │   ├── crx10ia_robot.usd
│   │   └── crx10ia_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx10ia.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx10ia`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx10ia`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx10ia`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx10ia`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx10ia_l

```text
crx10ia_l/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx10ia_l.usd.png
│   │   └── 256x256/
│   │       └── crx10ia_l.usd.png
│   ├── configuration/
│   │   ├── crx10ia_l_base.usd
│   │   ├── crx10ia_l_meshes.usd
│   │   ├── crx10ia_l_physics.usd
│   │   ├── crx10ia_l_robot.usd
│   │   └── crx10ia_l_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx10ia_l.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx10ia_l`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx10ia_l`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx10ia_l`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx10ia_l`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx10ia_lp

```text
crx10ia_lp/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx10ia_lp.usd.png
│   │   └── 256x256/
│   │       └── crx10ia_lp.usd.png
│   ├── configuration/
│   │   ├── crx10ia_lp_base.usd
│   │   ├── crx10ia_lp_meshes.usd
│   │   ├── crx10ia_lp_physics.usd
│   │   ├── crx10ia_lp_robot.usd
│   │   └── crx10ia_lp_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx10ia_lp.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx10ia_lp`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx10ia_lp`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx10ia_lp`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx10ia_lp`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx20ia_l

```text
crx20ia_l/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx20ia_l.usd.png
│   │   └── 256x256/
│   │       └── crx20ia_l.usd.png
│   ├── configuration/
│   │   ├── crx20ia_l_base.usd
│   │   ├── crx20ia_l_meshes.usd
│   │   ├── crx20ia_l_physics.usd
│   │   ├── crx20ia_l_robot.usd
│   │   └── crx20ia_l_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx20ia_l.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx20ia_l`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx20ia_l`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx20ia_l`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx20ia_l`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

### crx30ia

```text
crx30ia/
├── .metadata/
├── simready_usd/
│   ├── .thumbs/
│   │   ├── 1024x1024/
│   │   │   └── crx30ia.usd.png
│   │   └── 256x256/
│   │       └── crx30ia.usd.png
│   ├── configuration/
│   │   ├── crx30ia_base.usd
│   │   ├── crx30ia_meshes.usd
│   │   ├── crx30ia_physics.usd
│   │   ├── crx30ia_robot.usd
│   │   └── crx30ia_sensor.usd
│   ├── licenses/
│   │   ├── LICENSE.txt
│   │   └── THIRD_PARTY_NOTICES.txt
│   ├── materials/
│   │   └── mdl/
│   │       ├── nvidia/
│   │       │   ├── aux_definitions.mdl
│   │       │   ├── core_definitions.mdl
│   │       │   └── support_definitions.mdl
│   │       ├── OmniPBR.mdl
│   │       ├── OmniPBRBase.mdl
│   │       └── OmniPBR_ClearCoat.mdl
│   ├── runnables/
│   │   └── physics/
│   │       ├── newton.usd
│   │       └── physx.usd
│   └── crx30ia.usd
└── com.nvidia.simready.packaging.json
```

- **Sensor variant set** on the root prim `crx30ia`; default selection `Sensors` (also None).
- **Robot variant set** on the root prim `crx30ia`; default selection `Robot` (also None).
- **PhysX variant set** on the root prim `crx30ia`; default selection `Disabled` (also Enabled).
- **Newton variant set** on the root prim `crx30ia`; default selection `Disabled` (also Enabled).
- **Materials:** UsdPreviewSurface on every material, with NVIDIA MDL materials included for Omniverse RTX.
- **References:** all relative (`@./...@`); no absolute or search paths.
- **Collision:** 7 rigid bodies; collision meshes use convexHull approximation.

## License

Apache-2.0. Third-party notices for bundled files are included in each package
under `simready_usd/licenses/`.
