> **Pre-registration v2: rationale addendum (Owner decision D-63, 26 Nov 2026).** Recorded before any reporting-camera or test result exists. It corrects the stated reasons for v2 values after a literature review (`reports/v2_parameter_rationale_2026-11-26.md`, Architect project document). **No value, grid, rule, label, criterion or reference changes.** Where this addendum and §4 of `preregistration_v2_FROZEN.md` differ on a *reason*, this addendum applies; on any *value*, the frozen file applies.
>
> 1. **ttc_max 1.5 s.** The 1.5 s cutoff comes from road-intersection conflict research. van der Horst (1990) and FHWA-RD-03-050 (Gettman & Head 2003) justify it by low intersection speeds, not by reaction time. Linking it to one perception–reaction time is this study's own interpretation; driver reaction-time studies support that interpretation separately (Green 2000; Lerner 1993; Olson & Sivak 1986). No study has validated a TTC threshold for forklift–pedestrian encounters. One pedestrian calibration found 2.7 s fitted best (Wu et al. 2017).
> 2. **The 1.5 s anchor** is a *typical* surprise-event reaction time, not a conservative one. The 85th–95th percentiles are about 1.6–2.0 s, and the highway design value is 2.5 s (AASHTO). Markkula et al. (2016) argue against any fixed reaction time.
> 3. **pet_max 1.5 s** lies within the published band for *critical* pedestrian conflicts, about 1.2–1.7 s. Screening definitions of any conflict use 3–8 s.
> 4. **t_min 0.2 s** is a typical simple reaction time (about 0.21–0.23 s; Woods et al. 2015), not the fastest. It works as a debounce against detection flicker.
> 5. **d_pc 1.0 m.** An adult *step* is about 0.67–0.69 m and a *stride* (two steps) about 1.38 m, so 1.0 m is about 1.5 steps. The "one stride" wording in §4 is wrong.
> 6. **Walking pace.** 1.4–1.5 m/s is the brisk end of normal walking; usual pace is about 1.31 m/s (Murtagh et al. 2020).
> 7. **d_p 3.0 m.** The WorkSafe Victoria 3 m exclusion zone applies to a forklift travelling at walking pace *with the load lowered*. For raised loads it is mast and load height plus 3 m, which is relevant to future E2 work. With a 1.5 s reaction time, 3 m covers the stopping distance up to about 1.7 m/s; with 2.5 s it would need about 4 m.
> 8. **NZTA forklift brake rule** (stop within 4 m from 20 km/h, unladen): verified from a search snippet only. The page could not be retrieved.
> 9. **"1.15 s" data-derived TTC threshold** (Singh et al. 2024): known only from a secondary citation (arXiv:2611.04988).
> 10. **The "half the threshold" accuracy rule (GV-01, GV-07)** is a minimum feasibility floor. It is looser than metrology practice (a test uncertainty ratio of 4:1; NASA-HDBK-8739.19-4, ANSI/NCSL Z540.3). With k_σ = 2, an RMSE equal to the target makes the expanded uncertainty as large as the whole threshold.
> 11. **iou_m 0.3 / 0.5 / 0.7** matches the standard THUMOS14 evaluation range. The "unsourced convention" label in §4 is replaced.
> 12. **Person footprint r 0.30 m** is consistent with pedestrian-simulation body sizes (Helbing, Farkas & Vicsek 2000: diameters 0.5–0.7 m).
>
> **Unverified, to be checked or stated as limitations:**
> - whether the dataset forklift boxes include the forks (if not, clearance at the fork end is overstated by up to about 1.1 m);
> - ISO 3691, ISO 6292, ANSI B56.1 and HSE L117 texts (not inspected);
> - SSAM default values (not inspected).
>
> **Also recorded under D-63:**
> - T25.2 is inert under v2;
> - the selected stitching gap T_s = 5 s is at the top of its grid;
> - g_max means 1.5 s (CR-038);
> - SmartSpaces event-level results are excluded from this submission (CR-039).
