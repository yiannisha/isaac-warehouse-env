# Repository contents and setup

This repository contains the existing Dell rack simulation and the Pixmo warehouse environment. The warehouse uses the existing Isaac Sim container, desktop and artifact services. See [the warehouse guide](pixmo_environment.md) for build, validation and interactive commands, and [the supplied task](warehouse_plan.md) for the original requirements.

Clone on a machine with GitHub SSH access:

```bash
git clone git@github.com:yiannisha/isaac-warehouse-env.git
cd isaac-warehouse-env
```

The existing container expects the repository at `/workspace`. On the deployed VM its host directory remains `dell-rack`; configuring Git does not rename it or replace the running container. On another host, use that host's repository path for the workspace bind mount in `infra/start.sh`.

The reusable warehouse USD layers, original FANUC package and notices, pallet textures and NVIDIA terms, configuration, implementation and selected acceptance reports/renders are tracked. No Git LFS setup is required. Generated run directories, caches, virtual environments, the large NVIDIA datacenter pack, reference media and historical experiment output remain local and are ignored. The existing rack's source, authored assets and research notes are retained alongside the warehouse implementation.

The Anyware video, sampled frames and comparison sheet include third-party reference media and are not published in Git. Recover them locally with `pixmo/fetch_assets.py` and `pixmo/compare_views.py`, as described in the warehouse guide. The original asset/source archive and old run outputs linked by the acceptance document are VM artifacts; the Git checkout provides their tracked source and assets directly. Historical rack experiment reports referenced in older documents also remain VM-local.

For the rack demo, recover the large NVIDIA datacenter pack with `scripts/fetch_assets.sh` inside the existing container. The warehouse package resolves its own dependencies locally and does not require that pack.

The optional IsaacAutomator checkout is a separate upstream repository and is excluded from Git. Recover the documented revision when needed:

```bash
git clone --branch devcontainer https://github.com/boredengineering/IsaacAutomator.git vendor/IsaacAutomator
git -C vendor/IsaacAutomator checkout 1a708c60dc6f2eb6c00c774f729c109827fe80bd
```

Upstream assets retain their own licenses; this repository does not relicense NVIDIA or FANUC content. Provenance and approximation details are in [the asset sources](../references/pixmo/asset_sources.md).
