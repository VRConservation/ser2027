# Zenodo upload: values for the form

**Summary**: Field values for depositing the SER 2027 poster on Zenodo, and the checks to clear first.
**Last updated**: 2026-10-25

---

You upload this yourself at <https://zenodo.org/uploads/new>.

## Before you deposit

(i) Decide whether to wait for the SER acceptance (15 March 2027) or deposit now as v0.1 and add a new version after the conference.

(ii) Confirm the affiliation line. The poster shows only "Côa Connectivity Lab". The preprint also names the Rewilding Academic Talent Program, Rewilding Portugal. Add it back to the author line in `scripts/poster.py` only once Rewilding Portugal agrees.

(iii) If SER publishes a poster size other than A0 portrait, change `FIG_W, FIG_H` in `scripts/poster.py` and rebuild.

(iv) Scans of the hand-cut plates replace `img/plate-*.jpg` when ready.

(v) After deposit, add the poster DOI to the header links in `scripts/poster.py` and to `CITATION.cff`, then rebuild and publish a new version.

## Files to upload

(i) `poster/poster.pdf` (main file, A0). (ii) `poster/poster.png` (preview). (iii) Optional: a zip of the GitHub release, so the code is archived with the poster.

## Form fields

| Field | Value |
|---|---|
| Resource type | Poster |
| Title | Rabbits, wildcats, pond turtles and a river that stayed: one open connectivity screen for trophic and hydrological rewilding in the Greater Côa Valley, Portugal |
| Creator | Angulo Lopez, Linda. Affiliation: Côa Connectivity Lab. ORCID: 0009-0009-5689-7148 |
| Description | The abstract in `abstract.md` |
| Licence | CC BY 4.0 (text and map). Add to the description: "Plates CC BY-NC 4.0; code MIT, github.com/coa-connectivity-lab/ser2027" |
| Keywords | rewilding; European rabbit; European wildcat; pond turtle; ecological connectivity; circuit theory; free-flowing rivers; World Heritage; Côa Valley; Portugal |
| Conference | 12th SER World Conference on Ecological Restoration (SER 2027), Lisbon, Portugal, 30 August to 3 September 2027. Session: Lands in Motion |
| Version | v0.1 |
| Language | English |

## Related works

| Relation | Identifier | Type |
|---|---|---|
| Is supplemented by | 10.5281/zenodo.22997241 | Preprint (synthesis, hypotheses, plate method) |
| Is supplemented by | 10.5281/zenodo.22979020 | Preprint (connectivity workflow) |
| Is derived from | https://www.data.gouv.fr/datasets/coa-valley-eco-connectivity-v6 | Dataset |
| Is supplemented by | https://github.com/coa-connectivity-lab/ser2027 | Software |
