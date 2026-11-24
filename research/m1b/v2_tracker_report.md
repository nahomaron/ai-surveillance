# D-55 tracker selection (v2 detector + tracker package)

Status: tuning subset, synthetic SDG, selection evidence, not a reported result. Selected under D-55, **not frozen** (frozen later in pre-registration v2). Contract E-1.2.24 unchanged (artifact schema bundle E-1.2.21, as the pilot).

No event evaluation of any kind: no S4, S5 or S8 run and no EV metric. Tuning cameras only (116; 54 ceiling, 62 eye-level); nothing on the 110 reporting cameras or the test partition. Detector as frozen in D-45 (YOLO-World v2-s, person 0.20, forklift 0.05). Columns A, B, C and C′ unchanged.

## Summary (plain language)

- Forklift coverage by tracked points: column C settings 0.160, selected package 0.593.
- Forklift IDF1: column C 0.250, package 0.774. Person IDF1 is unchanged (0.846): the person tracker is the same.
- The package is ByteTrack (T1). T1 winner `trc_7flfpx52d2siiljxkqwcorr7nz`, T2 winner `trc_iwm5ndlac27qun2gouwrtoroun`. BoT-SORT did not win.
- Fragmentation remains: package 1.062 tracks per covered forklift identity (7 of 112 covered identities have two or more), column C 1.485 (26 of 66).
- T1 vs T2 winners: IDF1 0.774 vs 0.775 (both in the band); decided at `coverage`: matched forklift references 19981 vs 19980 of 33677, a margin of 1 reference frame(s).
- Under the secondary reading (tracked and predicted points) the same rule selects `trc_iwm5ndlac27qun2gouwrtoroun` (a different package; see CR-033 item 2).
- These are tracking measures on synthetic SDG tuning cameras: selection evidence, not a reported result, nothing validated.

## Selected package

Configuration ID `trc_7flfpx52d2siiljxkqwcorr7nz` (S3 tracker configuration ID, F.1 A1.2 configuration class).

| class | tracker | parameter | value |
|---|---|---|---|
| person | BYTETracker (`bytetrack`) | fuse_score | `true` |
| person | BYTETracker (`bytetrack`) | match_thresh | `0.8` |
| person | BYTETracker (`bytetrack`) | new_track_thresh | `0.25` |
| person | BYTETracker (`bytetrack`) | track_buffer | `30` |
| person | BYTETracker (`bytetrack`) | track_high_thresh | `0.25` |
| person | BYTETracker (`bytetrack`) | track_low_thresh | `0.1` |
| person | BYTETracker (`bytetrack`) | tracker_type | `"bytetrack"` |
| forklift | BYTETracker (`bytetrack`) | fuse_score | `false` |
| forklift | BYTETracker (`bytetrack`) | match_thresh | `0.8` |
| forklift | BYTETracker (`bytetrack`) | new_track_thresh | `0.05` |
| forklift | BYTETracker (`bytetrack`) | track_buffer | `90` |
| forklift | BYTETracker (`bytetrack`) | track_high_thresh | `0.05` |
| forklift | BYTETracker (`bytetrack`) | track_low_thresh | `0.05` |
| forklift | BYTETracker (`bytetrack`) | tracker_type | `"bytetrack"` |

Bridging g_max 15 (frozen v1), tracked box = detection box (AR-62 item 3), NumPy assignment path (AR-62 item 5).

## Selection (STEP 5)

Rule as approved: guards precision ≥ 0.95 and person IDF1 ≥ column C's (0.846); band 0.01 below the best forklift IDF1; then coverage, fragments per identity, parameters changed from the installed defaults, configuration ID. Primary reading (CR-033 item 2).

- **T1** (36 of 36 passed the guards): best IDF1 0.774 (`trc_7flfpx52d2siiljxkqwcorr7nz`); band ≥ 0.764: 2 configurations; path: coverage → 1; winner `trc_7flfpx52d2siiljxkqwcorr7nz`.
- **T2** (36 of 36 passed the guards): best IDF1 0.775 (`trc_iwm5ndlac27qun2gouwrtoroun`); band ≥ 0.765: 2 configurations; path: coverage → 1; winner `trc_iwm5ndlac27qun2gouwrtoroun`.
- **package**: best IDF1 0.775 (`trc_iwm5ndlac27qun2gouwrtoroun`); band ≥ 0.765: 2 configurations; path: coverage → 1; winner `trc_7flfpx52d2siiljxkqwcorr7nz`.

Guard failures: 0 of 72 configurations (precision: 0; person IDF1: 0). Per-configuration guard results: `v2_tracker_selection.json`.

## Grid (STEP 4), all 116 tuning cameras

IDF1 F / P: forklift / person IDF1 (TrackEval port, iou_cm 0.5, pooled IDTP/IDFP/IDFN). Coverage, precision and frag/id: primary reading, probe matcher IoU ≥ 0.3 on clipped reference-visible boxes. Counts: tracks started, predicted points, bridged gaps.

| config_id | fam | high/new | fuse | buffer | IDF1 F | coverage | precision | frag/id | IDF1 P | tracks | predicted | bridged | changed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `trc_i4ljlcifrwgephzz4cgjkmo5ej` | C | 0.25/0.25 | true | 30 | 0.250 | 0.160 | 1.000 | 1.485 | 0.846 | 98 | 334 | 47 | 0 |
| `trc_i6inovdhm2s36jvamfha2znokd` | T1 | 0.05/0.05 | true | 30 | 0.227 | 0.121 | 1.000 | 1.625 | 0.846 | 132 | 1110 | 344 | 3 |
| `trc_q4f7jjd7xqj6e5aogdzz4fjkyi` | T1 | 0.05/0.05 | true | 60 | 0.238 | 0.121 | 1.000 | 1.525 | 0.846 | 124 | 1118 | 346 | 4 |
| `trc_iptyuhjlprod37xvlyzaha4o3t` | T1 | 0.05/0.05 | true | 90 | 0.239 | 0.121 | 1.000 | 1.500 | 0.846 | 122 | 1117 | 347 | 4 |
| `trc_thdqorfetvz5tlekusjw2fzr3d` | T1 | 0.05/0.05 | false | 30 | 0.742 | 0.592 | 0.979 | 1.286 | 0.846 | 151 | 2833 | 955 | 4 |
| `trc_ty7xfe4xyzwyawowk5jsl25bth` | T1 | 0.05/0.05 | false | 60 | 0.771 | 0.593 | 0.979 | 1.080 | 0.846 | 126 | 2878 | 968 | 5 |
| `trc_7flfpx52d2siiljxkqwcorr7nz` | T1 | 0.05/0.05 | false | 90 | 0.774 | 0.593 | 0.979 | 1.062 | 0.846 | 123 | 2878 | 968 | 5 |
| `trc_jhbd3n3roq5eb5zlbachmwaznd` | T1 | 0.05/0.1 | true | 30 | 0.226 | 0.120 | 1.000 | 1.616 | 0.846 | 118 | 1087 | 339 | 3 |
| `trc_7ecoxlkmmpwa7nju6fokbstl3p` | T1 | 0.05/0.1 | true | 60 | 0.236 | 0.120 | 1.000 | 1.507 | 0.846 | 110 | 1095 | 341 | 4 |
| `trc_56r4lhbccvvj42iluzhb3742zh` | T1 | 0.05/0.1 | true | 90 | 0.237 | 0.121 | 1.000 | 1.479 | 0.846 | 108 | 1094 | 342 | 4 |
| `trc_tzcxbdgfqq2iwmveqinwaoq2dz` | T1 | 0.05/0.1 | false | 30 | 0.734 | 0.558 | 0.994 | 1.124 | 0.846 | 119 | 2098 | 729 | 4 |
| `trc_ymh7canszduw3ehnzu2loheade` | T1 | 0.05/0.1 | false | 60 | 0.752 | 0.566 | 0.994 | 1.029 | 0.846 | 109 | 2177 | 756 | 5 |
| `trc_szpvvuexivjl5bl2wvji7cujm6` | T1 | 0.05/0.1 | false | 90 | 0.755 | 0.566 | 0.994 | 1.019 | 0.846 | 108 | 2177 | 756 | 5 |
| `trc_opkceesi7bntbkvtk3e3nmlunz` | T1 | 0.05/0.25 | true | 30 | 0.215 | 0.115 | 1.000 | 1.530 | 0.846 | 101 | 916 | 292 | 2 |
| `trc_rurkfeuk7hlzv4hmhtpey5njb6` | T1 | 0.05/0.25 | true | 60 | 0.224 | 0.115 | 1.000 | 1.470 | 0.846 | 97 | 927 | 297 | 3 |
| `trc_bcyg7lfluv75l4imauxapzt32d` | T1 | 0.05/0.25 | true | 90 | 0.225 | 0.116 | 1.000 | 1.455 | 0.846 | 96 | 927 | 299 | 3 |
| `trc_omlp2gnep3xrljhnriytvjcy2b` | T1 | 0.05/0.25 | false | 30 | 0.601 | 0.406 | 1.000 | 1.012 | 0.846 | 84 | 965 | 347 | 3 |
| `trc_otjx7ewwcdinggj5kq4wo2jpxp` | T1 | 0.05/0.25 | false | 60 | 0.607 | 0.412 | 1.000 | 1.012 | 0.846 | 84 | 972 | 353 | 4 |
| `trc_4sqebhcej3snnwoft3vseratdp` | T1 | 0.05/0.25 | false | 90 | 0.607 | 0.412 | 1.000 | 1.012 | 0.846 | 84 | 972 | 353 | 4 |
| `trc_rprnecxj22fh3uqry6hovthhy3` | T1 | 0.1/0.1 | true | 30 | 0.223 | 0.121 | 1.000 | 1.644 | 0.846 | 120 | 1071 | 337 | 3 |
| `trc_6swarrsbbxpitt46xpsrxzjgot` | T1 | 0.1/0.1 | true | 60 | 0.232 | 0.121 | 1.000 | 1.548 | 0.846 | 113 | 1072 | 337 | 4 |
| `trc_mpkoyfsbsccwbclp44xjmwbp37` | T1 | 0.1/0.1 | true | 90 | 0.232 | 0.121 | 1.000 | 1.534 | 0.846 | 112 | 1071 | 336 | 4 |
| `trc_tzp4lgbqkwqqpkfhndzeak7xpv` | T1 | 0.1/0.1 | false | 30 | 0.639 | 0.485 | 1.000 | 1.340 | 0.846 | 138 | 1425 | 231 | 4 |
| `trc_zkhhdt2wbjqvyq3d75row3z6rj` | T1 | 0.1/0.1 | false | 60 | 0.673 | 0.487 | 1.000 | 1.126 | 0.846 | 116 | 1451 | 236 | 5 |
| `trc_57amvce2wbtzkvsve7vlz4ouux` | T1 | 0.1/0.1 | false | 90 | 0.682 | 0.487 | 1.000 | 1.078 | 0.846 | 111 | 1451 | 236 | 5 |
| `trc_esfnz7sdckzxcqnyprk5idbjr3` | T1 | 0.1/0.25 | true | 30 | 0.212 | 0.115 | 1.000 | 1.576 | 0.846 | 104 | 916 | 291 | 2 |
| `trc_gap6fq4qmi5x3nf3eoj7ore62t` | T1 | 0.1/0.25 | true | 60 | 0.220 | 0.116 | 1.000 | 1.500 | 0.846 | 99 | 920 | 294 | 3 |
| `trc_fpsjioulywcag7hw6i2z24bjg7` | T1 | 0.1/0.25 | true | 90 | 0.221 | 0.116 | 1.000 | 1.500 | 0.846 | 99 | 920 | 294 | 3 |
| `trc_i7l6anybs45d4uaggxhl3rjzh4` | T1 | 0.1/0.25 | false | 30 | 0.545 | 0.365 | 1.000 | 1.072 | 0.846 | 89 | 829 | 139 | 3 |
| `trc_66qro5wri5n4p45el5xqge6cbg` | T1 | 0.1/0.25 | false | 60 | 0.567 | 0.378 | 1.000 | 1.024 | 0.846 | 85 | 865 | 146 | 4 |
| `trc_7n3saxjbtiehw55yuvu6lpnn3n` | T1 | 0.1/0.25 | false | 90 | 0.575 | 0.380 | 1.000 | 1.000 | 0.846 | 83 | 865 | 146 | 4 |
| `trc_7wsw2iclhmh7qddej3p6nl7eam` | T1 | 0.25/0.25 | true | 30 | 0.329 | 0.217 | 1.000 | 1.439 | 0.846 | 95 | 161 | 24 | 1 |
| `trc_w4bwtsfabqk6kf5sjxc77csduo` | T1 | 0.25/0.25 | true | 60 | 0.339 | 0.223 | 1.000 | 1.364 | 0.846 | 90 | 161 | 24 | 2 |
| `trc_sxnrsqt5ussetdwyvx6daleikf` | T1 | 0.25/0.25 | true | 90 | 0.342 | 0.223 | 1.000 | 1.348 | 0.846 | 89 | 161 | 24 | 2 |
| `trc_fkywz4gq4fo5qlg46ac6lovy7m` | T1 | 0.25/0.25 | false | 30 | 0.396 | 0.260 | 1.000 | 1.240 | 0.846 | 93 | 212 | 26 | 2 |
| `trc_vywoqxr6ys2ev5jxyuu4mlzrq5` | T1 | 0.25/0.25 | false | 60 | 0.410 | 0.262 | 1.000 | 1.120 | 0.846 | 84 | 212 | 26 | 3 |
| `trc_hkx3gos7rj6keeoazv6c4zpw4c` | T1 | 0.25/0.25 | false | 90 | 0.417 | 0.263 | 1.000 | 1.067 | 0.846 | 80 | 212 | 26 | 3 |
| `trc_bo2nrse7haxr3qsmqccu4vzi7q` | T2 | 0.05/0.05 | true | 30 | 0.234 | 0.127 | 1.000 | 1.562 | 0.846 | 127 | 1124 | 345 | 4 |
| `trc_5rafgrfmh7yq24md5oj2tgzab6` | T2 | 0.05/0.05 | true | 60 | 0.243 | 0.128 | 1.000 | 1.475 | 0.846 | 120 | 1133 | 350 | 5 |
| `trc_kdi65wy3zqxrlippd5htqu63ge` | T2 | 0.05/0.05 | true | 90 | 0.244 | 0.128 | 1.000 | 1.450 | 0.846 | 118 | 1133 | 352 | 5 |
| `trc_yd3pf63froggbg5qso24my4xjt` | T2 | 0.05/0.05 | false | 30 | 0.742 | 0.592 | 0.979 | 1.286 | 0.846 | 151 | 2820 | 953 | 5 |
| `trc_fqxlvtw3jqab2lzk3j3vbc7pwx` | T2 | 0.05/0.05 | false | 60 | 0.772 | 0.593 | 0.979 | 1.080 | 0.846 | 126 | 2865 | 966 | 6 |
| `trc_iwm5ndlac27qun2gouwrtoroun` | T2 | 0.05/0.05 | false | 90 | 0.775 | 0.593 | 0.979 | 1.062 | 0.846 | 123 | 2865 | 966 | 6 |
| `trc_hlhqp4zcm5kfzn6xue5hk5cnuk` | T2 | 0.05/0.1 | true | 30 | 0.233 | 0.126 | 1.000 | 1.548 | 0.846 | 113 | 1101 | 337 | 4 |
| `trc_5tgiem2xes7keizbo44uy6igu2` | T2 | 0.05/0.1 | true | 60 | 0.242 | 0.127 | 1.000 | 1.452 | 0.846 | 106 | 1110 | 342 | 5 |
| `trc_gvbqokhg633qfqipwo2reyadej` | T2 | 0.05/0.1 | true | 90 | 0.243 | 0.127 | 1.000 | 1.425 | 0.846 | 104 | 1110 | 344 | 5 |
| `trc_xe6irqxylqxyopypzlp4b3bttg` | T2 | 0.05/0.1 | false | 30 | 0.734 | 0.558 | 0.994 | 1.124 | 0.846 | 119 | 2098 | 729 | 5 |
| `trc_74xioyvkakr5yn5lruvrtobmel` | T2 | 0.05/0.1 | false | 60 | 0.752 | 0.566 | 0.994 | 1.029 | 0.846 | 109 | 2177 | 756 | 6 |
| `trc_sh6pgy4hrct4o54bifyrzvhfyx` | T2 | 0.05/0.1 | false | 90 | 0.755 | 0.566 | 0.994 | 1.019 | 0.846 | 108 | 2177 | 756 | 6 |
| `trc_5ogeizg475eftefrdz3he6q6mp` | T2 | 0.05/0.25 | true | 30 | 0.223 | 0.121 | 1.000 | 1.455 | 0.846 | 96 | 919 | 294 | 3 |
| `trc_ebqvyr6ixfcit3vax3j5rs7qp2` | T2 | 0.05/0.25 | true | 60 | 0.231 | 0.122 | 1.000 | 1.409 | 0.846 | 93 | 940 | 304 | 4 |
| `trc_7fzf3vwrrhcay5btvmh7diotn2` | T2 | 0.05/0.25 | true | 90 | 0.232 | 0.122 | 1.000 | 1.394 | 0.846 | 92 | 940 | 306 | 4 |
| `trc_5d5ttg22tnnbzod4qpqi2vsgfe` | T2 | 0.05/0.25 | false | 30 | 0.600 | 0.406 | 1.000 | 1.012 | 0.846 | 84 | 965 | 347 | 4 |
| `trc_tlxvmpta4rfmzxpjzuwv2xk2xr` | T2 | 0.05/0.25 | false | 60 | 0.606 | 0.412 | 1.000 | 1.012 | 0.846 | 84 | 972 | 353 | 5 |
| `trc_b6rrfvpuiu6ylidkyanr7lzftv` | T2 | 0.05/0.25 | false | 90 | 0.606 | 0.412 | 1.000 | 1.012 | 0.846 | 84 | 972 | 353 | 5 |
| `trc_3aq3nhyigi6srfbqaq5dx4bgnm` | T2 | 0.1/0.1 | true | 30 | 0.232 | 0.127 | 1.000 | 1.562 | 0.846 | 114 | 1084 | 335 | 4 |
| `trc_sfdljo5rdq2l6vum2or3xear76` | T2 | 0.1/0.1 | true | 60 | 0.239 | 0.128 | 1.000 | 1.479 | 0.846 | 108 | 1088 | 338 | 5 |
| `trc_t4sfbi3djgzkimzkx2mclmzqab` | T2 | 0.1/0.1 | true | 90 | 0.240 | 0.128 | 1.000 | 1.466 | 0.846 | 107 | 1088 | 338 | 5 |
| `trc_u322ec2actrgeleujg3wy5gf7s` | T2 | 0.1/0.1 | false | 30 | 0.640 | 0.485 | 1.000 | 1.330 | 0.846 | 137 | 1418 | 227 | 5 |
| `trc_vwj4rapjwcqidaiyecfqvy56up` | T2 | 0.1/0.1 | false | 60 | 0.674 | 0.488 | 1.000 | 1.117 | 0.846 | 115 | 1444 | 232 | 6 |
| `trc_ti5uqexlymtt4w6njapjlsojtp` | T2 | 0.1/0.1 | false | 90 | 0.683 | 0.488 | 1.000 | 1.068 | 0.846 | 110 | 1444 | 232 | 6 |
| `trc_td42itiyj43eg4w5v4u6y62osl` | T2 | 0.1/0.25 | true | 30 | 0.222 | 0.122 | 1.000 | 1.500 | 0.846 | 99 | 931 | 296 | 3 |
| `trc_lwyqn5bdfnk34mx7nsqx3xfxt6` | T2 | 0.1/0.25 | true | 60 | 0.229 | 0.122 | 1.000 | 1.439 | 0.846 | 95 | 938 | 301 | 4 |
| `trc_s26dtxuaiopqcciv74jyzrxqye` | T2 | 0.1/0.25 | true | 90 | 0.229 | 0.123 | 1.000 | 1.439 | 0.846 | 95 | 938 | 301 | 4 |
| `trc_jibgvhelaikd2e6aud7aoya42n` | T2 | 0.1/0.25 | false | 30 | 0.545 | 0.366 | 1.000 | 1.072 | 0.846 | 89 | 825 | 136 | 4 |
| `trc_hdppfrmxmvolumjpl7zorak23y` | T2 | 0.1/0.25 | false | 60 | 0.568 | 0.378 | 1.000 | 1.024 | 0.846 | 85 | 861 | 143 | 5 |
| `trc_cpyf67gfxujzifvk365u7d2kzk` | T2 | 0.1/0.25 | false | 90 | 0.575 | 0.380 | 1.000 | 1.000 | 0.846 | 83 | 861 | 143 | 5 |
| `trc_7tcijgv5asvlntvitaav75bzzh` | T2 | 0.25/0.25 | true | 30 | 0.349 | 0.228 | 1.000 | 1.303 | 0.846 | 86 | 133 | 17 | 2 |
| `trc_oeoq5izlsze523yuw6igqey4qe` | T2 | 0.25/0.25 | true | 60 | 0.356 | 0.230 | 1.000 | 1.227 | 0.846 | 81 | 133 | 17 | 3 |
| `trc_krdguasjctwi55fq5brlcrqoql` | T2 | 0.25/0.25 | true | 90 | 0.359 | 0.231 | 1.000 | 1.212 | 0.846 | 80 | 133 | 17 | 3 |
| `trc_uqqvyt5g5klqssm6tptrpvkm2l` | T2 | 0.25/0.25 | false | 30 | 0.399 | 0.262 | 1.000 | 1.227 | 0.846 | 92 | 207 | 24 | 3 |
| `trc_65ty43t64ij755ievg5se7yovl` | T2 | 0.25/0.25 | false | 60 | 0.413 | 0.264 | 1.000 | 1.107 | 0.846 | 83 | 207 | 24 | 4 |
| `trc_jsvqlgs3rdw5mcakkishgv2axo` | T2 | 0.25/0.25 | false | 90 | 0.420 | 0.265 | 1.000 | 1.053 | 0.846 | 79 | 207 | 24 | 4 |

### ceiling (54 cameras)

| config_id | fam | high/new | fuse | buffer | IDF1 F | coverage | precision | frag/id | IDF1 P | tracks | predicted | bridged | changed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `trc_i4ljlcifrwgephzz4cgjkmo5ej` | C | 0.25/0.25 | true | 30 | 0.303 | 0.195 | 1.000 | 1.359 | 0.848 | 53 | 155 | 19 | 0 |
| `trc_i6inovdhm2s36jvamfha2znokd` | T1 | 0.05/0.05 | true | 30 | 0.277 | 0.146 | 1.000 | 1.467 | 0.848 | 66 | 666 | 200 | 3 |
| `trc_q4f7jjd7xqj6e5aogdzz4fjkyi` | T1 | 0.05/0.05 | true | 60 | 0.290 | 0.146 | 1.000 | 1.378 | 0.848 | 62 | 667 | 200 | 4 |
| `trc_iptyuhjlprod37xvlyzaha4o3t` | T1 | 0.05/0.05 | true | 90 | 0.292 | 0.146 | 1.000 | 1.356 | 0.848 | 61 | 667 | 202 | 4 |
| `trc_thdqorfetvz5tlekusjw2fzr3d` | T1 | 0.05/0.05 | false | 30 | 0.869 | 0.767 | 0.993 | 1.259 | 0.848 | 69 | 1237 | 459 | 4 |
| `trc_ty7xfe4xyzwyawowk5jsl25bth` | T1 | 0.05/0.05 | false | 60 | 0.904 | 0.768 | 0.993 | 1.019 | 0.848 | 56 | 1257 | 464 | 5 |
| `trc_7flfpx52d2siiljxkqwcorr7nz` | T1 | 0.05/0.05 | false | 90 | 0.904 | 0.768 | 0.993 | 1.019 | 0.848 | 56 | 1257 | 464 | 5 |
| `trc_jhbd3n3roq5eb5zlbachmwaznd` | T1 | 0.05/0.1 | true | 30 | 0.276 | 0.145 | 1.000 | 1.419 | 0.848 | 61 | 660 | 197 | 3 |
| `trc_7ecoxlkmmpwa7nju6fokbstl3p` | T1 | 0.05/0.1 | true | 60 | 0.289 | 0.145 | 1.000 | 1.326 | 0.848 | 57 | 661 | 197 | 4 |
| `trc_56r4lhbccvvj42iluzhb3742zh` | T1 | 0.05/0.1 | true | 90 | 0.291 | 0.146 | 1.000 | 1.302 | 0.848 | 56 | 661 | 199 | 4 |
| `trc_tzcxbdgfqq2iwmveqinwaoq2dz` | T1 | 0.05/0.1 | false | 30 | 0.866 | 0.733 | 1.000 | 1.113 | 0.848 | 59 | 1019 | 383 | 4 |
| `trc_ymh7canszduw3ehnzu2loheade` | T1 | 0.05/0.1 | false | 60 | 0.890 | 0.745 | 1.000 | 1.019 | 0.848 | 54 | 1063 | 399 | 5 |
| `trc_szpvvuexivjl5bl2wvji7cujm6` | T1 | 0.05/0.1 | false | 90 | 0.890 | 0.745 | 1.000 | 1.019 | 0.848 | 54 | 1063 | 399 | 5 |
| `trc_opkceesi7bntbkvtk3e3nmlunz` | T1 | 0.05/0.25 | true | 30 | 0.259 | 0.139 | 1.000 | 1.385 | 0.848 | 54 | 545 | 170 | 2 |
| `trc_rurkfeuk7hlzv4hmhtpey5njb6` | T1 | 0.05/0.25 | true | 60 | 0.272 | 0.139 | 1.000 | 1.333 | 0.848 | 52 | 546 | 171 | 3 |
| `trc_bcyg7lfluv75l4imauxapzt32d` | T1 | 0.05/0.25 | true | 90 | 0.274 | 0.140 | 1.000 | 1.308 | 0.848 | 51 | 546 | 173 | 3 |
| `trc_omlp2gnep3xrljhnriytvjcy2b` | T1 | 0.05/0.25 | false | 30 | 0.759 | 0.581 | 1.000 | 1.021 | 0.848 | 48 | 617 | 233 | 3 |
| `trc_otjx7ewwcdinggj5kq4wo2jpxp` | T1 | 0.05/0.25 | false | 60 | 0.769 | 0.592 | 1.000 | 1.021 | 0.848 | 48 | 623 | 238 | 4 |
| `trc_4sqebhcej3snnwoft3vseratdp` | T1 | 0.05/0.25 | false | 90 | 0.769 | 0.592 | 1.000 | 1.021 | 0.848 | 48 | 623 | 238 | 4 |
| `trc_rprnecxj22fh3uqry6hovthhy3` | T1 | 0.1/0.1 | true | 30 | 0.273 | 0.145 | 1.000 | 1.442 | 0.848 | 62 | 655 | 196 | 3 |
| `trc_6swarrsbbxpitt46xpsrxzjgot` | T1 | 0.1/0.1 | true | 60 | 0.286 | 0.145 | 1.000 | 1.349 | 0.848 | 58 | 656 | 196 | 4 |
| `trc_mpkoyfsbsccwbclp44xjmwbp37` | T1 | 0.1/0.1 | true | 90 | 0.286 | 0.146 | 1.000 | 1.349 | 0.848 | 58 | 656 | 196 | 4 |
| `trc_tzp4lgbqkwqqpkfhndzeak7xpv` | T1 | 0.1/0.1 | false | 30 | 0.764 | 0.646 | 1.000 | 1.377 | 0.848 | 73 | 786 | 122 | 4 |
| `trc_zkhhdt2wbjqvyq3d75row3z6rj` | T1 | 0.1/0.1 | false | 60 | 0.801 | 0.647 | 1.000 | 1.151 | 0.848 | 61 | 798 | 124 | 5 |
| `trc_57amvce2wbtzkvsve7vlz4ouux` | T1 | 0.1/0.1 | false | 90 | 0.817 | 0.647 | 1.000 | 1.057 | 0.848 | 56 | 798 | 124 | 5 |
| `trc_esfnz7sdckzxcqnyprk5idbjr3` | T1 | 0.1/0.25 | true | 30 | 0.256 | 0.139 | 1.000 | 1.410 | 0.848 | 55 | 541 | 169 | 2 |
| `trc_gap6fq4qmi5x3nf3eoj7ore62t` | T1 | 0.1/0.25 | true | 60 | 0.269 | 0.139 | 1.000 | 1.359 | 0.848 | 53 | 542 | 170 | 3 |
| `trc_fpsjioulywcag7hw6i2z24bjg7` | T1 | 0.1/0.25 | true | 90 | 0.269 | 0.139 | 1.000 | 1.359 | 0.848 | 53 | 542 | 170 | 3 |
| `trc_i7l6anybs45d4uaggxhl3rjzh4` | T1 | 0.1/0.25 | false | 30 | 0.685 | 0.513 | 1.000 | 1.106 | 0.848 | 52 | 572 | 89 | 3 |
| `trc_66qro5wri5n4p45el5xqge6cbg` | T1 | 0.1/0.25 | false | 60 | 0.717 | 0.534 | 1.000 | 1.043 | 0.848 | 49 | 587 | 92 | 4 |
| `trc_7n3saxjbtiehw55yuvu6lpnn3n` | T1 | 0.1/0.25 | false | 90 | 0.731 | 0.539 | 1.000 | 1.000 | 0.848 | 47 | 587 | 92 | 4 |
| `trc_7wsw2iclhmh7qddej3p6nl7eam` | T1 | 0.25/0.25 | true | 30 | 0.428 | 0.294 | 1.000 | 1.359 | 0.848 | 53 | 81 | 9 | 1 |
| `trc_w4bwtsfabqk6kf5sjxc77csduo` | T1 | 0.25/0.25 | true | 60 | 0.438 | 0.298 | 1.000 | 1.282 | 0.848 | 50 | 81 | 9 | 2 |
| `trc_sxnrsqt5ussetdwyvx6daleikf` | T1 | 0.25/0.25 | true | 90 | 0.444 | 0.299 | 1.000 | 1.256 | 0.848 | 49 | 81 | 9 | 2 |
| `trc_fkywz4gq4fo5qlg46ac6lovy7m` | T1 | 0.25/0.25 | false | 30 | 0.481 | 0.344 | 1.000 | 1.333 | 0.848 | 60 | 88 | 8 | 2 |
| `trc_vywoqxr6ys2ev5jxyuu4mlzrq5` | T1 | 0.25/0.25 | false | 60 | 0.499 | 0.348 | 1.000 | 1.178 | 0.848 | 53 | 88 | 8 | 3 |
| `trc_hkx3gos7rj6keeoazv6c4zpw4c` | T1 | 0.25/0.25 | false | 90 | 0.512 | 0.350 | 1.000 | 1.111 | 0.848 | 50 | 88 | 8 | 3 |
| `trc_bo2nrse7haxr3qsmqccu4vzi7q` | T2 | 0.05/0.05 | true | 30 | 0.279 | 0.152 | 1.000 | 1.489 | 0.848 | 67 | 640 | 194 | 4 |
| `trc_5rafgrfmh7yq24md5oj2tgzab6` | T2 | 0.05/0.05 | true | 60 | 0.290 | 0.153 | 1.000 | 1.400 | 0.848 | 63 | 640 | 194 | 5 |
| `trc_kdi65wy3zqxrlippd5htqu63ge` | T2 | 0.05/0.05 | true | 90 | 0.292 | 0.153 | 1.000 | 1.378 | 0.848 | 62 | 640 | 196 | 5 |
| `trc_yd3pf63froggbg5qso24my4xjt` | T2 | 0.05/0.05 | false | 30 | 0.868 | 0.767 | 0.993 | 1.259 | 0.848 | 69 | 1237 | 459 | 5 |
| `trc_fqxlvtw3jqab2lzk3j3vbc7pwx` | T2 | 0.05/0.05 | false | 60 | 0.903 | 0.768 | 0.993 | 1.019 | 0.848 | 56 | 1257 | 464 | 6 |
| `trc_iwm5ndlac27qun2gouwrtoroun` | T2 | 0.05/0.05 | false | 90 | 0.903 | 0.768 | 0.993 | 1.019 | 0.848 | 56 | 1257 | 464 | 6 |
| `trc_hlhqp4zcm5kfzn6xue5hk5cnuk` | T2 | 0.05/0.1 | true | 30 | 0.277 | 0.152 | 1.000 | 1.442 | 0.848 | 62 | 634 | 191 | 4 |
| `trc_5tgiem2xes7keizbo44uy6igu2` | T2 | 0.05/0.1 | true | 60 | 0.289 | 0.152 | 1.000 | 1.349 | 0.848 | 58 | 634 | 191 | 5 |
| `trc_gvbqokhg633qfqipwo2reyadej` | T2 | 0.05/0.1 | true | 90 | 0.290 | 0.152 | 1.000 | 1.326 | 0.848 | 57 | 634 | 193 | 5 |
| `trc_xe6irqxylqxyopypzlp4b3bttg` | T2 | 0.05/0.1 | false | 30 | 0.865 | 0.733 | 1.000 | 1.113 | 0.848 | 59 | 1019 | 383 | 5 |
| `trc_74xioyvkakr5yn5lruvrtobmel` | T2 | 0.05/0.1 | false | 60 | 0.889 | 0.745 | 1.000 | 1.019 | 0.848 | 54 | 1063 | 399 | 6 |
| `trc_sh6pgy4hrct4o54bifyrzvhfyx` | T2 | 0.05/0.1 | false | 90 | 0.889 | 0.745 | 1.000 | 1.019 | 0.848 | 54 | 1063 | 399 | 6 |
| `trc_5ogeizg475eftefrdz3he6q6mp` | T2 | 0.05/0.25 | true | 30 | 0.261 | 0.145 | 1.000 | 1.410 | 0.848 | 55 | 513 | 164 | 3 |
| `trc_ebqvyr6ixfcit3vax3j5rs7qp2` | T2 | 0.05/0.25 | true | 60 | 0.271 | 0.145 | 1.000 | 1.359 | 0.848 | 53 | 514 | 165 | 4 |
| `trc_7fzf3vwrrhcay5btvmh7diotn2` | T2 | 0.05/0.25 | true | 90 | 0.273 | 0.146 | 1.000 | 1.333 | 0.848 | 52 | 514 | 167 | 4 |
| `trc_5d5ttg22tnnbzod4qpqi2vsgfe` | T2 | 0.05/0.25 | false | 30 | 0.758 | 0.581 | 1.000 | 1.021 | 0.848 | 48 | 617 | 233 | 4 |
| `trc_tlxvmpta4rfmzxpjzuwv2xk2xr` | T2 | 0.05/0.25 | false | 60 | 0.768 | 0.592 | 1.000 | 1.021 | 0.848 | 48 | 623 | 238 | 5 |
| `trc_b6rrfvpuiu6ylidkyanr7lzftv` | T2 | 0.05/0.25 | false | 90 | 0.768 | 0.592 | 1.000 | 1.021 | 0.848 | 48 | 623 | 238 | 5 |
| `trc_3aq3nhyigi6srfbqaq5dx4bgnm` | T2 | 0.1/0.1 | true | 30 | 0.278 | 0.153 | 1.000 | 1.442 | 0.848 | 62 | 627 | 190 | 4 |
| `trc_sfdljo5rdq2l6vum2or3xear76` | T2 | 0.1/0.1 | true | 60 | 0.289 | 0.153 | 1.000 | 1.349 | 0.848 | 58 | 627 | 190 | 5 |
| `trc_t4sfbi3djgzkimzkx2mclmzqab` | T2 | 0.1/0.1 | true | 90 | 0.290 | 0.153 | 1.000 | 1.349 | 0.848 | 58 | 627 | 190 | 5 |
| `trc_u322ec2actrgeleujg3wy5gf7s` | T2 | 0.1/0.1 | false | 30 | 0.764 | 0.646 | 1.000 | 1.377 | 0.848 | 73 | 784 | 121 | 5 |
| `trc_vwj4rapjwcqidaiyecfqvy56up` | T2 | 0.1/0.1 | false | 60 | 0.801 | 0.647 | 1.000 | 1.151 | 0.848 | 61 | 796 | 123 | 6 |
| `trc_ti5uqexlymtt4w6njapjlsojtp` | T2 | 0.1/0.1 | false | 90 | 0.817 | 0.648 | 1.000 | 1.057 | 0.848 | 56 | 796 | 123 | 6 |
| `trc_td42itiyj43eg4w5v4u6y62osl` | T2 | 0.1/0.25 | true | 30 | 0.262 | 0.145 | 1.000 | 1.410 | 0.848 | 55 | 511 | 163 | 3 |
| `trc_lwyqn5bdfnk34mx7nsqx3xfxt6` | T2 | 0.1/0.25 | true | 60 | 0.272 | 0.146 | 1.000 | 1.359 | 0.848 | 53 | 512 | 164 | 4 |
| `trc_s26dtxuaiopqcciv74jyzrxqye` | T2 | 0.1/0.25 | true | 90 | 0.272 | 0.146 | 1.000 | 1.359 | 0.848 | 53 | 512 | 164 | 4 |
| `trc_jibgvhelaikd2e6aud7aoya42n` | T2 | 0.1/0.25 | false | 30 | 0.685 | 0.513 | 1.000 | 1.106 | 0.848 | 52 | 570 | 88 | 4 |
| `trc_hdppfrmxmvolumjpl7zorak23y` | T2 | 0.1/0.25 | false | 60 | 0.717 | 0.534 | 1.000 | 1.043 | 0.848 | 49 | 585 | 91 | 5 |
| `trc_cpyf67gfxujzifvk365u7d2kzk` | T2 | 0.1/0.25 | false | 90 | 0.731 | 0.539 | 1.000 | 1.000 | 0.848 | 47 | 585 | 91 | 5 |
| `trc_7tcijgv5asvlntvitaav75bzzh` | T2 | 0.25/0.25 | true | 30 | 0.441 | 0.303 | 1.000 | 1.308 | 0.848 | 51 | 67 | 6 | 2 |
| `trc_oeoq5izlsze523yuw6igqey4qe` | T2 | 0.25/0.25 | true | 60 | 0.445 | 0.303 | 1.000 | 1.231 | 0.848 | 48 | 67 | 6 | 3 |
| `trc_krdguasjctwi55fq5brlcrqoql` | T2 | 0.25/0.25 | true | 90 | 0.451 | 0.304 | 1.000 | 1.205 | 0.848 | 47 | 67 | 6 | 3 |
| `trc_uqqvyt5g5klqssm6tptrpvkm2l` | T2 | 0.25/0.25 | false | 30 | 0.487 | 0.347 | 1.000 | 1.311 | 0.848 | 59 | 88 | 8 | 3 |
| `trc_65ty43t64ij755ievg5se7yovl` | T2 | 0.25/0.25 | false | 60 | 0.505 | 0.351 | 1.000 | 1.156 | 0.848 | 52 | 88 | 8 | 4 |
| `trc_jsvqlgs3rdw5mcakkishgv2axo` | T2 | 0.25/0.25 | false | 90 | 0.518 | 0.353 | 1.000 | 1.089 | 0.848 | 49 | 88 | 8 | 4 |

### eye_level (62 cameras)

| config_id | fam | high/new | fuse | buffer | IDF1 F | coverage | precision | frag/id | IDF1 P | tracks | predicted | bridged | changed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `trc_i4ljlcifrwgephzz4cgjkmo5ej` | C | 0.25/0.25 | true | 30 | 0.199 | 0.128 | 1.000 | 1.667 | 0.844 | 45 | 179 | 28 | 0 |
| `trc_i6inovdhm2s36jvamfha2znokd` | T1 | 0.05/0.05 | true | 30 | 0.178 | 0.098 | 0.999 | 1.829 | 0.844 | 66 | 444 | 144 | 3 |
| `trc_q4f7jjd7xqj6e5aogdzz4fjkyi` | T1 | 0.05/0.05 | true | 60 | 0.187 | 0.098 | 0.999 | 1.714 | 0.844 | 62 | 451 | 146 | 4 |
| `trc_iptyuhjlprod37xvlyzaha4o3t` | T1 | 0.05/0.05 | true | 90 | 0.187 | 0.099 | 0.999 | 1.686 | 0.844 | 61 | 450 | 145 | 4 |
| `trc_thdqorfetvz5tlekusjw2fzr3d` | T1 | 0.05/0.05 | false | 30 | 0.602 | 0.432 | 0.956 | 1.310 | 0.844 | 82 | 1596 | 496 | 4 |
| `trc_ty7xfe4xyzwyawowk5jsl25bth` | T1 | 0.05/0.05 | false | 60 | 0.626 | 0.433 | 0.956 | 1.138 | 0.844 | 70 | 1621 | 504 | 5 |
| `trc_7flfpx52d2siiljxkqwcorr7nz` | T1 | 0.05/0.05 | false | 90 | 0.633 | 0.433 | 0.956 | 1.103 | 0.844 | 67 | 1621 | 504 | 5 |
| `trc_jhbd3n3roq5eb5zlbachmwaznd` | T1 | 0.05/0.1 | true | 30 | 0.177 | 0.098 | 1.000 | 1.900 | 0.844 | 57 | 427 | 142 | 3 |
| `trc_7ecoxlkmmpwa7nju6fokbstl3p` | T1 | 0.05/0.1 | true | 60 | 0.185 | 0.098 | 1.000 | 1.767 | 0.844 | 53 | 434 | 144 | 4 |
| `trc_56r4lhbccvvj42iluzhb3742zh` | T1 | 0.05/0.1 | true | 90 | 0.185 | 0.098 | 1.000 | 1.733 | 0.844 | 52 | 433 | 143 | 4 |
| `trc_tzcxbdgfqq2iwmveqinwaoq2dz` | T1 | 0.05/0.1 | false | 30 | 0.585 | 0.398 | 0.983 | 1.135 | 0.844 | 60 | 1079 | 346 | 4 |
| `trc_ymh7canszduw3ehnzu2loheade` | T1 | 0.05/0.1 | false | 60 | 0.596 | 0.401 | 0.984 | 1.038 | 0.844 | 55 | 1114 | 357 | 5 |
| `trc_szpvvuexivjl5bl2wvji7cujm6` | T1 | 0.05/0.1 | false | 90 | 0.603 | 0.402 | 0.984 | 1.019 | 0.844 | 54 | 1114 | 357 | 5 |
| `trc_opkceesi7bntbkvtk3e3nmlunz` | T1 | 0.05/0.25 | true | 30 | 0.172 | 0.093 | 1.000 | 1.741 | 0.844 | 47 | 371 | 122 | 2 |
| `trc_rurkfeuk7hlzv4hmhtpey5njb6` | T1 | 0.05/0.25 | true | 60 | 0.178 | 0.094 | 1.000 | 1.667 | 0.844 | 45 | 381 | 126 | 3 |
| `trc_bcyg7lfluv75l4imauxapzt32d` | T1 | 0.05/0.25 | true | 90 | 0.178 | 0.094 | 1.000 | 1.667 | 0.844 | 45 | 381 | 126 | 3 |
| `trc_omlp2gnep3xrljhnriytvjcy2b` | T1 | 0.05/0.25 | false | 30 | 0.415 | 0.247 | 1.000 | 1.000 | 0.844 | 36 | 348 | 114 | 3 |
| `trc_otjx7ewwcdinggj5kq4wo2jpxp` | T1 | 0.05/0.25 | false | 60 | 0.416 | 0.248 | 1.000 | 1.000 | 0.844 | 36 | 349 | 115 | 4 |
| `trc_4sqebhcej3snnwoft3vseratdp` | T1 | 0.05/0.25 | false | 90 | 0.416 | 0.248 | 1.000 | 1.000 | 0.844 | 36 | 349 | 115 | 4 |
| `trc_rprnecxj22fh3uqry6hovthhy3` | T1 | 0.1/0.1 | true | 30 | 0.175 | 0.099 | 1.000 | 1.933 | 0.844 | 58 | 416 | 141 | 3 |
| `trc_6swarrsbbxpitt46xpsrxzjgot` | T1 | 0.1/0.1 | true | 60 | 0.179 | 0.099 | 1.000 | 1.833 | 0.844 | 55 | 416 | 141 | 4 |
| `trc_mpkoyfsbsccwbclp44xjmwbp37` | T1 | 0.1/0.1 | true | 90 | 0.179 | 0.099 | 1.000 | 1.800 | 0.844 | 54 | 415 | 140 | 4 |
| `trc_tzp4lgbqkwqqpkfhndzeak7xpv` | T1 | 0.1/0.1 | false | 30 | 0.498 | 0.337 | 1.000 | 1.300 | 0.844 | 65 | 639 | 109 | 4 |
| `trc_zkhhdt2wbjqvyq3d75row3z6rj` | T1 | 0.1/0.1 | false | 60 | 0.529 | 0.341 | 1.000 | 1.100 | 0.844 | 55 | 653 | 112 | 5 |
| `trc_57amvce2wbtzkvsve7vlz4ouux` | T1 | 0.1/0.1 | false | 90 | 0.529 | 0.341 | 1.000 | 1.100 | 0.844 | 55 | 653 | 112 | 5 |
| `trc_esfnz7sdckzxcqnyprk5idbjr3` | T1 | 0.1/0.25 | true | 30 | 0.170 | 0.094 | 1.000 | 1.815 | 0.844 | 49 | 375 | 122 | 2 |
| `trc_gap6fq4qmi5x3nf3eoj7ore62t` | T1 | 0.1/0.25 | true | 60 | 0.174 | 0.095 | 1.000 | 1.704 | 0.844 | 46 | 378 | 124 | 3 |
| `trc_fpsjioulywcag7hw6i2z24bjg7` | T1 | 0.1/0.25 | true | 90 | 0.174 | 0.095 | 1.000 | 1.704 | 0.844 | 46 | 378 | 124 | 3 |
| `trc_i7l6anybs45d4uaggxhl3rjzh4` | T1 | 0.1/0.25 | false | 30 | 0.385 | 0.230 | 1.000 | 1.028 | 0.844 | 37 | 257 | 50 | 3 |
| `trc_66qro5wri5n4p45el5xqge6cbg` | T1 | 0.1/0.25 | false | 60 | 0.395 | 0.235 | 1.000 | 1.000 | 0.844 | 36 | 278 | 54 | 4 |
| `trc_7n3saxjbtiehw55yuvu6lpnn3n` | T1 | 0.1/0.25 | false | 90 | 0.395 | 0.235 | 1.000 | 1.000 | 0.844 | 36 | 278 | 54 | 4 |
| `trc_7wsw2iclhmh7qddej3p6nl7eam` | T1 | 0.25/0.25 | true | 30 | 0.227 | 0.147 | 1.000 | 1.556 | 0.844 | 42 | 80 | 15 | 1 |
| `trc_w4bwtsfabqk6kf5sjxc77csduo` | T1 | 0.25/0.25 | true | 60 | 0.238 | 0.154 | 1.000 | 1.481 | 0.844 | 40 | 80 | 15 | 2 |
| `trc_sxnrsqt5ussetdwyvx6daleikf` | T1 | 0.25/0.25 | true | 90 | 0.238 | 0.154 | 1.000 | 1.481 | 0.844 | 40 | 80 | 15 | 2 |
| `trc_fkywz4gq4fo5qlg46ac6lovy7m` | T1 | 0.25/0.25 | false | 30 | 0.308 | 0.183 | 1.000 | 1.100 | 0.844 | 33 | 124 | 18 | 2 |
| `trc_vywoqxr6ys2ev5jxyuu4mlzrq5` | T1 | 0.25/0.25 | false | 60 | 0.317 | 0.184 | 1.000 | 1.033 | 0.844 | 31 | 124 | 18 | 3 |
| `trc_hkx3gos7rj6keeoazv6c4zpw4c` | T1 | 0.25/0.25 | false | 90 | 0.318 | 0.184 | 1.000 | 1.000 | 0.844 | 30 | 124 | 18 | 3 |
| `trc_bo2nrse7haxr3qsmqccu4vzi7q` | T2 | 0.05/0.05 | true | 30 | 0.192 | 0.105 | 0.999 | 1.657 | 0.844 | 60 | 484 | 151 | 4 |
| `trc_5rafgrfmh7yq24md5oj2tgzab6` | T2 | 0.05/0.05 | true | 60 | 0.199 | 0.105 | 0.999 | 1.571 | 0.844 | 57 | 493 | 156 | 5 |
| `trc_kdi65wy3zqxrlippd5htqu63ge` | T2 | 0.05/0.05 | true | 90 | 0.199 | 0.105 | 0.999 | 1.543 | 0.844 | 56 | 493 | 156 | 5 |
| `trc_yd3pf63froggbg5qso24my4xjt` | T2 | 0.05/0.05 | false | 30 | 0.604 | 0.432 | 0.956 | 1.310 | 0.844 | 82 | 1583 | 494 | 5 |
| `trc_fqxlvtw3jqab2lzk3j3vbc7pwx` | T2 | 0.05/0.05 | false | 60 | 0.628 | 0.433 | 0.956 | 1.138 | 0.844 | 70 | 1608 | 502 | 6 |
| `trc_iwm5ndlac27qun2gouwrtoroun` | T2 | 0.05/0.05 | false | 90 | 0.635 | 0.433 | 0.956 | 1.103 | 0.844 | 67 | 1608 | 502 | 6 |
| `trc_hlhqp4zcm5kfzn6xue5hk5cnuk` | T2 | 0.05/0.1 | true | 30 | 0.190 | 0.103 | 1.000 | 1.700 | 0.844 | 51 | 467 | 146 | 4 |
| `trc_5tgiem2xes7keizbo44uy6igu2` | T2 | 0.05/0.1 | true | 60 | 0.198 | 0.104 | 1.000 | 1.600 | 0.844 | 48 | 476 | 151 | 5 |
| `trc_gvbqokhg633qfqipwo2reyadej` | T2 | 0.05/0.1 | true | 90 | 0.198 | 0.104 | 1.000 | 1.567 | 0.844 | 47 | 476 | 151 | 5 |
| `trc_xe6irqxylqxyopypzlp4b3bttg` | T2 | 0.05/0.1 | false | 30 | 0.587 | 0.398 | 0.983 | 1.135 | 0.844 | 60 | 1079 | 346 | 5 |
| `trc_74xioyvkakr5yn5lruvrtobmel` | T2 | 0.05/0.1 | false | 60 | 0.598 | 0.401 | 0.984 | 1.038 | 0.844 | 55 | 1114 | 357 | 6 |
| `trc_sh6pgy4hrct4o54bifyrzvhfyx` | T2 | 0.05/0.1 | false | 90 | 0.604 | 0.402 | 0.984 | 1.019 | 0.844 | 54 | 1114 | 357 | 6 |
| `trc_5ogeizg475eftefrdz3he6q6mp` | T2 | 0.05/0.25 | true | 30 | 0.187 | 0.099 | 1.000 | 1.519 | 0.844 | 41 | 406 | 130 | 3 |
| `trc_ebqvyr6ixfcit3vax3j5rs7qp2` | T2 | 0.05/0.25 | true | 60 | 0.192 | 0.101 | 1.000 | 1.481 | 0.844 | 40 | 426 | 139 | 4 |
| `trc_7fzf3vwrrhcay5btvmh7diotn2` | T2 | 0.05/0.25 | true | 90 | 0.192 | 0.101 | 1.000 | 1.481 | 0.844 | 40 | 426 | 139 | 4 |
| `trc_5d5ttg22tnnbzod4qpqi2vsgfe` | T2 | 0.05/0.25 | false | 30 | 0.415 | 0.247 | 1.000 | 1.000 | 0.844 | 36 | 348 | 114 | 4 |
| `trc_tlxvmpta4rfmzxpjzuwv2xk2xr` | T2 | 0.05/0.25 | false | 60 | 0.417 | 0.248 | 1.000 | 1.000 | 0.844 | 36 | 349 | 115 | 5 |
| `trc_b6rrfvpuiu6ylidkyanr7lzftv` | T2 | 0.05/0.25 | false | 90 | 0.417 | 0.248 | 1.000 | 1.000 | 0.844 | 36 | 349 | 115 | 5 |
| `trc_3aq3nhyigi6srfbqaq5dx4bgnm` | T2 | 0.1/0.1 | true | 30 | 0.189 | 0.105 | 1.000 | 1.733 | 0.844 | 52 | 457 | 145 | 4 |
| `trc_sfdljo5rdq2l6vum2or3xear76` | T2 | 0.1/0.1 | true | 60 | 0.191 | 0.105 | 1.000 | 1.667 | 0.844 | 50 | 461 | 148 | 5 |
| `trc_t4sfbi3djgzkimzkx2mclmzqab` | T2 | 0.1/0.1 | true | 90 | 0.191 | 0.105 | 1.000 | 1.633 | 0.844 | 49 | 461 | 148 | 5 |
| `trc_u322ec2actrgeleujg3wy5gf7s` | T2 | 0.1/0.1 | false | 30 | 0.500 | 0.338 | 1.000 | 1.280 | 0.844 | 64 | 634 | 106 | 5 |
| `trc_vwj4rapjwcqidaiyecfqvy56up` | T2 | 0.1/0.1 | false | 60 | 0.531 | 0.341 | 1.000 | 1.080 | 0.844 | 54 | 648 | 109 | 6 |
| `trc_ti5uqexlymtt4w6njapjlsojtp` | T2 | 0.1/0.1 | false | 90 | 0.531 | 0.341 | 1.000 | 1.080 | 0.844 | 54 | 648 | 109 | 6 |
| `trc_td42itiyj43eg4w5v4u6y62osl` | T2 | 0.1/0.25 | true | 30 | 0.184 | 0.100 | 1.000 | 1.630 | 0.844 | 44 | 420 | 133 | 3 |
| `trc_lwyqn5bdfnk34mx7nsqx3xfxt6` | T2 | 0.1/0.25 | true | 60 | 0.188 | 0.101 | 1.000 | 1.556 | 0.844 | 42 | 426 | 137 | 4 |
| `trc_s26dtxuaiopqcciv74jyzrxqye` | T2 | 0.1/0.25 | true | 90 | 0.188 | 0.101 | 1.000 | 1.556 | 0.844 | 42 | 426 | 137 | 4 |
| `trc_jibgvhelaikd2e6aud7aoya42n` | T2 | 0.1/0.25 | false | 30 | 0.385 | 0.230 | 1.000 | 1.028 | 0.844 | 37 | 255 | 48 | 4 |
| `trc_hdppfrmxmvolumjpl7zorak23y` | T2 | 0.1/0.25 | false | 60 | 0.395 | 0.235 | 1.000 | 1.000 | 0.844 | 36 | 276 | 52 | 5 |
| `trc_cpyf67gfxujzifvk365u7d2kzk` | T2 | 0.1/0.25 | false | 90 | 0.395 | 0.235 | 1.000 | 1.000 | 0.844 | 36 | 276 | 52 | 5 |
| `trc_7tcijgv5asvlntvitaav75bzzh` | T2 | 0.25/0.25 | true | 30 | 0.256 | 0.159 | 1.000 | 1.296 | 0.844 | 35 | 66 | 11 | 2 |
| `trc_oeoq5izlsze523yuw6igqey4qe` | T2 | 0.25/0.25 | true | 60 | 0.264 | 0.164 | 1.000 | 1.222 | 0.844 | 33 | 66 | 11 | 3 |
| `trc_krdguasjctwi55fq5brlcrqoql` | T2 | 0.25/0.25 | true | 90 | 0.264 | 0.164 | 1.000 | 1.222 | 0.844 | 33 | 66 | 11 | 3 |
| `trc_uqqvyt5g5klqssm6tptrpvkm2l` | T2 | 0.25/0.25 | false | 30 | 0.308 | 0.183 | 1.000 | 1.100 | 0.844 | 33 | 119 | 16 | 3 |
| `trc_65ty43t64ij755ievg5se7yovl` | T2 | 0.25/0.25 | false | 60 | 0.316 | 0.184 | 1.000 | 1.033 | 0.844 | 31 | 119 | 16 | 4 |
| `trc_jsvqlgs3rdw5mcakkishgv2axo` | T2 | 0.25/0.25 | false | 90 | 0.317 | 0.184 | 1.000 | 1.000 | 0.844 | 30 | 119 | 16 | 4 |

Person tracker: ByteTrack, column C configuration, one job per camera shared by every configuration, so person IDF1 is identical in every row by construction. Column C's tracker run reproduced the stored column C tracker log on 96 cameras (all identical: True).

## Fragmentation (STEP 6), tracking level only

| configuration | view | identities covered | median | P90 | max | covered by ≥ 2 tracks | longest bridged gap (frames) |
|---|---|---|---|---|---|---|---|
| package `trc_7flfpx52d2siiljxkqwcorr7nz` | all | 112 / 116 | 1.0 | 1 | 2 | 7 | 15 |
| package `trc_7flfpx52d2siiljxkqwcorr7nz` | ceiling | 54 / 54 | 1.0 | 1 | 2 | 1 | 15 |
| package `trc_7flfpx52d2siiljxkqwcorr7nz` | eye_level | 58 / 62 | 1.0 | 2 | 2 | 6 | 14 |
| column_c `trc_i4ljlcifrwgephzz4cgjkmo5ej` | all | 66 / 116 | 1.0 | 2 | 4 | 26 | 15 |
| column_c `trc_i4ljlcifrwgephzz4cgjkmo5ej` | ceiling | 39 / 54 | 1 | 2 | 3 | 13 | 15 |
| column_c `trc_i4ljlcifrwgephzz4cgjkmo5ej` | eye_level | 27 / 62 | 1 | 3 | 4 | 13 | 14 |

Secondary reading (tracked and predicted points) in `v2_tracker_fragmentation.json`. No recommendation is made; this informs the later stitching decision.

## Files

- `research/m1b/botsort_keys.json`: installed BoT-SORT keys and the D-55 settings.
- `research/m1b/v2_tracker_grid.json`: one row per configuration (overall and by viewpoint, both readings).
- `research/m1b/v2_tracker_selection.json`: guards, band, tie-break path, winners, column C row, sensitivity.
- `research/m1b/v2_tracker_fragmentation.json`: STEP 6.
- CR-033: the `tracker_id` field for column C, and the readings used.
