"""SER 2027 poster: rabbits, wildcats, pond turtles and a free-flowing river.

One A0 portrait poster for the 12th SER World Conference on Ecological
Restoration (Lisbon, 2027), theme "Lands in Motion". It combines the rabbit
release screen (prey for the wildcat) and the pond turtle pool screen on one
map, with the two UNESCO World Heritage areas, the three plates after the Côa
Iron Age fine-line engravings, and figures from the Côa eco-connectivity study.

Every number on the map and in the panels is computed here from the v6 data
bundle, through the screening code in the source repository (SOURCE below):
research/rewilding-dynamics/scripts/release_candidates.py. Nothing is typed in
by hand except dates and figures taken from published sources, which are cited.

Run:  conda run -n coa python scripts/poster.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch
from matplotlib.textpath import TextToPath
from PIL import Image
from rasterio.features import geometry_mask
from shapely.geometry import box

# Source repository (Solo-field-illustrator-project-for-Rewilding-Portugal), screening code and bundle paths
SOURCE = Path("/home/linda/Documents/myData/Solo-field-illustrator-project-for-Rewilding-Portugal/research/"
              "rewilding-dynamics/scripts")
sys.path.insert(0, str(SOURCE))
import release_candidates as rc  # noqa: E402  (computes the layers on import; draws nothing)

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
N2K = Path("/home/linda/Documents/myData/data-management/data/raw/landcover/natura2000/Natura2000_end2024.gpkg")
NE = Path("/home/linda/Documents/myData/data-management/data/raw/colab/ne_10m_admin_0_countries.geojson")
OUT = ROOT / "poster"
OUT.mkdir(exist_ok=True)

FIG_W, FIG_H = 33.11, 46.81  # A0 portrait, inches; every position below is a fraction, so another size is one edit
PT_W, PT_H = FIG_W * 72, FIG_H * 72
CREAM, PAPER, NAVY, CORAL, PURPLE, BLUE, SUN, SKY = (rc.CREAM, rc.PAPER, rc.NAVY, rc.CORAL, rc.PURPLE, rc.BLUE,
                                                   rc.SUN, rc.SKY)
SIENNA = "#8a361b"
DISPLAY = rc.DISPLAY
BOLD = font_manager.FontProperties(fname=str(rc.CACHE / "fonts" / "Exo2-700.ttf"))
BODY = font_manager.FontProperties(fname=str(rc.CACHE / "fonts" / "Exo2-400.ttf"))
plt.rcParams["pdf.fonttype"] = 42  # embed TrueType, so the PDF prints as designed

SIZE = 28        # body text, points at A0
SMALL = 22
HEAD = 58

# ---------------------------------------------------------------------------
# Figures from the screen
# ---------------------------------------------------------------------------
heritage = {lay: gpd.read_file(rc.PROCESSED / "heritage_protection.gpkg", layer=lay).to_crs(3035)
            for lay in ["unesco_alto_douro", "coa_rock_art_core"]}
douro_u = heritage["unesco_alto_douro"].union_all()
coa_core_u = heritage["coa_rock_art_core"].union_all()
cand_u = rc.cand_poly.union_all()
cand_km2 = rc.km2(rc.candidate)
douro_overlap_ha = cand_u.intersection(douro_u).area / 1e4
core_overlap_ha = cand_u.intersection(coa_core_u).area / 1e4
cand_pts = rc.pts[rc.pts.candidate]
pools_in_core = int(cand_pts.within(coa_core_u.buffer(0)).sum())
n_pools, n_cand, n_paired = len(rc.pts), int(rc.pts.candidate.sum()), int(rc.pts.paired.sum())
douro_in_area_ha = douro_u.intersection(rc.area).area / 1e4
res = rc.res_poly.copy()
res["ha"] = res.area / 1e4
sabor = res.sort_values("ha").iloc[-1]  # the largest water body over 50 ha in the area: Baixo Sabor (Cerejais)

# The border: how much of the study area is in Spain, and what the v6 model covers there
countries = gpd.read_file(NE, columns=["ADMIN"], bbox=(-8.5, 39.5, -6.0, 42.0)).to_crs(3035)
spain = countries[countries.ADMIN == "Spain"].union_all()
portugal = countries[countries.ADMIN == "Portugal"].union_all()
spain_in = rc.area.intersection(spain)
spain_share = spain_in.area / rc.area.area
border_km = portugal.boundary.intersection(spain.boundary).intersection(rc.area).length / 1000
spain_mask = ~geometry_mask([spain], out_shape=rc.land.shape, transform=rc.template.rio.transform()) & rc.inside
spain_unmodelled = np.isnan(rc.land[spain_mask]).mean()
spain_cand_km2 = cand_u.intersection(spain).area / 1e6
natura = gpd.read_file(N2K, layer="NaturaSite_polygon", bbox=rc.area.bounds)
natura = natura[natura.intersects(rc.area)]
natura_u = natura.union_all()
natura_share = natura_u.intersection(rc.area).area / rc.area.area
print(f"Spain {spain_in.area / 1e6:.0f} km² ({spain_share:.1%}), border {border_km:.0f} km, unmodelled {spain_unmodelled:.0%}, "
      f"rabbit candidates in Spain {spain_cand_km2:.1f} km²; Natura 2000 {natura_share:.1%} of the study area, "
      f"{len(natura)} sites")
print(f"rabbit {cand_km2:.0f} km², hunting {rc.hunt_share:.1%}, Douro WH overlap {douro_overlap_ha:.1f} ha, "
      f"Côa core overlap {core_overlap_ha:.1f} ha; pools {n_pools}, candidates {n_cand}, paired {n_paired}, "
      f"candidate pools in Côa core {pools_in_core}; largest reservoir {sabor.ha:.0f} ha")


# ---------------------------------------------------------------------------
# Text layout: measured wrapping, columns that flow top to bottom
# ---------------------------------------------------------------------------
TTP = TextToPath()


def width_pt(s, prop, size):
    p = prop.copy()
    p.set_size(size)
    return TTP.get_text_width_height_descent(s, p, ismath=False)[0]


def wrap(text, prop, size, width):
    """Greedy word wrap to a width in points, measured on the real font."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}".strip()
            if line and width_pt(trial, prop, size) > width:
                out.append(line)
                line = word
            else:
                line = trial
        out.append(line)
    return out


ROW_SIZE = SIZE - 2


class Column:
    """A text column: x, width and current y are figure fractions; y moves down as blocks are added."""

    def __init__(self, fig, x, width, top):
        self.fig, self.x, self.w, self.y = fig, x, width, top

    def gap(self, pt):
        self.y -= pt / PT_H

    def head(self, text, colour=CORAL):
        self.fig.text(self.x, self.y, text.upper(), fontproperties=DISPLAY, fontsize=HEAD, color=colour, va="top")
        self.gap(HEAD * 1.05)

    def kicker(self, text, colour=NAVY):
        self.fig.text(self.x, self.y, text.upper(), fontproperties=BOLD, fontsize=SMALL, color=colour, va="top")
        self.gap(SMALL * 1.7)

    def para(self, text, size=SIZE, prop=BODY, colour=NAVY, spacing=1.38, width=None, x=None):
        lines = wrap(text, prop, size, (width or self.w) * PT_W)
        self.fig.text(x if x is not None else self.x, self.y, "\n".join(lines), fontproperties=prop, fontsize=size,
                      color=colour, va="top", linespacing=spacing)
        self.gap(len(lines) * size * spacing + size * 0.55)

    def axes(self, height_pt, width=None, x=None):
        ax = self.fig.add_axes([x if x is not None else self.x, self.y - height_pt / PT_H, width or self.w,
                                height_pt / PT_H])
        self.gap(height_pt)
        return ax


def panel_box(fig, x, y0, y1, w, colour=PAPER, edge=None):
    pad = 18 / PT_W
    fig.patches.append(FancyBboxPatch((x - pad, y1 - pad), w + 2 * pad, y0 - y1 + 2 * pad, transform=fig.transFigure,
                                      boxstyle=f"round,pad=0,rounding_size={10 / PT_W}", facecolor=colour,
                                      edgecolor=edge or colour, linewidth=2, zorder=-1))


# ---------------------------------------------------------------------------
# Poster: header band / map block with two flanks / three panels / references
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=CREAM)

# ---- Header band, set apart from the body -----------------------------------
HEAD_Y = 0.902
hdr = fig.add_axes([0, HEAD_Y, 1, 1 - HEAD_Y])
hdr.set_facecolor(NAVY)
hdr.set_xticks([])
hdr.set_yticks([])
for side in hdr.spines.values():
    side.set_visible(False)
rc.band(fig, HEAD_Y - 0.006, 0.006, [CORAL, PURPLE, BLUE, SUN])
fig.text(0.03, 0.988, "SER 2027 · 12th World Conference on Ecological Restoration · Lisbon · Lands in Motion".upper(),
         fontproperties=BOLD, fontsize=26, color=SUN, va="top")
fig.text(0.03, 0.978, "Rabbits, wildcats, pond turtles\nand a free-flowing river".upper(), fontproperties=DISPLAY,
         fontsize=128, color=CREAM, va="top", linespacing=0.92)
fig.text(0.03, 0.9195, "One open connectivity screen for trophic and hydrological rewilding in the Greater Côa Valley, "
         "Portugal", fontproperties=BODY, fontsize=34, color=CREAM, va="top")
fig.text(0.03, 0.9095, "Linda Angulo Lopez  ·  Côa Connectivity Lab  ·  ORCID 0009-0009-5689-7148",
         fontproperties=BOLD, fontsize=27, color=SUN, va="top")
links = ("Preprint (synthesis, hypotheses, plate method)\ndoi.org/10.5281/zenodo.22997241\n"
         "Preprint (connectivity workflow)\ndoi.org/10.5281/zenodo.22979020\n"
         "Data: Côa Valley Eco-Connectivity v6\ndata.gouv.fr/datasets/coa-valley-eco-connectivity-v6\n"
         "Poster code and files\ngithub.com/coa-connectivity-lab/ser2027")
fig.text(0.97, 0.978, links, fontproperties=BODY, fontsize=19, color=CREAM, va="top", ha="right", linespacing=1.45)

TOP = 0.876
XL, WL = 0.03, 0.235          # left flank
XB, WB = 0.29, 0.42           # map block, centred on the page (0.29 + 0.42 / 2 = 0.5)
XR, WR = 0.735, 0.235         # right flank

# ---- Map block: the focal point ---------------------------------------------
B = Column(fig, XB + 0.015, WB - 0.03, TOP - 0.012)
block_top = TOP
title_w = width_pt("GREATER CÔA VALLEY, PORTUGAL", DISPLAY, HEAD + 10) / PT_W
fig.text(0.5, B.y, "GREATER CÔA VALLEY, PORTUGAL", fontproperties=DISPLAY, fontsize=HEAD + 10, color=CORAL, va="top",
         ha="center")
B.gap((HEAD + 10) * 1.05)
for line in wrap("Rabbit release candidates inside the wildcat's corridors, pond turtle pools and the two World "
                 "Heritage areas, on one map. Screening maps, not release sites: every candidate needs a field "
                 "survey first.", BODY, SIZE, B.w * PT_W):
    fig.text(0.5, B.y, line, fontproperties=BODY, fontsize=SIZE, color=NAVY, va="top", ha="center")
    B.gap(SIZE * 1.38)
B.gap(22)

# key figures in one row across the block
stats = [(f"{cand_km2:,.0f}", "km² of rabbit\ncandidate area"),
         (f"{rc.hunt_share:.0%}", "of it inside\nhunting zones"),
         ("10", "priority\nsurvey blocks"),
         (f"{n_cand}/{n_pools}", "year-round pools\nare candidates"),
         (str(n_paired), "pool within 2 km\nof a rabbit area"),
         (str(rc.n_wildcat), "wildcat records\nin GBIF here")]
cell = B.w / len(stats)
for i, (big, small) in enumerate(stats):
    cx = B.x + (i + 0.5) * cell
    fig.text(cx, B.y, big, fontproperties=DISPLAY, fontsize=64, color=CORAL if i < 3 else BLUE, va="top",
             ha="center")
    fig.text(cx, B.y - 68 / PT_H, small, fontproperties=BODY, fontsize=17, color=NAVY, va="top", ha="center",
             linespacing=1.2)
B.gap(140)

s = rc.study.to_crs(rc.PLOT_CRS)
bx0, by0, bx1, by1 = s.total_bounds
map_w = 0.335
PAD_W, PAD_S = 8000, 6000  # extra margin west and south, room for the locator inset
map_h_pt = map_w * PT_W * (by1 - by0 + 4000 + PAD_S) / (bx1 - bx0 + 4000 + PAD_W)
ax = B.axes(map_h_pt, width=map_w, x=0.5 - map_w / 2)
ax.set_facecolor(PAPER)
s.plot(ax=ax, color=CREAM, zorder=0)
grid = rc.template.copy(data=np.where(rc.habitat_only, 1, np.where(rc.candidate, 2, 0)).astype("float32"))
grid = grid.where(grid > 0).rio.write_nodata(np.nan).rio.reproject(rc.PLOT_CRS)
gx0, gy0, gx1, gy1 = grid.rio.bounds()
ax.imshow(grid.values, extent=(gx0, gx1, gy0, gy1), cmap=ListedColormap(["#dfe6b4", CORAL]), vmin=1, vmax=2,
          interpolation="nearest", zorder=1)
rc.hunting.to_crs(rc.PLOT_CRS).boundary.plot(ax=ax, color="#cfc6b6", linewidth=0.35, zorder=2)
hydro = gpd.read_file(rc.HYDRO, bbox=tuple(rc.study.to_crs(4326).total_bounds))
hydro[hydro.ORD_STRA >= 6].to_crs(rc.PLOT_CRS).plot(ax=ax, color="#9dbbe6", linewidth=2.6, zorder=2)
rc.rivers.to_crs(rc.PLOT_CRS).plot(ax=ax, color="#7da2dc", linewidth=1.2, zorder=2)
res.to_crs(rc.PLOT_CRS).plot(ax=ax, color=SKY, edgecolor="#7da2dc", linewidth=0.8, zorder=3)
gpd.GeoSeries([spain_in], crs=3035).to_crs(rc.PLOT_CRS).plot(ax=ax, color=PAPER, alpha=0.72, zorder=3.5)
gpd.GeoSeries([natura_u.intersection(rc.area).boundary], crs=3035).to_crs(rc.PLOT_CRS).plot(
    ax=ax, color="#3f7d3a", linewidth=1.6, linestyle=(0, (2, 1.5)), zorder=4.5)
gpd.GeoSeries([portugal.boundary.intersection(spain.boundary).intersection(rc.area.buffer(2000))], crs=3035).to_crs(
    rc.PLOT_CRS).plot(ax=ax, color=NAVY, linewidth=3, linestyle=(0, (6, 2, 1, 2)), zorder=9)
douro_clip = gpd.GeoSeries([douro_u.intersection(rc.area)], crs=3035).to_crs(rc.PLOT_CRS)
douro_clip.plot(ax=ax, facecolor="none", edgecolor=PURPLE, hatch="///", linewidth=1.6, zorder=4)
gpd.GeoSeries([coa_core_u], crs=3035).to_crs(rc.PLOT_CRS).plot(ax=ax, color=PURPLE, edgecolor=PURPLE, linewidth=2.5,
                                                                zorder=4)
pr = rc.priority.to_crs(rc.PLOT_CRS)
pr.boundary.plot(ax=ax, color=NAVY, linewidth=2.0, zorder=5)
p = rc.pts.to_crs(rc.PLOT_CRS)
size = 5 * (14 + 8 * np.sqrt(p["ha"].clip(upper=20)))
p[~p.candidate].plot(ax=ax, color="#b9c7e6", markersize=size[~p.candidate], zorder=6)
p[p.candidate].plot(ax=ax, color=BLUE, markersize=size[p.candidate], edgecolor="white", linewidth=1.2, zorder=7)
p[p.paired].plot(ax=ax, facecolor="none", edgecolor=CORAL, markersize=size[p.paired] * 4, linewidth=3, zorder=8)
s.boundary.plot(ax=ax, color=NAVY, linewidth=1.4, linestyle=(0, (4, 2)), zorder=8)
rc.coa.to_crs(rc.PLOT_CRS).plot(ax=ax, color=NAVY, linewidth=3.2, zorder=8)
for r in pr.itertuples():
    c = r.geometry.representative_point()
    ax.text(c.x, c.y, str(r.rank), fontproperties=DISPLAY, fontsize=30, color="white", ha="center", va="center",
            zorder=10, bbox=dict(boxstyle="circle,pad=0.2", facecolor=NAVY, edgecolor="none"))


def label(x, y, text, colour=NAVY, ha="left"):
    ax.text(x, y, text, fontproperties=BOLD, fontsize=19, color=colour, ha=ha, va="center", zorder=11,
            bbox=dict(boxstyle="round,pad=0.25", facecolor=PAPER, edgecolor="none", alpha=0.85))


sab = gpd.GeoSeries([sabor.geometry], crs=3035).to_crs(rc.PLOT_CRS).iloc[0].representative_point()
label(sab.x + 3000, sab.y + 3500, "Baixo Sabor\nreservoir")
core_pt = gpd.GeoSeries([coa_core_u], crs=3035).to_crs(rc.PLOT_CRS).iloc[0].centroid
label(core_pt.x + 5000, core_pt.y - 7000, "Côa rock art\n(UNESCO 1998)", PURPLE, ha="left")
dpt = douro_clip.iloc[0].representative_point()
label(dpt.x, dpt.y + 6000, "Alto Douro Wine Region\n(UNESCO 2001)", PURPLE, ha="center")
mid = rc.coa.to_crs(rc.PLOT_CRS).union_all().interpolate(0.5, normalized=True)
label(mid.x - 4000, mid.y + 3000, "River Côa", NAVY, ha="right")
es_pt = gpd.GeoSeries([spain_in], crs=3035).to_crs(rc.PLOT_CRS).iloc[0].representative_point()
label(es_pt.x, es_pt.y, "SPAIN\nconnectivity not\nyet modelled", "#5b5146", ha="center")
ax.set_xlim(bx0 - 2000 - PAD_W, bx1 + 2000)
ax.set_ylim(by0 - 2000 - PAD_S, by1 + 2000)
x0, y0 = bx1 - 16000, by0 + 3000
ax.plot([x0, x0 + 10000], [y0, y0], color=NAVY, linewidth=7, solid_capstyle="butt")
ax.text(x0 + 5000, y0 + 2200, "10 km", ha="center", fontproperties=BODY, fontsize=19, color=NAVY)
ax.annotate("N", xy=(bx1 - 2500, by0 + 20000), xytext=(bx1 - 2500, by0 + 12000), ha="center", fontproperties=BOLD,
            fontsize=24, color=NAVY, arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=3, mutation_scale=30))
ax.set_axis_off()

# Locator: where the study area sits in Portugal (Natural Earth 1:10m, public domain)
iberia_box = box(-9.8, 36.0, 3.4, 43.9)
ne = gpd.read_file(NE, columns=["ADMIN"], bbox=iberia_box.bounds)
ne = ne[ne.ADMIN.isin(["Portugal", "Spain", "France", "Andorra"])].clip(iberia_box).to_crs(3035)
loc = ax.inset_axes([0.0, 0.0, 0.25, 0.17])
loc.set_facecolor(SKY)
ne[ne.ADMIN != "Portugal"].plot(ax=loc, color="#e6dccb", edgecolor="#b8ab95", linewidth=0.8)
ne[ne.ADMIN == "Portugal"].plot(ax=loc, color=CREAM, edgecolor=NAVY, linewidth=1.6)
rc.study.plot(ax=loc, color=CORAL, edgecolor=NAVY, linewidth=1.0)
lx0, ly0, lx1, ly1 = ne.total_bounds
loc.set_xlim(lx0 - 20000, lx1 + 20000)
loc.set_ylim(ly0 - 20000, ly1 + 20000)
loc.set_aspect("equal")
loc.set_xticks([])
loc.set_yticks([])
for side in loc.spines.values():
    side.set_edgecolor(NAVY)
    side.set_linewidth(1.5)
loc.text(lx0 + 15000, ly0 + 5000, "PORTUGAL", fontproperties=BOLD, fontsize=12, color=NAVY, ha="left", va="bottom")
loc.text(lx0 + 0.6 * (lx1 - lx0), ly0 + 0.45 * (ly1 - ly0), "SPAIN", fontproperties=BOLD, fontsize=12,
         color="#8d806b", ha="center")
sc = rc.study.to_crs(3035).union_all().centroid
loc.annotate("Study area", xy=(sc.x + 30000, sc.y), xytext=(sc.x + 160000, sc.y + 90000), fontproperties=BOLD,
             fontsize=12, color=CORAL, arrowprops=dict(arrowstyle="-", color=CORAL, lw=1.2))

B.gap(18)
leg = fig.legend(handles=[
    Patch(facecolor=CORAL, edgecolor=NAVY, linewidth=2, label="Priority survey block (1 to 10)"),
    Patch(color=CORAL, label="Rabbit candidate area, survey first"),
    Patch(color="#dfe6b4", label="Rabbit mosaic outside the corridors"),
    Line2D([], [], color=BLUE, marker="o", lw=0, markersize=16, label="Candidate pool, survey in August"),
    Line2D([], [], color="#b9c7e6", marker="o", lw=0, markersize=16, label="Year-round pool, weaker connectivity"),
    Line2D([], [], markerfacecolor="none", markeredgecolor=CORAL, marker="o", lw=0, markersize=24, mew=3,
           label="Pool paired with a rabbit area (H6)"),
    Patch(facecolor="none", edgecolor=PURPLE, hatch="///", label="Alto Douro Wine Region (UNESCO)"),
    Patch(color=PURPLE, label="Côa rock-art core (UNESCO)"),
    Patch(facecolor=SKY, edgecolor="#7da2dc", label="Reservoirs over 50 ha (left out)"),
    Line2D([], [], color="#cfc6b6", lw=2, label="Hunting zones"),
    Line2D([], [], color="#3f7d3a", lw=2.5, ls=(0, (2, 1.5)), label="Natura 2000 sites (SCI and SPA)"),
    Line2D([], [], color=NAVY, lw=3, ls=(0, (6, 2, 1, 2)), label="Portugal-Spain border"),
], loc="upper center", bbox_to_anchor=(0.5, B.y), ncol=2, prop=BODY.copy(), frameon=False, labelcolor=NAVY,
    handlelength=1.6, columnspacing=1.6, labelspacing=0.7)
for t in leg.get_texts():
    t.set_fontsize(SMALL)
B.gap(6 * SMALL * 1.72 + 20)
panel_box(fig, XB, block_top, B.y, WB, colour=PAPER, edge=NAVY)
body_bottom = B.y

# ---- Left flank: the chain and the method -----------------------------------
L = Column(fig, XL, WL, TOP)
L.head("Three animals, one chain")
L.para("The European rabbit (Oryctolagus cuniculus) is the keystone prey of the Iberian Peninsula, and Endangered in "
       "its native range. The European wildcat (Felis silvestris) depends on it. The pond turtle links the pair to "
       "the river: it holds on where summer pools hold water. In the Côa, predators, prey and rivers meet in three "
       "animals.", size=SIZE - 1)
L.gap(20)
chain = L.axes(560)
chain.set_xlim(0, 10)
chain.set_ylim(0.1, 5.8)
chain.set_axis_off()
nodes = {"Grazing\nand fire": (1.15, 4.7), "Open\nmosaic": (3.7, 4.7), "Rabbit": (6.2, 4.7), "Wildcat": (8.75, 4.7),
         "Free-flowing\nCôa": (1.05, 1.0), "Summer\npools": (3.7, 1.0), "Pond\nturtle": (6.2, 1.0),
         "River\nhealth": (8.75, 1.0)}
animals = ("Rabbit", "Wildcat", "Pond\nturtle")
for name, (x, y) in nodes.items():
    colour = CORAL if y > 3 else BLUE
    chain.text(x, y, name, ha="center", va="center", fontproperties=BOLD, fontsize=21,
               color="white" if name in animals else NAVY,
               bbox=dict(boxstyle="round,pad=0.5", linewidth=2.5, edgecolor=colour,
                         facecolor=colour if name in animals else PAPER))


def arrow(a, b, colour, style="-"):
    (x0, y0), (x1, y1) = nodes[a], nodes[b]
    chain.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=30, color=colour, lw=3,
                                    linestyle=style, shrinkA=48, shrinkB=48))


for a, b in [("Grazing\nand fire", "Open\nmosaic"), ("Open\nmosaic", "Rabbit"), ("Rabbit", "Wildcat")]:
    arrow(a, b, CORAL)
for a, b in [("Free-flowing\nCôa", "Summer\npools"), ("Summer\npools", "Pond\nturtle"), ("Pond\nturtle", "River\nhealth")]:
    arrow(a, b, BLUE)
arrow("Rabbit", "Pond\nturtle", PURPLE, style=(0, (3, 2)))
chain.text(6.45, 2.85, "prey buffer: when\nrabbits crash, predators\nturn to reptiles (H6)", fontproperties=BODY,
           fontsize=18, color=PURPLE, va="center")
chain.text(0.05, 5.75, "LAND", fontproperties=BOLD, fontsize=16, color=CORAL, va="top")
chain.text(0.05, 2.3, "WATER", fontproperties=BOLD, fontsize=16, color=BLUE, va="top")
L.para("About 45 references, joined into one chain and seven testable hypotheses (Angulo Lopez, 2026a).",
       size=SMALL - 2)
L.gap(50)
L.head("Method")
L.para(f"(i) Study area of 10,230 km², the Côa and 30 km around it, extended to its catchment; {spain_share:.0%} "
       "of it lies in Spain, where v6 models no current.\n"
       "(ii) Ten focal species in land, water and air groups, from GBIF records and Natura 2000.\n"
       "(iii) Circuit theory in pure Python, a moving-window solver after Prima et al. (2024), on a laptop, with no "
       "paid software.\n"
       "(iv) Three local penalties: fire weighted by recency (MODIS, 2015 to July 2025), 22 barriers recorded in the "
       "field in August 2026, and the two World Heritage areas.\n"
       "(v) Rabbit screen: scrub-pasture mosaic (ESA WorldCover 2021), not burned since 2023, 200 m or more from a "
       "road, in the top third of the land-group current, blocks of 1 km² or more.\n"
       "(vi) Pond turtle screen: pools with water in all 12 months of 2021 (JRC Global Surface Water), within 200 m "
       "of a river, reservoirs over 50 ha left out, on the better-connected half of the water-group current.",
       size=SIZE - 2)

# ---- Right flank: the plates ----------------------------------------------------
R = Column(fig, XR, WR, TOP)
R.head("New animals in an old line")
R.para("New works after the Iron Age fine-line engravings of the Côa, not ancient motifs. Each animal keeps one "
       "diagnostic feature and is paired with one sentence of evidence. Digital studies; the hand-cut plates follow. "
       "Nothing is drawn on rock.", size=SMALL - 1)
R.gap(6)
plates = [
    ("plate-rabbit.jpg", "Rabbit · prey", CORAL,
     f"Keystone prey, Endangered in its native range. {cand_km2:,.0f} km² of candidate release area. Rock art: two "
     "possible lagomorphs at Vermelhosa, Palaeolithic and uncertain."),
    ("plate-wildcat.jpg", "Wildcat · beneficiary", CORAL,
     f"Supported, not released: neutering of domestic cats near villages, with mesopredator monitoring. "
     f"{rc.n_wildcat} GBIF records here. Rock art: three possible felids, Palaeolithic and uncertain."),
    ("plate-pond-turtle.jpg", "Pond turtle · river indicator", BLUE,
     f"Presence in the Côa unconfirmed. GBIF holds {rc.n_turtle} Emys orbicularis records (2002 to 2010) and no "
     "Mauremys leprosa. Survey in August before any release. Not in the rock art."),
]
img_w = 0.118
img_h_pt = img_w * PT_W * 5 / 4
for fname, title, colour, text in plates:
    top = R.y
    pax = fig.add_axes([XR, top - img_h_pt / PT_H, img_w, img_h_pt / PT_H])
    pax.imshow(Image.open(IMG / fname))
    pax.set_axis_off()
    tx, tw = XR + img_w + 0.01, WR - img_w - 0.01
    fig.text(tx, top - 4 / PT_H, "\n".join(wrap(title.upper(), DISPLAY, 34, tw * PT_W)), fontproperties=DISPLAY,
             fontsize=34, color=colour, va="top", linespacing=1.1)
    n_title = len(wrap(title.upper(), DISPLAY, 34, tw * PT_W))
    fig.text(tx, top - (16 + 40 * n_title) / PT_H, "\n".join(wrap(text, BODY, SMALL - 2, tw * PT_W)),
             fontproperties=BODY, fontsize=SMALL - 2, color=NAVY, va="top", linespacing=1.32)
    R.gap(img_h_pt + 24)
R.gap(30)
R.head("Across the border")
R.para(f"(i) {spain_share:.0%} of the study area ({spain_in.area / 1e6:,.0f} km²) lies in Spain, along "
       f"{border_km:.0f} km of border.\n"
       f"(ii) Natura 2000 covers {natura_share:.0%} of it, in sites that face each other: Douro Internacional e Vale "
       "do Águeda (PT) and Arribes del Duero (ES); Vale do Côa (PT) and Campo de Azaba and Campo de Argañán (ES); "
       "Malcata (PT) and El Rebollar and Sierra de Gata (ES).\n"
       "(iii) The Douro Internacional (1998) and Arribes del Duero (2002) natural parks are two of the four parks "
       "of the Meseta Ibérica transboundary Biosphere Reserve (UNESCO 2015). The Serra da Malcata nature reserve and "
       "the Serra da Estrela natural park lie to the south.\n"
       f"(iv) The v6 model stops at the border: {spain_unmodelled:.0%} of the Spanish side has no modelled current, "
       f"so only {spain_cand_km2:.0f} km² of rabbit candidates fall in Spain, and the turtle screen follows the Côa "
       "catchment only, which leaves out the Águeda.", size=SMALL - 1)

# ---- Row of three panels under the map block ---------------------------------
ROW_TOP = min(body_bottom, L.y, R.y) - 0.022
XP, WP = [0.03, 0.355, 0.68], 0.29
P1 = Column(fig, XP[0], WP, ROW_TOP)
P1.head("A free-flowing river")
P1.para("The Côa stayed free-flowing because of its rock art. In 1995 students at the Vila Nova de Foz Côa secondary "
        "school took up the slogan \"As gravuras não sabem nadar\" (the engravings can't swim) against a dam that would "
        "have flooded open-air engravings more than 20,000 years old. The government led by António Guterres "
        "suspended the dam on 17 January 1996. UNESCO inscribed the sites in 1998, and extended them to Siega Verde, "
        "Spain, in 2010.", size=ROW_SIZE)
P1.para("Where the Côa meets the Douro, the Alto Douro Wine Region (UNESCO 2001, 24,600 ha of terraced vineyard, "
        f"{douro_in_area_ha / 100:,.0f} km² of it in the study area) lives on a dammed river: about 1,800 MW on the "
        "Douro mainstem by 1985, and the Baixo Sabor dam in service since 2016 on the next tributary east.", size=ROW_SIZE)

P2 = Column(fig, XP[1], WP, ROW_TOP)
P2.head("What the screen shows")
P2.para(f"(i) Faia Brava is {rc.faia_mosaic:.0%} good rabbit mosaic but carries little land-group current, so none "
        "of it makes the cut. The best corridors lie west of the river, on hunting land.\n"
        f"(ii) Only {n_paired} candidate pool lies within 2 km of a candidate rabbit area. H6 can be tested at one "
        "site now; testing it widely needs a larger radius or new pools.\n"
        f"(iii) {pools_in_core} candidate pools lie inside the Côa rock-art core. Turtle surveys there need the "
        "Archaeological Park's agreement.\n"
        f"(iv) {douro_overlap_ha:.0f} ha of rabbit candidate area falls inside the Alto Douro boundary. Rabbits next "
        "to vineyards is a question for growers and hunters before any release.", size=ROW_SIZE)

P2.gap(20)
P2.para("Which animals will the next chapter of the Côa include, and who decides?", size=34, prop=BOLD, colour=CORAL,
        spacing=1.2)

P3 = Column(fig, XP[2], WP, ROW_TOP)
P3.head("What we propose")
P3.para("(i) A rabbit baseline: repeated transects in the ten priority blocks, run with the hunters who already "
        f"manage rabbits on {rc.hunt_share:.0%} of the candidate area (H1, H3).\n"
        f"(ii) An August survey of the {n_cand} candidate pools before any pond turtle release; release only into "
        "permanent water and monitor for years (H4, H5).\n"
        "(iii) For the wildcat, neutering of domestic cats near villages and mesopredator monitoring alongside any "
        "rabbit release (H2).\n"
        "(iv) Add the rabbit and the pond turtle to the workflow and rerun the combined corridor (H7).\n"
        "(v) Next, a transfrontier study: extend the model into Castilla y León and Extremadura, with Spanish land "
        "cover, roads, hunting areas and records, and test whether the Côa corridors continue into Campo de Azaba, El "
        "Rebollar and Arribes del Duero.", size=ROW_SIZE)
row_bottom = min(P1.y, P2.y, P3.y)
for x in XP:
    panel_box(fig, x, ROW_TOP + 0.004, row_bottom, WP, colour=PAPER)

# ---- References at the bottom ------------------------------------------------
foot_top = 0.080
fig.add_artist(Line2D([0.03, 0.97], [foot_top + 0.006, foot_top + 0.006], transform=fig.transFigure, color=NAVY,
                      lw=2))
F = Column(fig, 0.03, 0.94, foot_top)
F.kicker("Hypotheses (Angulo Lopez, 2026a, §6)", CORAL)
F.para("H1 Rabbits follow the grazing mosaic.  H2 Wildcat habitat tracks rabbit habitat.  H3 Fire resets the rabbit "
       "mosaic, for better and worse.  H4 Water connectivity is limited by summer flow, not by barriers alone.  "
       "H5 Pond turtles persist where summer pools persist.  H6 A rabbit baseline protects the turtle.  H7 The rock-art "
       "corridor is also the best combined corridor.", size=17)
F.kicker("References and data", CORAL)
F.para(
    "Angulo Lopez, L. (2026a). Rabbits, wildcats, pond turtles and a river that stayed. Preprint, Zenodo, "
    "doi:10.5281/zenodo.22997241.  Angulo Lopez, L. (2026b). Movement, Water, Connection: a reproducible Python "
    "connectivity workflow. Preprint, Zenodo, doi:10.5281/zenodo.22979020.  Côa Valley Eco-Connectivity v6 (CCL_v6), "
    "Etalab 2.0, data.gouv.fr.  Prima, M.-C. et al. (2024). Methods in Ecology and Evolution.  Bertolero, A. and Oro, D. "
    "(2009).  ESA WorldCover 10 m 2021 v200 (Zanaga et al., 2022), CC BY 4.0.  JRC Global Surface Water v1.4 (Pekel et "
    "al., 2016, Nature 540).  HydroRIVERS v1.0 (Lehner and Grill, 2013).  NASA MODIS MCD64A1.  OpenStreetMap "
    "contributors (ODbL).  ICNF hunting zones.  DGPC classified heritage boundaries.  Natural Earth 1:10m (public domain).  EEA Natura 2000, end-2024.  UNESCO MAB, Meseta Ibérica Transboundary Biosphere Reserve (2015).  GBIF.org occurrences, "
    "generalised to 5 km.  Reis, M. (2012-2014). Inventário dos sítios da arte rupestre do Vale do Côa, Portvgalia "
    "33-35.  UNESCO World Heritage Centre, sites 866 and 1046.  Resolução do Conselho de Ministros n.º 14/1996.  "
    "Map: EPSG:3763; every figure is computed in scripts/poster.py from the v6 bundle.  Code written with AI "
    "assistance (Claude, Anthropic) from the author's method and direction, and reviewed by the author.  "
    "Linda Angulo Lopez, 2026. Text and map CC BY 4.0; plates CC BY-NC 4.0; code MIT.",
    size=14.5, spacing=1.35)
rc.band(fig, 0, 0.006, [BLUE, PURPLE, CORAL, SUN])

print(f"map block ends {body_bottom:.3f}, left flank {L.y:.3f}, right flank {R.y:.3f}; "
      f"panel row {ROW_TOP:.3f} to {row_bottom:.3f}; references start {foot_top + 0.006:.3f}, end {F.y:.3f}")
fig.savefig(OUT / "poster.pdf", facecolor=CREAM, dpi=300)  # images (plates, map grid) at 300 dpi
fig.savefig(OUT / "poster.png", facecolor=CREAM, dpi=100)
print("wrote", OUT / "poster.pdf", "and poster.png")
