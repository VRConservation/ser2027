# Zenodo deposit: SER 2027 poster

**Summary**: Field-by-field values for depositing the SER 2027 poster on Zenodo, the files to upload, and the checks to clear before and after publishing.
**Last updated**: 2026-10-25

---

**Published** on 25 October 2026 as v0.1: <https://doi.org/10.5281/zenodo.23638438>. The record names Rewilding Portugal as the affiliation, has no related works yet and lists CC BY 4.0 only. Add the related works and the CC BY-NC 4.0 entry for the plates with "Edit" on the record; metadata edits do not need a new version.

You upload and publish this yourself at <https://zenodo.org/uploads/new>. The files are ready in `deposit/`, which `.gitignore` keeps out of the repository. Rebuild it with `scripts/prepare_deposit.sh`.

## Before you publish

(i) **Reserve the DOI first.** In the upload form, under "Digital Object Identifier", answer "No" to "Do you already have a DOI?" and click "Get a DOI now!". Zenodo reserves the DOI without publishing anything. Then:
- add the DOI to the poster header, `codemeta.json` (`identifier`) and `CITATION.cff` (`doi`)
- rebuild the poster
- rerun `scripts/prepare_deposit.sh`
- upload the files from `deposit/`

The PDF then carries its own DOI.

(ii) **Timing.** Abstracts open on 3 December 2026 and close on 29 January 2027, and SER sends decisions on 15 March 2027. You can deposit now as v0.1 and add a new version after the conference, or wait for acceptance. A deposit before acceptance is fine, but don't describe it as "presented at" until it has been.

(iii) **Affiliation.** The poster names only "Côa Connectivity Lab". The preprint also names the Rewilding Academic Talent Program, Rewilding Portugal. Add it only once Rewilding Portugal agrees, in the poster author line, in `codemeta.json` and here.

(iv) **Size.** If SER asks for anything other than A0 portrait, change `FIG_W, FIG_H` in `scripts/poster.py` and rebuild.

(v) **Plates.** If scans of the hand-cut plates are ready, they replace `img/plate-*.jpg`.

(vi) **Publishing is permanent.** Files can't be changed after you publish, only replaced by a new version, and the DOI stays.

## Files to upload (from `deposit/`)

| File | What it is |
|---|---|
| `AnguloLopez_2026_SER2027_poster_v0.1.pdf` | The poster, A0 portrait, fonts embedded, images at 300 dpi. Set it as the default preview |
| `AnguloLopez_2026_SER2027_poster_v0.1_preview.png` | 100 dpi preview |
| `ser2027-v0.1-source.zip` | Snapshot of the repository at the deposited commit (code, plates, metadata) |

## Form fields

| Field | Value |
|---|---|
| Resource type | Poster |
| Title | Rabbits, wildcats, pond turtles and a free-flowing river: one open connectivity screen for trophic and hydrological rewilding in the Greater Côa Valley, Portugal |
| Publication date | The day you publish |
| Creators | Angulo Lopez, Linda. Person. ORCID 0009-0009-5689-7148. Affiliation: Côa Connectivity Lab. Role: (leave empty, creator) |
| Description | Paste `deposit/description.html` in the editor's source view, or paste the abstract from `abstract.md` as plain text |
| Licenses | Creative Commons Attribution 4.0 International (CC BY 4.0). Add a second rights entry: Creative Commons Attribution Non Commercial 4.0 International (CC BY-NC 4.0), for the plates. The description states which part is under which licence; the code is MIT, in the repository |
| Keywords and subjects | rewilding; ecological restoration; ecological connectivity; circuit theory; European rabbit; Oryctolagus cuniculus; European wildcat; Felis silvestris; pond turtle; free-flowing rivers; Natura 2000; transboundary conservation; World Heritage; Côa Valley; Portugal |
| Languages | English |
| Version | v0.1 |
| Publisher | Zenodo |
| Funding | None |

## Conference (under "Conference")

| Field | Value |
|---|---|
| Conference title | 12th World Conference on Ecological Restoration |
| Acronym | SER 2027 |
| Dates | 30 August to 3 September 2027 |
| Place | Lisbon, Portugal |
| Website | https://ser2027.org |
| Session | Lands in Motion |

## Related works

| Relation | Identifier | Scheme | Resource type |
|---|---|---|---|
| Is derived from | 10.5281/zenodo.22997241 | DOI | Publication / Preprint |
| Is derived from | 10.5281/zenodo.22979020 | DOI | Publication / Preprint |
| Is derived from | https://www.data.gouv.fr/datasets/coa-valley-eco-connectivity-v6 | URL | Dataset |
| Is supplemented by | https://github.com/coa-connectivity-lab/ser2027 | URL | Software |
| References | 10.2909/91357f39-7866-41ce-b447-43905c364ec8 | DOI | Dataset (EEA Natura 2000, end-2024) |
| References | 10.5281/zenodo.7254221 | DOI | Dataset (ESA WorldCover 2021 v200) |

## Additional description (type: Notes)

> Text, map and poster layout: CC BY 4.0. Plates (the rabbit, wildcat and pond turtle after the Iron Age fine-line engravings of the Côa): CC BY-NC 4.0. Code: MIT, https://github.com/coa-connectivity-lab/ser2027. Underlying data keep their own licences (Côa Valley Eco-Connectivity v6, Licence Ouverte 2.0; OpenStreetMap, ODbL; ESA WorldCover and HydroRIVERS, CC BY 4.0; Natura 2000, EEA; GBIF occurrences, per record). The code was written with AI assistance (Claude, Anthropic) from the author's method and direction, and reviewed by the author. These are screening maps, not release sites: every candidate needs a field survey first.

## After you publish

(i) Add the DOI, if you didn't reserve it, to the poster header, `codemeta.json`, `CITATION.cff` and the README, then push.

(ii) Add a Zenodo badge to the README.

(iii) Add a line to the knowledge base (`notes/Conservation.md`, `notes/log.md`).
