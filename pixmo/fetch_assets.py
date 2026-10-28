"""Download official FANUC USD package and the primary Wistia reference.

Run with the existing container's python3. No Isaac installation required.
"""
import hashlib
import json
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HF = "https://huggingface.co/datasets/FANUC-CORPORATION/SimReady-Assets"


def fetch(url, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=90) as response:
        data = response.read()
    target.write_bytes(data)
    return {"url": url, "path": str(target.relative_to(ROOT)),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    ref = ROOT / "references/pixmo"
    ref.mkdir(parents=True, exist_ok=True)
    (ref/'frames').mkdir(parents=True,exist_ok=True)
    revision = 'cedea1f1a598d1da8745635ee9d5ac291b89df64'
    api = HF.replace('/datasets/', '/api/datasets/') + f'/tree/{revision}?recursive=true&limit=1000'
    fetch(api, ref / "fanuc_tree.json")
    entries = json.loads((ref / "fanuc_tree.json").read_text())
    selected = [e for e in entries if e["type"] == "file" and
                (e["path"].startswith("crx30ia/") or e["path"] in ("README.md", ".gitattributes"))]
    def download(entry):
        return fetch(HF + f'/resolve/{revision}/' + entry["path"],
                     ROOT / "assets/robots/pixmo/vendor/fanuc" / entry["path"])
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(download, selected))
    fetch("https://fast.wistia.com/embed/medias/dgqj21im6b.json", ref / "wistia_media.json")
    media = json.loads((ref / "wistia_media.json").read_text())["media"]
    asset = next(a for a in media["assets"] if a["type"] == "md_mp4_video")
    records.append(fetch(asset["url"], ref / "reference.mp4"))
    pallet_url='https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Props/Pallet/'
    for source,target in [('pallet.usd','nvidia_pallet.usd'),
                          ('Materials/Textures/FOF_Map_Palette_A_D.tga','pallet_diffuse.tga'),
                          ('Materials/Textures/FOF_Map_Palette_A_N.tga','pallet_normal.tga')]:
        records.append(fetch(pallet_url+source,ref/target))
    for timestamp,name in [(0,'establishing'),(8,'approach'),(12,'pickup'),(16,'transfer'),
                           (24,'pallet-side'),(40,'partial-stack'),(64,'base-movement'),(88,'placement')]:
        subprocess.run(['ffmpeg','-loglevel','error','-ss',str(timestamp),'-i',str(ref/'reference.mp4'),
                        '-frames:v','1','-y',str(ref/'frames'/f'{timestamp:03d}-{name}.jpg')],check=True)
    (ref / "download_manifest.json").write_text(json.dumps(
        {"fanuc_revision": revision, "wistia_id": "dgqj21im6b", "files": records}, indent=2))
    print(f'Downloaded {len(records)} files; FANUC revision {revision}', flush=True)


if __name__ == "__main__":
    main()
