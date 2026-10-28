"""Deterministic, locally generated cardboard and concrete PBR color maps."""
import random
from pathlib import Path
from PIL import Image


def create(path,color,seed,fibers=False):
    rng=random.Random(seed)
    n=256
    pixels=[]
    for y in range(n):
        row=rng.uniform(-.009,.009) if fibers else 0
        for x in range(n):
            noise=rng.uniform(-.025,.025)+row
            if fibers and x%7==0:noise-=.008
            def encode(c):
                c=max(0,min(1,c+noise))
                return round((12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055)*255)
            pixels.append(tuple(encode(c) for c in color))
    image=Image.new('RGB',(n,n));image.putdata(pixels)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path)


def generate(directory):
    for i,color in enumerate([(.55,.40,.22),(.64,.48,.28),(.49,.35,.19)]):
        create(Path(directory)/f'cardboard_{i}.png',color,71+i,True)
    create(Path(directory)/'concrete.png',(.31,.33,.32),81)
