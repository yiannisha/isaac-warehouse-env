"""Deterministic layouts independent of Isaac runtime."""
import copy
import json
import random
import os
from pathlib import Path

ROOT = Path(os.environ.get('PIXMO_WORKSPACE',Path(__file__).resolve().parents[1]))


def load(path=None, randomized=False, seed=None):
    cfg = json.loads(Path(path or ROOT / 'configs/depalletizing_scene.json').read_text())
    if seed is not None: cfg['seed'] = seed
    if randomized:
        rng = random.Random(cfg['seed'])
        for p in cfg['pallets']:
            p['pattern'] = rng.choice(['grid', 'bond', 'irregular', 'partial', 'mixed'])
            p['perturbation_m'] = 0.004
    if cfg['physics_dt'] <= 0: raise ValueError('physics_dt must be positive')
    if not cfg['robots']: raise ValueError('At least one robot is required')
    if len({p['name'] for p in cfg['pallets']}) != len(cfg['pallets']):
        raise ValueError('Pallet names must be unique')
    for p in cfg['pallets']:
        if p['mass_kg'] <= 0 or any(v <= 0 for v in p['box_size']):
            raise ValueError('Box mass and dimensions must be positive')
    return cfg


def boxes_for_pallet(pallet, pallet_size, seed):
    """Non-overlapping stacks. Mixed layouts retain full support per column."""
    p = copy.deepcopy(pallet)
    rng = random.Random(seed)
    nx, ny, nz = p['grid']
    sx, sy, sz = p['box_size']
    gap = 0.008
    if nx * sx + (nx - 1) * gap > pallet_size[0] or ny * sy + (ny - 1) * gap > pallet_size[1]:
        raise ValueError(f"Boxes overhang pallet {p['name']}")
    if p['pattern'] not in ('grid', 'bond', 'mixed', 'irregular', 'partial'):
        raise ValueError('Unknown stack pattern ' + p['pattern'])
    result = []
    for i in range(nx):
        for j in range(ny):
            layers = nz
            if p['pattern'] in ('irregular', 'partial'):
                layers = rng.randint(max(1, nz - 2), nz)
            # Different column widths/heights with consistent support, no initial overlap.
            scale = rng.choice([0.82, 0.92, 1.0]) if p['pattern'] == 'mixed' else 1.0
            dims = [sx * scale, sy * scale, sz * scale]
            for k in range(layers):
                x = (i - (nx - 1) / 2) * (sx + gap)
                y = (j - (ny - 1) / 2) * (sy + gap)
                # Bond courses span the seams below, with half-cartons at the
                # two ends and full cartons across the interior boundaries.
                pieces = [(x, dims[0])]
                if p['pattern'] == 'bond' and k % 2 == 1:
                    if i>0:continue
                    half=(sx-gap)/2
                    widths=[half]+[sx]*(nx-1)+[half]
                    edge=-(nx*sx+(nx-1)*gap)/2
                    pieces=[]
                    for width in widths:
                        pieces.append((edge+width/2,width))
                        edge+=width+gap
                for xx, width in pieces:
                    d = [width, dims[1], dims[2]]
                    perturb = min(p.get('perturbation_m', 0), gap / 3)
                    xyz = [p['position'][0] + xx + rng.uniform(-perturb, perturb),
                           p['position'][1] + y + rng.uniform(-perturb, perturb),
                           p['position'][2] + pallet_size[2] + (k + .5) * dims[2] + .001]
                    result.append({'name': f"Box_{len(result):03d}", 'position': xyz,
                                   'size': d, 'mass': p['mass_kg'] * width / sx,
                                   'layer': k, 'sku': len(result) % 3})
    count=p.get('box_count',len(result))
    if not isinstance(count,int) or count<0 or count>len(result):
        raise ValueError('box_count must be between zero and the stack capacity')
    return result[:count]
