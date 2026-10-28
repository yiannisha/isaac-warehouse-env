"""Layout invariants used before expensive physical validation."""
import copy
import unittest
from pixmo.config import load,boxes_for_pallet


class LayoutTests(unittest.TestCase):
    def test_reference_reproducible(self):
        cfg=load()
        for p in cfg['pallets']:
            self.assertEqual(boxes_for_pallet(p,cfg['pallet_size'],7),boxes_for_pallet(p,cfg['pallet_size'],7))

    def test_all_patterns_no_initial_overlap_or_overhang(self):
        cfg=load();p=copy.deepcopy(cfg['pallets'][0]);size=cfg['pallet_size']
        for pattern in ['grid','bond','mixed','irregular','partial']:
            p['pattern']=pattern;p['perturbation_m']=.002
            for seed in range(5):
                boxes=boxes_for_pallet(p,size,seed)
                for i,a in enumerate(boxes):
                    for axis in [0,1]:
                        self.assertLessEqual(abs(a['position'][axis]-p['position'][axis])+a['size'][axis]/2,size[axis]/2)
                    for b in boxes[i+1:]:
                        depths=[(a['size'][k]+b['size'][k])/2-abs(a['position'][k]-b['position'][k]) for k in range(3)]
                        self.assertLess(min(depths),1e-8,(pattern,seed,a,b))

    def test_bad_layout_rejected(self):
        cfg=load();p=copy.deepcopy(cfg['pallets'][0]);p['box_size'][0]=2
        with self.assertRaises(ValueError):boxes_for_pallet(p,cfg['pallet_size'],7)

    def test_explicit_box_count(self):
        cfg=load();p=copy.deepcopy(cfg['pallets'][0]);p['box_count']=7
        self.assertEqual(len(boxes_for_pallet(p,cfg['pallet_size'],7)),7)

    def test_bond_courses_bridge_lower_seams(self):
        cfg=load();p=copy.deepcopy(cfg['pallets'][0]);p['pattern']='bond'
        boxes=boxes_for_pallet(p,cfg['pallet_size'],7)
        row_y=min(b['position'][1] for b in boxes)
        courses=[sorted([b for b in boxes if b['layer']==k and b['position'][1]==row_y],
                        key=lambda b:b['position'][0]) for k in [0,1]]
        lower_seam=(courses[0][0]['position'][0]+courses[0][1]['position'][0])/2
        self.assertTrue(any(b['position'][0]-b['size'][0]/2<lower_seam-.05 and
                            b['position'][0]+b['size'][0]/2>lower_seam+.05 for b in courses[1]))


if __name__=='__main__':unittest.main()
