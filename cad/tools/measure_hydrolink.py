#!/usr/bin/env python3
"""Re-measure the HydroLink / FlowLab interface numbers used by the lift design.

    python3 -I cad/tools/measure_hydrolink.py HydroLink_final_V1.33.3mf FlowLab3.3mf

Reads the 3MF archives directly (no slicer needed) and prints the plate list,
part sizes, the track cross-section, basin floor heights and the vortex drain.
The 3MF files themselves are not committed to this repo.
"""
import sys
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import manifold3d as mf
from shapely.geometry import Polygon

NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
PATH = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}path"


class Package:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        self.model = ET.fromstring(self.z.read("3D/3dmodel.model"))
        self.settings = ET.fromstring(self.z.read("Metadata/model_settings.config"))
        self._cache = {}

    def plates(self):
        for p in self.settings.findall("plate"):
            meta = {m.get("key"): m.get("value") for m in p.findall("metadata")}
            ids = [m.get("value") for mi in p.findall("model_instance") for m in mi.findall("metadata") if m.get("key") == "object_id"]
            yield meta.get("plater_name"), ids

    def solid(self, object_id):
        """Return the object as a Manifold in its own (component) frame."""
        for o in self.model.find("m:resources", NS).findall("m:object", NS):
            if o.get("id") != str(object_id):
                continue
            out = mf.Manifold()
            for c in o.find("m:components", NS).findall("m:component", NS):
                doc = self._doc(c.get(PATH).lstrip("/"))
                for oo in doc.find("m:resources", NS).findall("m:object", NS):
                    if oo.get("id") != c.get("objectid"):
                        continue
                    mesh = oo.find("m:mesh", NS)
                    v = np.array([[float(x.get(k)) for k in "xyz"] for x in mesh.find("m:vertices", NS)])
                    f = np.array([[int(x.get(k)) for k in ("v1", "v2", "v3")] for x in mesh.find("m:triangles", NS)])
                    a = np.array(list(map(float, c.get("transform").split()))) if c.get("transform") else np.r_[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0.0]
                    v = v @ a[:9].reshape(3, 3) + a[9:]
                    out += mf.Manifold(mf.Mesh(vert_properties=v.astype(np.float32), tri_verts=f.astype(np.uint32)))
            return out
        raise KeyError(object_id)

    def _doc(self, name):
        if name not in self._cache:
            self._cache[name] = ET.fromstring(self.z.read(name))
        return self._cache[name]


def size(m):
    b = m.bounding_box()
    return tuple(round(b[i + 3] - b[i], 1) for i in range(3))


def floor_top(m):
    """Height above the base where the solid cross-section first drops sharply."""
    b = m.bounding_box()
    area = lambda z: sum(abs(Polygon(p).area) for p in m.slice(b[2] + z).to_polygons())
    a0 = area(0.2)
    for z in np.arange(0.4, 30, 0.2):
        if area(z) < 0.3 * a0:
            return round(z, 1)


def main(hydro, flow):
    H, F = Package(hydro), Package(flow)
    for name, pkg in (("HydroLink", H), ("FlowLab", F)):
        print(f"\n== {name} plates")
        for plate, ids in pkg.plates():
            print(f"  {plate:22s} x{len(ids)}  {size(pkg.solid(ids[0]))}")

    plate = dict(H.plates())
    # Track "I": CAD frame is x across, y up, z along the track.
    track = H.solid(plate["I"][0])
    mid = max(track.slice(0).to_polygons(), key=lambda p: abs(Polygon(p).area))
    p = np.asarray(mid)
    floor = p[np.abs(p[:, 0]) < 2, 1].max()
    print("\n== Track 'I' cross-section at mid-length")
    print(f"  outer {np.ptp(p[:, 0]):.1f} wide x {np.ptp(p[:, 1]):.1f} tall; inner floor {floor - p[:, 1].min():.1f} above underside")
    print(f"  flange zone: last {100 - 90} mm at each end, {size(track)[0]} mm wide")

    for b in ("Big basin", "Medium basin"):
        basin = H.solid(plate[b][0]).rotate((90, 0, 0))
        print(f"== {b}: size {size(basin)}, inner floor top ~{floor_top(basin)} mm above table")

    fplate = dict(F.plates())
    floaty = F.solid(fplate["Floaty"][0])
    print(f"== Floaty: {size(floaty)}")
    ins = F.solid(fplate["Vortex insert"][0])
    v = np.asarray(ins.to_mesh().vert_properties)[:, :3]
    c = v.mean(0)
    near = v[np.hypot(v[:, 0] - c[0], v[:, 2] - c[2]) < 20]
    print(f"== Vortex insert: size {size(ins)}, centre drain ~{np.ptp(near[:, 0]):.0f} x {np.ptp(near[:, 2]):.0f} mm")
    blk = F.solid(fplate["Flow blocker"][0])
    print(f"== Flow blocker / modifier body: {size(blk)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
