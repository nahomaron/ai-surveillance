"""The single schema source (WP-00): every table of E-1.2.1 section 5, as amended by F.1.

Each definition line is `name[?] type [@constraint ...] [~]`. `@event` marks an event-time column (AR-7 as revised):
stored, but outside the payload hash, the artifact ID and every record ID. `?` is nullable (section 1.1); `~` marks
a field or type the contract implies but does not state, listed in CR-002. Same-artifact `nk`
columns and each table's own ID are expanded in registry.py. Anchor tables use parent anchor IDs
(F.1 A1.2).
"""
from __future__ import annotations

ENUMS: dict[str, tuple[str, ...]] = {
    "data_origin": ("real_natural", "real_staged", "synthetic_rendered", "synthetic_transferred"),
    "prov_class": ("human_observed", "human_measured", "human_judged", "human_adjudicated", "model_estimated",
                   "geometry_estimated", "rule_derived", "simulator_truth", "dataset_supplied", "externally_supplied"),
    "null_reason": ("not_applicable", "not_observable", "uncalibrated", "upstream_failure", "not_supplied",
                    "not_computed_by_config", "withheld_privacy", "pending_review", "out_of_scope_rq1"),
    "sigma_status": ("calibrated", "inflated", "uncalibrated_model", "not_estimated"),
    "timeline_kind": ("aligned_session", "recording_local"),
    "coverage_state": ("not_recorded", "gap_unobserved", "unusable", "usable_degraded", "usable"),
    "ai_activity_state": ("not_evaluated", "observed_no_detection", "objects_detected_no_pair", "pair_detected"),
    "ref_activity_state": ("not_annotated", "unobservable", "reference_verified_absent",
                           "objects_present_no_interaction", "interaction_present"),
    "evidence_class": ("detected", "inferred", "insufficient"),
    "evidence_state": ("visible", "partially_visible", "occluded_predicted", "truncated", "lost"),
    "geometry_method": ("none", "image_only", "ground_plane_homography", "full_camera", "multi_view",
                        "simulator_truth", "reference_survey", "reference_click"),
    "calibration_tier": ("full_camera", "ground_plane_homography"),
    "contact_state": ("none_observed", "undetermined", "suspected", "not_assessable"),
    "sample_type": ("RES", "ECS"),
    "namespace": ("reference", "candidate_review", "study_d6", "pseudo_label"),
    "label_source": ("simulator_truth", "human_manual", "human_corrected_from_model", "model_only"),
    "scenario": ("S_VIEW", "S_LINK", "S_POSS"),
    "unit_status": ("verified", "assumed", "unknown"),
    "reference_class": ("rule_conformance", "independent_perceptual_geometric", "independent_expert_judgment"),
    "object_class": ("person", "forklift", "pallet_truck", "load", "rack", "fork", "other"),
    "support_basis": ("detected", "detected_plus_inferred"),
    "consensus_method": ("agreement", "third_annotator", "adjudicated", "simulator"),
    "q_reason": ("person_occluded", "forklift_occluded", "truncated", "low_quality_frame", "predicted_only",
                 "timing_uncertain", "person_lost", "forklift_lost"),  # T10.9 adds the *_lost values
    "quality_flag": ("frozen", "black", "overexposed", "blurred", "compression_damage", "decode_error"),
    "summary_label": ("CT", "UD", "NM", "PC", "H", "O"),
    "export_class": ("fixture_verification", "research"),
}

# (name, prefix, store, stage, identity class, natural key, definition, types_inferred)
_D: list[tuple] = []


def _t(name, prefix, store, stage, cls, key, body, inferred=False):
    _D.append((name, prefix, store, stage, cls, key, body, inferred))


# Section 5.1 registration (anchor class, F.1 A1.2).
_t("dataset_source", "dsr", "Obs", "S0", "anchor", "name version", """
name str
version str
data_origin data_origin
dataset_kind enum{fixture,research}
source_url str
retrieved_utc ts
license_component_id id
annotation_levels list<enum{objects,tracks,world_geometry,zones,events,none}>
unit_status unit_status
notes_ref? str
""")
_t("license_component", "lic", "Gov", "S0", "anchor", "component version", """
component str
version str
component_type enum{dataset,model_code,model_weights,library,tool}
license_label str
terms_location enum{license_file,card_only,website,written_agreement,unknown}
obligations list<str>
license_status enum{verified,card_only_unverified,open_question,not_read}
verified_utc? ts
decision_ref? str
""")
_t("site", "sit", "Obs", "S0", "anchor", "dataset_id site_label", """
dataset_id id
site_label str
data_origin data_origin
site_kind enum{synthetic_scene,staged_facility,operational_facility}
independent_of_development bool
approvals_ref? str
""")
_t("session", "ses", "Obs", "S0", "anchor", "site_id session_label", """
site_id id
session_label str
scripted bool
scenario_ref? str
lineage struct{ext_run_id?:str,scene_id?:str,render_parent?:str,seed?:i64,generation_batch?:str,actor_roster_ref?:str,layout_id?:str,script_id?:str,collection_day?:str}
""")
_t("camera", "cam", "Obs", "S0", "anchor", "site_id camera_label", """
site_id id
camera_label str
mount_height_m? f64
viewpoint_class enum{ceiling,high_oblique,eye_level,other}
fov_polygon_w? list<list<f64>[2]>
declared_overlap_camera_ids list<id>
""")
_t("source_file", "src", "Obs", "S0", "anchor", "sha256", """
sha256 str
size_bytes i64
container str
codec str
uri str
privacy_state enum{synthetic_no_persons,contains_identifiable_persons,redacted_derivative}
retention_policy_id id
""")
_t("recording", "rec", "Obs", "S0", "anchor", "src_id session_id camera_id registration_label", """
src_id id
session_id id
camera_id id
registration_label str
timeline_id id
""")
_t("timeline", "tl", "Obs", "S0", "anchor", "kind anchor_id", """
kind timeline_kind
anchor_id id
extent_start_tl_s? f64
extent_end_tl_s? f64
extent_source enum{session_metadata,recording_extent}
""")
_t("clock_alignment", "clk", "Obs", "S0", "anchor", "recording_id method version", """
recording_id id
timeline_id id
method enum{hardware_sync,dataset_supplied_sync,shared_visual_event,contiguous_file_sequence}
version str ~
offset_s f64
drift_ppm f64
sigma_s f64 @ge0
evidence_ref str
prov_class prov_class
""")
_t("camera_group", "cgp", "Obs", "S0", "anchor", "timeline_id camera_ids", """
timeline_id id
camera_ids list<id>
grouping_basis enum{declared_overlap,calibrated_overlap,whole_session}
""")
_t("world_frame", "wf", "Obs", "S0", "anchor", "site_id label version", """
site_id id
label str
version str
origin_description str
transform_from_dataset? list<f64>[16]
unit_status unit_status
prov_class prov_class
""")
_t("calibration", "cal", "Obs", "S0", "anchor", "camera_id calibration_tier method valid_from_us version", """
camera_id id
world_frame_id id
calibration_tier calibration_tier
method enum{dataset_supplied,checkerboard_plus_survey,survey_points_pnp,survey_points_pnp_ground_only}
version str ~
valid_from_us i64
valid_to_us? i64
intrinsics_K? list<f64>[9]
R_cam_from_world? list<f64>[9]
t_cam_from_world_m? list<f64>[3]
distortion_model? enum{none,opencv_radtan5,opencv_fisheye4}
distortion_coeffs? list<f64>
homography_assumes_undistorted bool
homography_img_to_floor? list<f64>[9]
reproj_error_px_rmse? f64
heldout_ground_error_m_rmse? f64
quality_state enum{validated_gv02,supplied_unvalidated,failed}
height_reference_ids list<str>
""")
_t("context_map", "ctx", "Obs", "S0", "anchor", "site_id version", """
site_id id
version str
zones list<struct{zone_id:str,label:str,polygon_w:list<list<f64>[2]>}>
height_references list<struct{height_ref_id:str,label:str,kind:enum{rack_beam,marker_pole,surveyed_point},position_w:list<f64>[3],height_m:f64,sigma_m:f64}>
prov_class prov_class
""")

# Section 5.2 configuration records (configuration class, F.1 A1.2).
_t("footprint_prior", "fpp", "Config", "-", "configuration", "", """
class object_class
label str
shape enum{disc,oriented_rect}
radius_m? f64
length_m? f64
width_m? f64
anchor enum{box_bottom_centre,rear_axle,centre}
source str
sigma_length_m f64
sigma_width_m f64
version_label? str ~
""")
_t("substrate_config", "sbc", "Config", "-", "configuration", "", """
g_max i32 ~
pair_classes list<enum{forklift,pallet_truck}> ~
v_min f64 ~
k_sup f64 ~
motion_models list<str> ~
prediction_horizon_s f64 ~
version_label? str ~
""")
_t("clearance_band_scheme", "bsc", "Config", "-", "configuration", "", """
edges_m list<f64>
bands list<struct{lower_m?:f64,upper_m?:f64}>
version_label? str ~
""")
_t("rule_configuration", "rcf", "Config", "-", "configuration", "", """
experiment enum{E1}
providers list<struct{provider_id:enum{R1,R2,R3,R4,R5,R6},enabled:bool,params:map<str,f64>}>
lifecycle struct{m_gap_frames:i32,t_min_s:f64,w_post_s:f64}
classification struct{d_nm_m:f64,k_sigma:f64,k_c:f64,k_c_turn:f64,o_max_frac:f64,w_e_s:f64}
motion_models list<str> ~
substrate_config_id id
band_scheme_id id
preregistration_ref? str
version_label? str ~
""")

_t("decode_config", "dcf", "Config", "-", "configuration", "", """
k_sup f64 ~
f_untimed f64 ~
f_sub f64 ~
rules_version str ~
delta_nom_declarations list<struct{recording_id:id,delta_nom_s:f64,evidence_ref:str}> ~
final_frame_support enum{delta_nom,zero} ~
version_label? str ~
""")
_t("geometry_config", "gcf", "Config", "-", "configuration", "", """
w_v_s f64 ~
v_part f64 ~
motion_models list<str> ~
footprint_prior_ids list<id> ~
version_label? str ~
""")
_t("sampling_plan_config", "spc", "Config", "-", "configuration", "", """
sample_type sample_type ~
w_ref_s f64 ~
w_guard_s f64 ~
tiling_origin_tl_s f64 ~
strata list<struct{stratum_id:str,definition:str,n_h:i64}> ~
seed i64 ~
version_label? str ~
""")

# Section 5.3.
_t("decode_summary", "dsm", "Obs", "S1", "observation", "recording_id", """
recording_id id
decoder_build str
width_px i32
height_px i32
time_base_num i64
time_base_den i64
n_frames_decoded i64
n_frames_timed i64
n_frames_eligible i64
reorder_depth i32
vfr_detected bool
delta_nom_s f64
delta_nom_source enum{declared_config,median_adjacent_pairs,median_all_timed}
delta_nom_declared_s? f64
delta_nom_median_s? f64
substituted_support_frac f64
untimed_frac f64
extent_start_tl_s f64
extent_end_tl_s f64
rejected bool
""")
_t("frame", None, "Obs", "S1", "observation", "recording_id decode_seq", """
recording_id id
decode_seq i64
frame_index? i64
pts? i64
ts_source enum{pts,best_effort,dts_derived,none}
ts_status enum{ok,duplicate,reordered,substituted,untimed}
t_resolved_s? f64
t_tl_s? f64
decode_ok bool
quality_flags list<quality_flag>
eligible bool
support_start_tl_s? f64
support_s f64 @ge0
support_status enum{measured,capped,final_assumed,substituted,excluded_own_support,timing_uncertain,zero_duplicate,zero_untimed}
""")
_t("coverage_segment", "cov", "Obs", "S1", "observation", "timeline_id camera_id t_start_us=t_start_tl_s", """
timeline_id id
camera_id id
recording_id? id
t_start_tl_s f64
t_end_tl_s f64
start_frame? i64
end_frame_excl? i64
coverage_state coverage_state
support_s f64 @ge0
unusable_reasons list<enum{frozen,black,overexposed,blurred,compression_damage,decode_error,excluded_frame,untimed_frame,timing_substituted}>
rules_version str
""")

# Section 5.4.
_t("detection", "det", "Obs", "S2", "observation", "recording_id frame_index det_index", """
recording_id id
frame_index i64
det_index i32
class object_class
bbox_xyxy_px list<f64>[4] @bbox
truncated bool
score f64 @01
score_calibrated? f64
model_component_id id
""")
_t("track", "trk", "Obs", "S3", "observation", "recording_id track_local_id", """
recording_id id
track_local_id i64
class object_class
start_frame i64
end_frame_excl i64
span_s f64
t_detected_s f64
t_inferred_s f64
t_insufficient_s f64
n_gaps i32
max_gap_frames i32
id_switch_suspect bool
""")
_t("track_point", "tpt", "Obs", "S3", "observation", "track_nk frame_index", """
track_nk nk
frame_index i64
detection_id? id
bbox_xyxy_px list<f64>[4] @bbox
state enum{tracked,predicted,lost}
foot_point_px list<f64>[2]
evidence_class evidence_class
""")

# Section 5.5.
_t("object_state", "ost", "Obs", "S4", "observation", "track_id frame_index", """
track_id id
frame_index i64
geometry_method geometry_method
calibration_id? id
world_frame_id? id
x_m? f64
y_m? f64
pos_cov_m2? list<f64>[3]
sigma_status sigma_status
yaw_rad? f64
yaw_sigma_rad? f64
footprint_prior_id id
speed_mps? f64
speed_sigma_mps? f64
heading_rad? f64
smoothing_window_s f64
evidence_state evidence_state
evidence_class evidence_class
visibility_frac? f64
""")
_t("pow", "pow", "Obs", "S4", "observation", "person_track_id forklift_track_id start_frame", """
person_track_id id
forklift_track_id id
start_frame i64
end_frame_excl i64
recording_id id
timeline_id id
camera_id id
t_start_tl_s f64
t_end_tl_s f64
span_s f64
t_detected_s f64
t_inferred_s f64
t_insufficient_s f64
bridged_gaps list<struct{start_frame:i64,end_frame_excl:i64}>
end_reason enum{track_end_person,track_end_forklift,gap_exceeded,id_switch,coverage_gap,recording_end}
continuation_of_nk? nk
""")
_t("pair_series", "psr", "Obs", "S4", "observation", "pow_nk frame_index", """
pow_nk nk
frame_index i64
clearance_m? f64
clearance_sigma_m? f64
sigma_status sigma_status
clearance_state enum{measured,unmeasurable_uncalibrated,unmeasurable_occluded,unmeasurable_geometry_failure}
footprint_overlap tri
image_gap_px? f64 ~
image_gap_norm? f64 ~
closing_rate_mps? f64
ttca_s? f64
predicted list<struct{motion_model_id:str,horizon_s:f64,pred_min_clearance_m:f64,sigma_m?:f64,t_at_min_s:f64}> ~
q_state enum{sufficient,insufficient}
q_reasons list<q_reason>
evidence_class evidence_class
borderline_flags list<enum{footprint_orientation_unknown}> ~
""")
_t("exposure_profile", "exp", "Obs", "S4", "observation", "subject_type subject_nk band_scheme_id", """
subject_type enum{pow,gpw}
subject_nk nk
band_scheme_id id
t_total_support_s f64
t_in_band_detected_s list<f64>
t_in_band_inferred_s list<f64>
t_clearance_unknown_s f64
t_insufficient_s f64
t_moving_detected_s f64
t_moving_inferred_s f64
t_stationary_detected_s f64
t_stationary_inferred_s f64
t_motion_unknown_s f64
t_joint_visible_s f64
sigma_status sigma_status
calibration_tier enum{calibrated_validated,calibrated_unvalidated,uncalibrated}
""")
_t("activity_segment", "act", "Obs", "S4", "observation", "timeline_id camera_id t_start_us=t_start_tl_s", """
timeline_id id
camera_id id
t_start_tl_s f64
t_end_tl_s f64
coverage_segment_id id
coverage_state coverage_state
ai_activity_state ai_activity_state
support_s f64 @ge0
perception_artifact_id? id
""")
_t("gpw", "gpw", "Obs", "S4", "observation", "member_pow_nks", """
member_pow_nks list<nk>
timeline_id id
t_start_tl_s f64
t_end_tl_s f64
link_median_mahalanobis f64
n_overlap_frames i64
calibration_ids list<id>
clock_alignment_ids list<id>
link_method_version str
""")

# Section 5.6.
_t("flag_series", None, "Obs", "S5", "observation", "pow_id frame_index", """
pow_id id
frame_index i64
P tri
M tri
X tri
E tri
G tri
Q tri
C_any tri
T tri
C_by_provider map<enum{R3,R4,R5},tri>
""")
_t("episode", "ep", "Obs", "S5", "observation", "pow_id start_frame", """
pow_id id
start_frame i64
end_frame_excl i64
attr_end_frame_excl i64
experiment enum{E1}
classification_contract enum{E1_v1}
recording_id id
camera_id id
timeline_id id
continuation_of_nk? nk
t_start_tl_s f64
t_end_tl_s f64
span_s f64
duration_detected_s f64
duration_inferred_s f64
duration_insufficient_s f64
support_detected_frac? f64
P_ep bool
X_ep bool
C_ep bool
C_ep_by_provider map<enum{R3,R4,R5},bool>
E_ep tri
e_assessed bool
K tri
minclr_m? f64
minclr_sigma_m? f64
minclr_frame? i64
closest_approach_frame? i64
ca_observed bool
contact_state contact_state
lbl_O bool
lbl_H bool
lbl_PC bool
lbl_NM bool
lbl_UD bool
lbl_CT bool
lbl_IE bool
summary_label summary_label
review_route bool
borderline_flags list<enum{clearance_within_k_sigma,speed_near_v_min,onset_sensitive,footprint_orientation_unknown}>
label_stability_frac? f64
exp_t_in_band_detected_s list<f64>
exp_t_in_band_inferred_s list<f64>
exp_t_clearance_unknown_s f64
exp_speed_at_ca_mps? f64
exp_closing_rate_max_mps? f64
exp_ttca_min_s? f64
exp_evasive_score? f64
exp_visible_frac? f64
""")
_t("discarded_episode", "dep", "Obs", "S5", "observation", "pow_id start_frame", """
pow_id id
start_frame i64
end_frame_excl i64
span_s f64
discard_reason enum{shorter_than_t_min}
""")
_t("event_link", "lnk", "Obs", "S5", "observation", "episode_a_nk episode_b_nk", """
episode_a_nk nk
episode_b_nk nk
edge enum{L,P,D,U}
time_offset_s? f64
clock_sigma_s? f64
median_mahalanobis? f64
n_overlap_frames i64
basis list<enum{calibrated_geometry,declared_fov_overlap,same_camera,fov_disjoint,time_disjoint,metadata_missing,different_timeline}>
link_conflict bool
linkage_version str
""")
_t("candidate_event", "evt", "Obs", "S5", "observation", "scenario member_episode_nks", """
scenario scenario
member_episode_nks list<nk>
t_onset_tl_s? f64
t_end_tl_s? f64
P_ev bool
X_ev bool
C_ev bool
E_ev tri
K_ev tri
minclr_ev_m? f64
contact_state_ev contact_state
lbl_O bool
lbl_H bool
lbl_PC bool
lbl_NM bool
lbl_UD bool
lbl_CT bool
lbl_IE bool
summary_label summary_label
review_route bool
grouping_algorithm_version str
join_sequence list<str>
edges_used list<struct{a_nk:str,b_nk:str,edge:enum{L,P,D,U}}>
alternative_groups map<str,list<str>>
ambiguous bool
unresolved_members list<str>
""")
_t("event_count_summary", "ecs", "Obs", "S5", "observation", "scope_type scope_id scenario label", """
scope_type enum{reference_window,recording,timeline,split_partition}
scope_id str
scenario scenario
label str
n_events i64
n_ambiguous_groups i64
n_unresolved_identity_episodes i64
assumptions list<struct{assumption:enum{A1,A2,A3},status:enum{unverified,sample_supported},evidence_ref?:str}>
wording enum{scenario_count}
""")

# Section 5.7.
_t("load_state", "lds", "Obs", "S4-E2", "observation", "track_id frame_index method", """
track_id id
frame_index i64
method enum{image_heuristic,height_reference_plane,simulator_truth,reference_measured}
calibration_id? id
elevation_state enum{on_floor,carried_low,elevated,in_rack,unknown}
height_m? f64
height_sigma_m? f64
height_reference_id? id
carrier_forklift_track_id? id
load_mass_kg? f64
load_mass_prov? enum{externally_supplied}
load_mass_sigma_kg? f64
evidence_class evidence_class
""")
_t("e2_occupancy_series", "e2s", "Obs", "S4-E2", "observation", "person_track_id load_track_id frame_index method", """
person_track_id id
load_track_id id
frame_index i64
method enum{image_overlap_baseline,projected_footprint}
occupancy tri
region_polygon_w? list<list<f64>[2]>
margin_m? f64
person_position_sigma_m? f64
q_state enum{sufficient,insufficient}
evidence_class evidence_class
""")
_t("e2_occupancy_profile", "e2p", "Obs", "S4-E2", "observation", "person_track_id load_track_id method", """
person_track_id id
load_track_id id
method enum{image_overlap_baseline,projected_footprint}
t_coobserved_s f64
t_occupied_detected_s f64
t_occupied_inferred_s f64
t_not_occupied_s f64
t_occupancy_unknown_s f64
""")

# Section 5.8 (types inferred; the contract's table gives names and enums only).
_t("sampling_plan", "spl", "Val", "V0", "observation", "plan_label version", """
plan_label str
version str
sample_type sample_type
split_version_id id
population_definition_ref str
supersedes_plan_id? id
frame_definition struct{camera_group_ids:list<id>,w_ref_s:f64,w_guard_s:f64,tiling_origin_tl_s:f64}
frame_sha256 str
strata list<struct{stratum_id:str,definition:str,N_h:i64,n_h:i64}>
stratifier_inputs list<str>
seed i64
frozen_utc ts @event
ecs_selection_basis? str
""", True)
_t("reference_window", "rwn", "Val", "V0", "observation", "plan_nk camera_group_id window_index", """
plan_nk nk
camera_group_id id
timeline_id id
window_index i64
t_start_tl_s f64
t_end_tl_s f64
window_length_s f64 @ge0
t_guard_end_tl_s f64
stratum_id str
sample_type sample_type
inclusion_prob? f64
weight? f64
exhaustive bool
annotation_status enum{planned,in_progress,double_annotated,adjudicated,locked}
locked_utc? ts @event
lock_sha256? str
split_version_id id
partition_at_sampling str
leakage_group_id str
""", True)
_t("annotator", "anr", "Val", "V1", "human", "", """
role enum{a_layer,b_layer,c_layer_reviewer,adjudicator,study_participant}
qualification_ref str
independence_attestation bool
pseudonym str
""", True)
_t("annotation_record", "anc", "Val", "V1", "human", "", """
annotator_id id
window_id id
layer enum{A,B}
namespace namespace
label_source label_source
teacher_model_id? id
teacher_version? str
prompt? str
thresholds? map<str,f64>
target_kind enum{object_presence,interaction,geometry,coverage}
payload str
tool str
submitted_utc ts
blind_to_system bool
""", True)
_t("ref_object_presence", "rop", "Val", "CV-SIM", "observation", "window_id camera_id physical_identity_id", """
window_id id
camera_id id
class object_class
physical_identity_id str
presence_intervals list<struct{start_frame:i64,end_frame_excl:i64}>
keyframes list<struct{frame_index:i64,bbox_xyxy_px:list<f64>[4],evidence_state:evidence_state}>
keyframe_interval_s f64
consensus_method consensus_method
source_record_ids list<id>
prov_class enum{human_observed,simulator_truth}
label_source label_source
reference_class reference_class
""", True)
_t("ref_interaction", "rin", "Val", "CV-SIM", "observation", "window_id person_identity_id forklift_identity_id t_onset_us=t_onset_tl_s", """
window_id id
person_identity_id str
forklift_identity_id str
per_camera list<struct{camera_id:id,start_frame:i64,end_frame_excl:i64,assessable:bool}>
t_onset_tl_s f64
t_offset_tl_s f64
assessability enum{assessable,not_assessable}
visible_contact enum{yes,no_visible_contact,cant_tell}
evasive_action enum{yes,no,cant_tell}
evasive_onset_tl_s? f64
boundary_agreement_iou? f64
consensus_method consensus_method
source_record_ids list<id>
prov_class prov_class
label_source label_source
reference_class reference_class
""", True)
_t("ref_geometry", "rgm", "Val", "CV-SIM", "observation", "window_id physical_identity_id camera_id frame_index", """
window_id id
physical_identity_id str
camera_id id
frame_index i64
x_m f64
y_m f64
sigma_m f64
method enum{simulator_truth,reference_survey,reference_click}
click_count i32
click_spread_m? f64
world_frame_id id
interp_method str
label_source label_source ~
reference_class reference_class
""", True)
_t("ref_coverage_label", "rcl", "Val", "CV-SIM", "observation", "window_id camera_id t_start_us=t_start_tl_s", """
window_id id
camera_id id
timeline_id id
t_start_tl_s f64
t_end_tl_s f64
start_frame? i64
end_frame_excl? i64
ref_activity_state ref_activity_state
unobservable_reason? enum{not_recorded,gap_unobserved,unusable_footage,outside_view,occluded_region,other}
eligible_support_s f64 @ge0
prov_class prov_class
label_source label_source
reference_class reference_class
""")
_t("reviewer_assessment", "rva", "Val", "V3", "human", "", """
annotator_id id
namespace namespace
target_type enum{ref_event,system_episode,system_event}
target_id id
label enum{nm,ud,ct,not_hazardous,unsure}
confidence f64
rationale str
blind bool
shown_system_output bool
submitted_utc ts
""", True)
_t("adjudication", "adj", "Val", "V4", "human", "", """
target_type enum{ref_event,system_episode,system_event}
target_id id
namespace namespace
final_label enum{nm,ud,ct,not_hazardous,unsure}
tier enum{tier1,tier2}
method str
assessment_ids list<id>
agreement_stat_ref? str
prov_class enum{human_adjudicated}
reference_class reference_class
""", True)
_t("validation_status_log", None, "Val", "V4", "human", "", """
seq i64
status_id id
target_type str
target_id id
config_id id
status enum{unreviewed,confirmed,rejected,disputed}
layer str
namespace namespace
basis_ids list<id>
actor_id id
created_utc ts
prev_hash str
record_hash str
""", True)

# Section 5.9 (types inferred where the contract's table gives names and enums only).
_t("split_manifest", "spm", "Eval", "X0b", "observation", "split_label version", """
split_label str
version str
parent_version_id? id
basis enum{metadata_only,metadata_plus_reference_identity}
tier enum{T1,T2a,T2b,T3,synthetic_to_real}
leakage_groups list<struct{leakage_group_id:str,member_recording_ids:list<id>,edge_types:list<str>}>
assignments list<struct{leakage_group_id:str,partition:str}>
t2b_shared_sessions? list<id>
shared_scene_content bool
training_manifest_hashes list<str>
frozen_utc ts @event
revision? struct{audit_id:id,moved_groups:list<str>,rule:enum{PR-01}}
""", True)
_t("leakage_audit", "lka", "Eval", "X0c", "observation", "split_version_id audit_seq", """
split_version_id id
audit_seq i64
tier enum{T1,T2a,T2b,T3,synthetic_to_real}
edges_added list<struct{recording_a:id,recording_b:id,edge_type:str,evidence_ref:str}>
violations list<struct{leakage_group_id:str,partitions:list<str>}>
discovery_basis enum{metadata,sampled_annotation}
audit_complete bool
""", True)
_t("match_record", "mat", "Eval", "S8", "observation", "window_id config_id scenario label_group ref_event_id system_event_id", """
window_id id
config_id id
scenario scenario
label_group enum{G1,G2,any}
ref_event_id? id
system_event_id? id
match_type enum{matched,duplicate_alert,false_alert,miss,abstained_miss,unobservable_reference}
temporal_iou? f64
onset_error_s? f64
offset_error_s? f64
reference_class reference_class
""", True)
_t("error_attribution", "era", "Eval", "S8", "observation", "match_nk", """
match_nk nk
primary_stage enum{evidence_unavailable,perception,tracking,geometry,event_reasoning,linkage,reference_ambiguity,unresolved}
secondary_factors list<str>
attribution_status enum{verified_oracle_single,verified_oracle_joint,diagnostic_inferred,unresolved}
oracle_artifact_ids list<id>
rule_test_results map<str,str>
""", True)
_t("completeness_record", "cmr", "Eval", "S8", "observation", "window_id metric_id support_basis config_id stratum", """
window_id id
metric_id enum{CM-01,CM-02,CM-03,CM-04,CM-05,CM-06,CM-07,CM-08,CM-09,CM-10}
support_basis support_basis
config_id? id
stratum map<str,str>
numerator f64
denominator f64
value? f64
interp_method str
iou_cm f64
k_kf_s f64
""", True)
_t("metric_result", "mtr", "Eval", "S8", "observation", "metric_id definition_version config_id scenario label support_basis sample_type estimand weighted slice", """
metric_id str
definition_version str
split_version_id id
config_id? id
scenario? scenario
label? str
support_basis? support_basis
slice map<str,str>
sample_type sample_type
estimand enum{frame_description,new_session_performance,conditional_on_selection}
estimand_validity enum{design_valid,requires_resample,conditional_on_selection}
validity enum{valid,invalidated_leakage}
leakage_screening_status enum{passed_available_screening}
weighted bool
value? f64
ci_low? f64
ci_high? f64
ci_level? f64
interval_method enum{stratified_window_bootstrap,cluster_bootstrap,wilson,bland_altman,none}
n_units i64
n_events i64
eff_n f64
counts_only? bool
shared_scene_content bool
claim_level enum{L1,L2,L3,L4,L5,none}
coverage_companion_id? id
reference_class reference_class
""", True)
_t("acceptance_criterion", "acc", "Eval", "pre-reg", "configuration", "criterion_label version", """
criterion_label str
version str
output_id str
criterion_type enum{technical_accuracy,completeness,repeatability,parameter_robustness,comparability}
metric_id str
slice map<str,str>
rule enum{ci_upper_le,ci_lower_ge,abs_bias_ci_within,exact_equal,flip_rate_le}
target f64
ci_level f64
estimand enum{frame_description,new_session_performance,conditional_on_selection}
n_min_units i64
preregistration_ref str
frozen_utc ts @event
""", True)
_t("measurement_fitness", "fit", "Eval", "S8f", "observation", "scope", """
scope struct{output_id:str,measurement_definition_version:str,data_origin:data_origin,condition_stratum:str,calibration_tier:str,config_id:id,intended_use:enum{observation_description,exposure_duration_measurement,candidate_event_screening,rq2_candidate_input},criterion_ids:list<id>}
criterion_decisions map<str,enum{met,not_met,inconclusive,not_assessable}>
measurement_status enum{technically_validated,experimental,unsuitable_under_tested_conditions,not_yet_assessable}
failing_interval? struct{low:f64,high:f64}
construct_status enum{CV0,CV1,CV2}
construct_evidence struct{definition_evidence_ref?:str,source_refs?:list<str>,expert_alignment_result_id?:id}
parameter_sensitive bool
override? struct{downgrade_only:bool,rationale:str,actor:str}
interpretation_note str
""", True)

# F.1 A5.2.
_t("track_identity_assoc", "tia", "Eval", "S8", "observation", "window_id camera_id frame_index track_id physical_identity_id", """
window_id id
camera_id id
frame_index i64
track_id? id
physical_identity_id? str
status enum{matched,ambiguous,unmatched_system,missed_reference}
""", True)
_t("track_identity_summary", "tis", "Eval", "S8", "observation", "window_id track_id", """
window_id id
track_id id
dominant_identity_id? str
dominant_share? f64
n_identities i32
n_switches i32
status enum{one_to_one,id_switch,fragment,unmatched_system}
""", True)

# Section 2.5 and 5.10 governance.
_t("execution", None, "Gov", "-", "execution", "", """
run_id id
artifact_spec_id str
artifact_id? str
stage str
started_utc ts
ended_utc ts
host str
platform struct{cpu:str,gpu?:str,driver?:str}
status enum{complete,failed}
compared_to_artifact_id? str
tolerance_report_ref? str
logs_ref str
""", True)
_t("evidence_clip", "ecl", "Gov", "S6", "observation", "recording_id start_frame end_frame_excl purpose", """
recording_id id
start_frame i64
end_frame_excl i64
purpose enum{review,reference_annotation,report_figure}
decoded_frame_sha256 list<str>
encoding str
redaction_state enum{none,faces_blurred,other}
access_class enum{restricted_research,team_internal,publishable_synthetic_only}
retention_policy_id id
expires_utc? ts
""", True)
_t("retention_policy", "rtp", "Gov", "-", "human", "", """
label str
applies_to str
retain_days? i64
deletion_method str
legal_basis_ref? str
""", True)
_t("access_log", "alg", "Gov", "-", "human", "", """
actor str
action enum{read,export,delete,policy_change}
target str
purpose str
time ts
""", True)
_t("stage_error", "ser", "Gov", "-", "execution", "run_id error_index", """
run_id id
error_index i64
code str
severity enum{data_recorded,stage_fatal}
recording_id? id
frame_range? struct{start_frame:i64,end_frame_excl:i64}
message str
contract_ref str
""", True)

DEFINITIONS = _D
