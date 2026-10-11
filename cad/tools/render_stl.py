#!/usr/bin/env python3
"""Render STL files to PNG previews (flat-shaded, no GPU needed).

    python3 cad/tools/render_stl.py out.png part.stl [more.stl ...] [--view iso|side|top|front]
"""
import argparse
import struct

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

VIEWS = {"iso": (24, -58), "side": (0, -90), "top": (90, -90), "front": (0, 0), "back_iso": (24, 122)}


def read_stl(path):
    with open(path, "rb") as fh:
        fh.read(80)
        n = struct.unpack("<I", fh.read(4))[0]
        rec = np.frombuffer(fh.read(n * 50), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return rec["v"].astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--view", default="iso", choices=VIEWS)
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    tris = np.concatenate([read_stl(p) for p in a.stl])
    elev, azim = VIEWS[a.view]
    fig = plt.figure(figsize=(9, 6), dpi=110)
    ax = fig.add_subplot(projection="3d")
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-9)
    light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
    base = np.array([0.25, 0.62, 0.78])
    pc = Poly3DCollection(tris, facecolors=np.clip(base[None] * shade[:, None], 0, 1), linewidths=0)
    ax.add_collection3d(pc)
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    ctr, span = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(ctr[0] - span, ctr[0] + span); ax.set_ylim(ctr[1] - span, ctr[1] + span); ax.set_zlim(max(0, ctr[2] - span), ctr[2] + span) if lo[2] >= 0 else ax.set_zlim(ctr[2] - span, ctr[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev, azim)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    if a.title:
        ax.set_title(a.title)
    plt.tight_layout()
    plt.savefig(a.out)


if __name__ == "__main__":
    main()
