# Pixmo Mobile Depalletizing — observed scene specification

Primary footage: [Anyware Wistia share](https://anyware-robotics.wistia.com/s/3rxu71f7qd5fn8f), player ID `dgqj21im6b`, title **Pixmo Mobile Depalletizing**. The actual video was retrieved on 2026-10-27 through its public player metadata at `https://fast.wistia.com/embed/medias/dgqj21im6b.json`. Downloaded 960-pixel MP4 and original metadata are retained here. This is a footage-based reconstruction, not a fallback based on unrelated demos.

`overview.jpg` samples the video at 8-second intervals. `frames/` contains individually selected establishing, approach, pickup, transfer, pallet-side, depleted-stack, base-motion, and placement views. The video includes accelerated sequences and camera cuts; no timing or camera calibration is claimed.

## Observed geometry and activity

- Dark-blue low enclosed rectangular mobile base with chamfered shoulders, recessed dark underside, silver access handles, corner status lamps, red/yellow emergency stop, and a tall black sensor mast. Exact drive mechanism is hidden and is not identified as mecanum.
- White FANUC collaborative arm with dark round joint covers. Its mount is above the base deck on a short black bellows-covered riser. A large dark hose follows the arm.
- Rectangular metal wrist manifold with a visible array of green suction cups. The arm approaches carton top faces, lifts, turns toward the conveyor, lowers, and releases.
- Several wooden pallets form a line parallel to the conveyor. Two cartons across are clearly visible, with multiple layers; heights and carton orientation change as the robot empties pallets and moves along the line. The default represents an early loaded moment with three staging positions rather than all time-varying stacks at once.
- A real powered roller conveyor runs beside the base, on the opposite side from the source stacks. Silver cylindrical rollers, black rails and thin metal legs are visible. It is the destination; a second destination pallet would contradict the footage.
- Large gray industrial floor and high gray wall, surface electrical conduits, wall-mounted electrical cabinets, dock/loading equipment, yellow rails and bollards. Further wide shots show overhead steel structure and rows of boxes. People are visible transiently but are not included as static collision obstacles.

## Coordinate convention and estimates

Meters, Z-up; X follows the conveyor and pallet line; source pallets are at +Y and the conveyor is at -Y. The first robot's base ground center is `(0,0,0)`. These are estimated working coordinates, not surveyed positions. The actual arm geometry is used at its original scale.

| Quantity | Default | Basis and confidence |
|---|---|---|
| Pallet footprint | 1.2192 × 1.016 m | Standard 48 × 40 inch starting estimate; medium. Exact regional pallet type cannot be proven from perspective. |
| Pallet height | 0.145 m | Visual proportions and reused NVIDIA wooden pallet; medium. |
| Base enclosure | 1.32 × 0.90 × 0.64 m | Compared with adjacent pallet and known arm links; medium-low. |
| Arm base origin | `(0.22,0,0.88)` | End-offset mount with short riser, footage frames 0 and 24 s; medium-low. No attempt to enlarge the arm to fit the scene. |
| Arm link offsets | 0.37, 0.95, 0.75, 0.185 m | Official FANUC CRX-30iA USD joint frames; high for the asset, model identification medium. |
| Gripper contact offset | 0.30 m along wrist +X | Estimated 0.08 m wrist standoff plus 0.22 m manifold/cup depth; low. Standoff keeps the rectangular array clear of the original FANUC wrist housing. |
| Suction array footprint | 0.44 × 0.28 m, 12 green cups | Several green cups visible; precise cup count is an approximation, low. |
| Carton dimensions | 0.56 × 0.46 × 0.29 m | Compared with pallet deck and arm; medium-low. Footage contains more than one carton size. |
| Source stack | 2 × 2 × 4 cartons | Representative early stack; medium. Not asserted identical throughout footage. |
| Source pallet center | `(0,1.24,0)` | Adjacent side of base with a small aisle gap; medium-low. |
| Neighbor pallet centers | `(±1.65,1.24,0)` | Representative spacing from wide shots; low. |
| Conveyor deck | Z = 0.74 m, width 0.76 m | Compared with base deck/pallet; medium-low. |
| Conveyor centerline | Y = -1.18 m | Parallel to long base edge, reachable placement; medium-low. |
| Modeled conveyor length | 9 m | Crop of a visibly longer line; low. |
| Conveyor speed | 0.20 m/s | Operational demo setting; not measured in accelerated footage. |
| Modeled room | 18 × 14 × 8 m, rear wall Y = 4 m | Navigable crop of much larger warehouse; low. |
| Box mass | 5 kg | Simulation assumption, not a video measurement. |
| Suction payload limit | 22.7 kg | Public Pixmo product page's 50 lb payload; does not include pressure/contact calibration. |

## Sources and assumptions requiring visual review

- [Anyware solution](https://anyware-robotics.com/solution/) identifies its custom base, integrated linear riser and gripper. The current marketing page may depict a newer robot revision; the supplied footage controls the default scene.
- [FANUC supported-model mapping](https://fanuc-corporation.github.io/fanuc_driver_doc/main/docs/environment/supported_models.html) maps CRX-25iA to CRX-30iA. The original USD's manufacturer geometry and axes are preserved.
- [Official SimReady package](https://huggingface.co/datasets/FANUC-CORPORATION/SimReady-Assets/tree/main/crx30ia) supplies the arm. See the pinned download manifest and local license copies.

Remaining visual approximations include exact base dimensions, cup count, riser travel, individual sensors, warehouse cabinet/dock spacing, roof structure, cardboard printing and precise camera calibration. Navigation uses a planar servo, not claimed wheel dynamics. The riser is fixed at its observed approximate working height. No proprietary perception or planning system is reconstructed. Compare the rendered contact sheet with the retained footage before treating visual fidelity as verified.
