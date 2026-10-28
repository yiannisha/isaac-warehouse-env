# Component discovery, provenance and licenses

## FANUC arm

Source: https://huggingface.co/datasets/FANUC-CORPORATION/SimReady-Assets, `crx30ia/`, revision `cedea1f1a598d1da8745635ee9d5ac291b89df64` downloaded 2026-10-27. The preferred official USD was accessible, so URDF/mesh conversion and handmade replacement arms were unnecessary. Local package: `assets/robots/pixmo/vendor/fanuc/crx30ia/`. Original Apache-2.0 `licenses/LICENSE.txt` and `THIRD_PARTY_NOTICES.txt` are preserved, along with MDL dependencies and metadata. Checksums appear in `download_manifest.json`.

The `PhysX=Enabled`, `Newton=Disabled`, `Robot=Robot` variant selections are used. Six original revolute joints, joint frames/axes/limits, meshes and inertial data are retained. The world-fixed joint is connected to the new mobile chassis; the articulation root moves to the assembled robot. Drive gains are simulation settings, not calibrated manufacturer tuning. A small kinematics-only URDF is derived from these exact USD joint frames for the installed NVIDIA Lula IK solver; it does not replace the official rendered or physical arm.

Existing Isaac installation was searched for CRX assets. It contains CRX-10iA/L motion policy data, which is a different model and was not substituted. FANUC's [official model mapping](https://fanuc-corporation.github.io/fanuc_driver_doc/main/docs/environment/supported_models.html) supports the CRX-30iA choice for CRX-25iA deployments.

## Mobile base and vacuum tool

The primary Wistia footage and Anyware's [solution page](https://anyware-robotics.com/solution/) were examined. Public web/GitHub searches for Pixmo CAD, STEP, STL, USD and URDF did not locate an accurate reusable base. This is a search result, not a claim that no asset exists anywhere. Anyware describes its base and gripper as its own designs. Existing installed assets did not supply a Pixmo base. Therefore the parameterized base is custom, with visual and collision components separated. Generic wheel geometry is omitted because its mechanism is hidden in the footage.

Vacuum component discovery included [Schmalz area-gripper CAD](https://www.schmalz.com/en-fr/products/automation-743270/vacuum-grippers-746238/gripping-systems-and-end-of-arm-tooling-eoat-746240/vacuum-area-gripping-system-fxp-fmp-306396/area-gripping-systems-fxp-306649/10.01.38.03082). The manufacturer page requires login for CAD download; its foam-array product also does not match the observed green cup array. No authenticated CAD was fetched or incompatible commercial product substituted. Manifold, adapter, cup bellows and hoses are procedural approximations, with contact validated separately from geometry. No claim that Pixmo uses a Schmalz product is made.

## Pallet

Existing project/datacenter assets were searched for pallets; none matched. Reused NVIDIA Isaac wooden pallet from `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Props/Pallet/pallet.usd`, plus its original diffuse and normal textures. [NVIDIA's documentation](https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_isaac_randomizers.html) identifies this asset. Source copies are retained under `references/pixmo/`, packaged copies under `assets/environments/pixmo_depalletizing/vendor/pallet/`. NVIDIA asset terms apply; these files are not relicensed under the FANUC Apache license. See the existing installation's `/isaac-sim/LICENSE.txt` and `/isaac-sim/PACKAGE-LICENSES` for the installed NVIDIA terms.

Visual scale is normalized from measured USD bounds to the configured pallet size. Original pallet visual/UV geometry is reused, with a portable UsdPreviewSurface material using its original texture. Compound static slat collision replaces the visual mesh collision so fork gaps remain open. Cardboard boxes and the scene-specific warehouse/conveyor are custom native USD geometry because generic warehouses would place unrelated equipment into the primary reference scene.

The original pallet material's `OmniPBR.mdl` reference is also resolved locally by copying the manufacturer-supplied MDL files already included in the FANUC package into the pallet vendor directory. Their original copyright headers and the full FANUC package's third-party notices are retained. This avoids an implicit shader-library lookup when checking the extracted bundle outside Isaac's renderer.

## Infrastructure reuse

Uses the existing `dell-rack-sim:6.0.1` container and Isaac `6.0.1-rc.7+release.42383.32955d8d.gl`, `rack_sim.geometry`, native USD/PhysX, installed Lula IK, viewport capture, native `omni.ui`, and the existing Xvfb/Fluxbox/noVNC/artifact server. No new repository, Isaac installation, remote desktop service, web platform or training framework is added.

## Reference media

The Wistia video and sampled frames remain Anyware Robotics reference material, not newly authored robot assets. Public accessibility is not a blanket redistribution license. They are retained locally for this requested comparison; no publishing or redistribution permission is implied.
