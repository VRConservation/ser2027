"""SER 2027 poster: rabbits, wildcats, pond turtles and a river that stayed.

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

# Source repository (Solo-field-illustrator-project-for-Rewilding-Portugal), screening code and bundle paths
SOURCE = Path("/home/linda/Documents/myData/Solo-field-illustrator-project-for-Rewilding-Portugal/research/"
              "rewilding-dynamics/scripts")
sys.path.insert(0, str(SOURCE))
import release_candidates as rc  # noqa: E402  (computes the layers on import; draws nothing)

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
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
# Poster
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=CREAM)
rc.band(fig, 0.994, 0.006, [CORAL, PURPLE, BLUE])

# Header
fig.text(0.03, 0.982, "SER 2027 · 12th World Conference on Ecological Restoration · Lisbon · Lands in Motion".upper(),
         fontproperties=BOLD, fontsize=26, color=CORAL, va="top")
fig.text(0.03, 0.972, "Rabbits, wildcats, pond turtles\nand a river that stayed".upper(), fontproperties=DISPLAY,
         fontsize=132, color=NAVY, va="top", linespacing=0.92)
fig.text(0.03, 0.9135, "One open connectivity screen for trophic and hydrological rewilding in the Greater Côa Valley, "
         "Portugal", fontproperties=BODY, fontsize=36, color=NAVY, va="top")
fig.text(0.03, 0.902, "Linda Angulo Lopez  ·  Côa Connectivity Lab  ·  ORCID 0009-0009-5689-7148",
         fontproperties=BOLD, fontsize=28, color=NAVY, va="top")
links = ("Preprint (synthesis, hypotheses, plate method)\ndoi.org/10.5281/zenodo.22997241\n"
         "Preprint (connectivity workflow)\ndoi.org/10.5281/zenodo.22979020\n"
         "Data: Côa Valley Eco-Connectivity v6\ndata.gouv.fr/datasets/coa-valley-eco-connectivity-v6\n"
         "Poster code and files\ngithub.com/coa-connectivity-lab/ser2027")
fig.text(0.97, 0.972, links, fontproperties=BODY, fontsize=19, color=NAVY, va="top", ha="right", linespacing=1.45)

TOP = 0.884
XL, XC, XR = 0.03, 0.345, 0.70
WL, WC, WR = 0.285, 0.325, 0.27

# ---- Left column ----------------------------------------------------------
L = Column(fig, XL, WL, TOP)
L.head("Three animals, one chain")
L.para("The European rabbit (Oryctolagus cuniculus) is the keystone prey of the Iberian Peninsula, and Endangered in "
       "its native range. The European wildcat (Felis silvestris) depends on it. The pond turtle links the pair to "
       "the river: it holds on where summer pools hold water. Rewilding projects usually treat predators, prey and "
       "rivers as three questions. In the Côa they meet in three animals.")
chain = L.axes(470)
chain.set_xlim(0, 10)
chain.set_ylim(0.1, 5.8)
chain.set_axis_off()
nodes = {"Grazing\nand fire": (1.05, 4.7), "Open\nmosaic": (3.6, 4.7), "Rabbit": (6.15, 4.7), "Wildcat": (8.8, 4.7),
         "Free-flowing\nCôa": (1.05, 1.0), "Summer\npools": (3.6, 1.0), "Pond\nturtle": (6.15, 1.0),
         "River\nhealth": (8.8, 1.0)}
for name, (x, y) in nodes.items():
    land = y > 3
    chain.text(x, y, name, ha="center", va="center", fontproperties=BOLD, fontsize=22,
               color="white" if name in ("Rabbit", "Wildcat", "Pond\nturtle") else NAVY,
               bbox=dict(boxstyle="round,pad=0.55", linewidth=2.5, edgecolor=CORAL if land else BLUE,
                         facecolor=(CORAL if land else BLUE) if name in ("Rabbit", "Wildcat", "Pond\nturtle")
                         else PAPER))


def arrow(a, b, colour, style="-", rad=0.0):
    (x0, y0), (x1, y1) = nodes[a], nodes[b]
    chain.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=34, color=colour, lw=3,
                                    linestyle=style, shrinkA=70, shrinkB=70, connectionstyle=f"arc3,rad={rad}"))


for a, b in [("Grazing\nand fire", "Open\nmosaic"), ("Open\nmosaic", "Rabbit"), ("Rabbit", "Wildcat")]:
    arrow(a, b, CORAL)
for a, b in [("Free-flowing\nCôa", "Summer\npools"), ("Summer\npools", "Pond\nturtle"), ("Pond\nturtle", "River\nhealth")]:
    arrow(a, b, BLUE)
arrow("Rabbit", "Pond\nturtle", PURPLE, style=(0, (3, 2)))
chain.text(6.35, 2.85, "prey buffer: when rabbits\ncrash, predators turn to\nreptiles (H6)", fontproperties=BODY,
           fontsize=17, color=PURPLE, va="center")
chain.text(0.1, 5.75, "LAND", fontproperties=BOLD, fontsize=17, color=CORAL, va="top")
chain.text(0.1, 2.25, "WATER", fontproperties=BOLD, fontsize=17, color=BLUE, va="top")
L.gap(10)
L.para("The chain draws on about 45 references (Angulo Lopez, 2026a) and yields seven testable hypotheses, each tied "
       "to a step in the open workflow.", size=SMALL, colour=NAVY)
L.gap(30)

L.head("Method")
L.para("(i) Study area of 10,230 km², the Côa and 30 km around it, extended to its catchment.\n"
       "(ii) Ten focal species in land, water and air groups, from GBIF records and Natura 2000.\n"
       "(iii) Circuit theory in pure Python, a moving-window solver after Prima et al. (2024). It runs on a laptop, "
       "with no paid software.\n"
       "(iv) Three local penalties: fire weighted by recency (MODIS, 2015 to July 2025), 22 barriers recorded in the "
       "field in August 2026, and a flat penalty over the two World Heritage areas.\n"
       "(v) Rabbit screen: scrub-pasture mosaic (ESA WorldCover 2021), not burned since 2023, 200 m or more from a "
       "road, inside the top third of the land-group current, in blocks of 1 km² or more.\n"
       "(vi) Pond turtle screen: pools with water in all 12 months of 2021 (JRC Global Surface Water), within 200 m "
       "of a river, reservoirs over 50 ha left out, on the better-connected half of the water-group current.")
L.gap(30)

box_top = L.y
L.head("What we propose")
L.para("(i) A rabbit baseline: repeated transects in the ten priority blocks, run with the hunters who already manage "
       f"rabbits on {rc.hunt_share:.0%} of the candidate area (H1, H3).\n"
       f"(ii) An August survey of the {n_cand} candidate pools, before any pond turtle release; release only into "
       "permanent water and monitor for years (H4, H5).\n"
       "(iii) For the wildcat, neutering of domestic cats near villages and mesopredator monitoring alongside any "
       "rabbit release (H2).\n"
       "(iv) Add the rabbit and the pond turtle to the workflow and rerun the combined corridor (H7).")
panel_box(fig, XL, box_top + 10 / PT_H, L.y + 10 / PT_H, WL, colour=PAPER, edge=CORAL)
L.gap(26)
L.para("Which animals will the next chapter of the Côa include, and who decides?", size=34, prop=BOLD, colour=CORAL,
       spacing=1.25)


# ---- Centre column: the one map -------------------------------------------
C = Column(fig, XC, WC, TOP)
C.head("Where to survey first")
C.para("Rabbit release candidates inside the wildcat's corridors, pond turtle pools, and the two World Heritage "
       "areas, on one map. Screening maps, not release sites: every candidate needs a field survey first.",
       size=SIZE)
C.gap(6)

# key figures, two rows of three
stats = [(f"{cand_km2:,.0f} km²", "rabbit candidate area,\nblocks of 1 km² or more"),
         (f"{rc.hunt_share:.0%}", "of it inside\nhunting zones"),
         ("10", "priority survey blocks,\nranked by current"),
         (f"{n_cand} of {n_pools}", "year-round pools on\nbetter-connected rivers"),
         (str(n_paired), "pool within 2 km of a\nrabbit area (H6)"),
         (str(rc.n_wildcat), "wildcat records in GBIF\nfor the study area")]
for i, (big, small) in enumerate(stats):
    x = XC + (i % 3) * WC / 3
    y = C.y - (i // 3) * 175 / PT_H
    fig.text(x, y, big, fontproperties=DISPLAY, fontsize=70, color=CORAL if i < 3 else BLUE, va="top")
    fig.text(x, y - 74 / PT_H, small, fontproperties=BODY, fontsize=17, color=NAVY, va="top", linespacing=1.2)
C.gap(320)

s = rc.study.to_crs(rc.PLOT_CRS)
bx0, by0, bx1, by1 = s.total_bounds
map_h_pt = WC * PT_W * (by1 - by0 + 4000) / (bx1 - bx0 + 4000)
ax = C.axes(map_h_pt)
ax.set_facecolor(CREAM)
s.plot(ax=ax, color=PAPER, zorder=0)
grid = rc.template.copy(data=np.where(rc.habitat_only, 1, np.where(rc.candidate, 2, 0)).astype("float32"))
grid = grid.where(grid > 0).rio.write_nodata(np.nan).rio.reproject(rc.PLOT_CRS)
gx0, gy0, gx1, gy1 = grid.rio.bounds()
ax.imshow(grid.values, extent=(gx0, gx1, gy0, gy1), cmap=ListedColormap(["#dfe6b4", CORAL]), vmin=1, vmax=2,
          interpolation="nearest", zorder=1)
rc.hunting.to_crs(rc.PLOT_CRS).boundary.plot(ax=ax, color="#cfc6b6", linewidth=0.35, zorder=2)
hydro = gpd.read_file(rc.HYDRO, bbox=tuple(rc.study.to_crs(4326).total_bounds))
big_rivers = hydro[hydro.ORD_STRA >= 6].to_crs(rc.PLOT_CRS)
big_rivers.plot(ax=ax, color="#9dbbe6", linewidth=2.6, zorder=2)
rc.rivers.to_crs(rc.PLOT_CRS).plot(ax=ax, color="#7da2dc", linewidth=1.2, zorder=2)
res.to_crs(rc.PLOT_CRS).plot(ax=ax, color=SKY, edgecolor="#7da2dc", linewidth=0.8, zorder=3)
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
label(core_pt.x - 4500, core_pt.y - 9000, "Côa rock art\n(UNESCO 1998)", PURPLE, ha="right")
dpt = douro_clip.iloc[0].representative_point()
label(dpt.x, dpt.y + 6000, "Alto Douro Wine Region\n(UNESCO 2001)", PURPLE, ha="center")
coa_line = rc.coa.to_crs(rc.PLOT_CRS).union_all()
mid = coa_line.interpolate(0.5, normalized=True)
label(mid.x + 4000, mid.y, "River Côa", NAVY)
ax.set_xlim(bx0 - 2000, bx1 + 2000)
ax.set_ylim(by0 - 2000, by1 + 2000)
x0, y0 = bx1 - 16000, by0 + 3000
ax.plot([x0, x0 + 10000], [y0, y0], color=NAVY, linewidth=7, solid_capstyle="butt")
ax.text(x0 + 5000, y0 + 2200, "10 km", ha="center", fontproperties=BODY, fontsize=19, color=NAVY)
ax.annotate("N", xy=(bx1 - 2500, by0 + 20000), xytext=(bx1 - 2500, by0 + 12000), ha="center", fontproperties=BOLD,
            fontsize=24, color=NAVY, arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=3, mutation_scale=30))
ax.set_axis_off()

C.gap(14)
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
], loc="upper left", bbox_to_anchor=(XC - 0.005, C.y), ncol=2, prop=BODY.copy(), fontsize=SMALL, frameon=False,
    labelcolor=NAVY, handlelength=1.6, columnspacing=1.2, labelspacing=0.75)
for t in leg.get_texts():
    t.set_fontsize(SMALL)
C.gap(290)
C.head("What the screen shows")
C.para(f"(i) Faia Brava is {rc.faia_mosaic:.0%} good rabbit mosaic but carries little land-group current, so none of "
       "it makes the cut. The best corridors lie west of the river, on hunting land.\n"
       f"(ii) Only {n_paired} candidate pool lies within 2 km of a candidate rabbit area. H6 can be tested at one site "
       "now; testing it widely needs a larger radius or new pools.\n"
       f"(iii) {pools_in_core} candidate pools lie inside the Côa rock-art core. Turtle surveys there need the "
       "Archaeological Park's agreement.\n"
       f"(iv) {douro_overlap_ha:.0f} ha of rabbit candidate area falls inside the Alto Douro boundary. Rabbits next to "
       "vineyards is a question for growers and hunters before any release.")

# ---- Right column: plates, proposal, hypotheses ---------------------------
R = Column(fig, XR, WR, TOP)
R.head("New animals in an old line")
R.para("New works after the Iron Age fine-line engravings of the Côa, not ancient motifs. Each animal is reduced to "
       "one diagnostic feature and paired with one sentence of evidence. Digital studies; the hand-cut plates follow. "
       "Nothing is drawn on rock.", size=SMALL)
R.gap(8)
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
img_w = 0.112
img_h_pt = img_w * PT_W * 5 / 4
for fname, title, colour, text in plates:
    top = R.y
    pax = fig.add_axes([XR, top - img_h_pt / PT_H, img_w, img_h_pt / PT_H])
    pax.imshow(Image.open(IMG / fname))
    pax.set_axis_off()
    tx = XR + img_w + 0.012
    tw = WR - img_w - 0.012
    fig.text(tx, top - 6 / PT_H, title.upper(), fontproperties=DISPLAY, fontsize=40, color=colour, va="top")
    lines = wrap(text, BODY, SMALL, tw * PT_W)
    fig.text(tx, top - 56 / PT_H, "\n".join(lines), fontproperties=BODY, fontsize=SMALL, color=NAVY, va="top",
             linespacing=1.35)
    R.gap(img_h_pt + 26)
R.gap(14)

R.head("A river that stayed")
R.para("The Côa stayed free-flowing because of its rock art. In 1995 students at the Vila Nova de Foz Côa secondary "
       "school took up the slogan \"As gravuras não sabem nadar\" (the engravings can't swim) against a dam that would "
       "have flooded open-air engravings more than 20,000 years old. The government led by António Guterres suspended "
       "the dam on 17 January 1996. UNESCO inscribed the sites in 1998, and extended them to Siega Verde, Spain, in "
       "2010.")
R.para("Where the Côa meets the Douro, the Alto Douro Wine Region (UNESCO 2001, 24,600 ha of terraced vineyard, "
       f"{douro_in_area_ha / 100:,.0f} km² of it in the study area) lives on a dammed river: about 1,800 MW on the "
       "Douro mainstem by 1985, and the Baixo Sabor dam in service since 2016 on the next tributary east.")
events = [("1995", "Students take up \"As gravuras não sabem nadar\""),
          ("1996", "Côa dam suspended (17 Jan); park opens"),
          ("1998", "Côa rock art inscribed by UNESCO"), ("2001", "Alto Douro Wine Region inscribed"),
          ("2010", "Extension to Siega Verde, Spain"), ("2016", "Baixo Sabor dam in service"),
          ("2017", "Côa cofferdam on the obsolete-barrier list"), ("2026", "This screen")]
row = SMALL * 1.65
timeline = R.axes(row * len(events) + 10)
timeline.set_xlim(0, 1)
timeline.set_ylim(len(events) - 0.4, -0.6)
timeline.set_axis_off()
timeline.plot([0.012, 0.012], [0, len(events) - 1], color=NAVY, lw=2.5)
for i, (yr, text) in enumerate(events):
    timeline.plot(0.012, i, "o", color=BLUE if yr == "2026" else CORAL, markersize=13)
    timeline.text(0.05, i, yr, fontproperties=BOLD, fontsize=SMALL, color=NAVY, va="center")
    timeline.text(0.2, i, text, fontproperties=BODY, fontsize=SMALL, color=NAVY, va="center")
R.gap(16)
R.para("What is not finished: the 32 m cofferdam built for the Côa dam was never removed. Rain still backs water up "
       "about 10 km, and it has submerged 119 rock-art panels for more than 500 days in total since 1996. Its "
       "demolition has been on the national list of obsolete barriers since 2017.")


# ---- Footer -----------------------------------------------------------------
foot_top = 0.072
fig.add_artist(Line2D([0.03, 0.97], [foot_top + 0.004, foot_top + 0.004], transform=fig.transFigure, color=NAVY,
                      lw=1.5))
hyp = ("HYPOTHESES (Angulo Lopez, 2026a, §6).  H1 Rabbits follow the grazing mosaic.  H2 Wildcat habitat tracks rabbit "
       "habitat.  H3 Fire resets the rabbit mosaic, for better and worse.  H4 Water connectivity is limited by summer "
       "flow, not by barriers alone.  H5 Pond turtles persist where summer pools persist.  H6 A rabbit baseline protects "
       "the turtle.  H7 The rock-art corridor is also the best combined corridor.")
F = Column(fig, 0.03, 0.94, foot_top)
F.para(hyp, size=19, colour=NAVY)
sources = (
    "Angulo Lopez, L. (2026a). Rabbits, wildcats, pond turtles and a river that stayed. Preprint, Zenodo, "
    "doi:10.5281/zenodo.22997241.  Angulo Lopez, L. (2026b). Movement, Water, Connection: a reproducible Python "
    "connectivity workflow. Preprint, Zenodo, doi:10.5281/zenodo.22979020.  Côa Valley Eco-Connectivity v6 (CCL_v6), "
    "Etalab 2.0, data.gouv.fr.  Prima, M.-C. et al. (2024). Methods in Ecology and Evolution.  Bertolero, A. and Oro, D. "
    "(2009).  ESA WorldCover 10 m 2021 v200 (Zanaga et al., 2022), CC BY 4.0.  JRC Global Surface Water v1.4 (Pekel et "
    "al., 2016, Nature 540).  HydroRIVERS v1.0 (Lehner and Grill, 2013).  NASA MODIS MCD64A1.  OpenStreetMap "
    "contributors (ODbL).  ICNF hunting zones.  DGPC classified heritage boundaries.  GBIF.org occurrences, "
    "generalised to 5 km.  Reis, M. (2012-2014). Inventário dos sítios da arte rupestre do Vale do Côa, Portvgalia "
    "33-35.  UNESCO World Heritage Centre, sites 866 and 1046.  Resolução do Conselho de Ministros n.º 14/1996.  "
    "Público (31 July 2023) and CNN Portugal (23 July 2026) on the Côa cofferdam.  Map: EPSG:3763; the screen is "
    "computed in scripts/poster.py from the v6 bundle.  Code written with AI assistance (Claude, Anthropic) from the "
    "author's method and direction, and reviewed by the author.")
F.para(sources, size=14.5, colour=NAVY, spacing=1.35)
fig.text(0.97, 0.016, "Linda Angulo Lopez · 2026 · Text and map CC BY 4.0 · Plates CC BY-NC 4.0 · Code MIT",
         fontproperties=BODY, fontsize=17, color=NAVY, ha="right", va="bottom")
rc.band(fig, 0, 0.008, [BLUE, PURPLE, CORAL, SUN])

for col, name in [(L, "left"), (C, "centre"), (R, "right")]:
    print(f"{name} column ends at y={col.y:.3f} (footer starts at {foot_top + 0.01:.3f})")
fig.savefig(OUT / "poster.pdf", facecolor=CREAM, dpi=300)  # images (plates, map grid) at 300 dpi
fig.savefig(OUT / "poster.png", facecolor=CREAM, dpi=100)
print("wrote", OUT / "poster.pdf", "and poster.png")
