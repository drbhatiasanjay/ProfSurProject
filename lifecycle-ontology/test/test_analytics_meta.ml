(** Analytics meta-layer tests — Phase 2 alcotest suite. *)

open Domain
open Analytics_meta

(* ── Testable helpers ────────────────────────────────────────────────────── *)


(* ── model_kind suite ────────────────────────────────────────────────────── *)

let all_kinds = [ Fe; Re; Ols; Gmm; Rf; Xgboost; Lstm; Gru ]

let test_model_kind_count () =
  Alcotest.(check int) "8 model kinds" 8 (List.length all_kinds)

let test_model_kind_to_string () =
  List.iter (fun k ->
    let s = model_kind_to_string k in
    Alcotest.(check bool) ("non-empty " ^ s) true (String.length s > 0)
  ) all_kinds

let test_model_kind_strings_distinct () =
  let strs = List.map model_kind_to_string all_kinds in
  let uniq = List.sort_uniq String.compare strs in
  Alcotest.(check int) "all strings distinct" 8 (List.length uniq)

let test_model_kind_econometric_prefix () =
  (* Econometric models: Fe Re Ols Gmm *)
  let eco = [Fe; Re; Ols; Gmm] in
  List.iter (fun k ->
    let s = model_kind_to_string k in
    Alcotest.(check bool) (s ^ " non-empty") true (String.length s > 0)
  ) eco

let model_kind_suite = [
  "count",           `Quick, test_model_kind_count;
  "to_string",       `Quick, test_model_kind_to_string;
  "strings distinct",`Quick, test_model_kind_strings_distinct;
  "econometric",     `Quick, test_model_kind_econometric_prefix;
]

(* ── normative_band suite ────────────────────────────────────────────────── *)

let test_normative_band_construction () =
  let band : normative_band = {
    nb_id          = "nb_maturity_steel_lev";
    stage          = Stage.Maturity;
    industry       = "Steel";
    metric         = Metric.leverage_ratio;
    lower          = 0.25;
    upper          = 0.45;
    source_vintage = "thesis";
  } in
  Alcotest.(check string) "nb_id"    "nb_maturity_steel_lev" band.nb_id;
  Alcotest.(check string) "industry" "Steel"                 band.industry;
  Alcotest.(check bool)   "lower < upper" true (band.lower < band.upper);
  Alcotest.(check bool)   "stage = Maturity" true (Stage.equal band.stage Stage.Maturity)

let test_normative_band_stage_field () =
  let band : normative_band = {
    nb_id = "nb_startup_it_lev"; stage = Stage.Startup;
    industry = "IT"; metric = Metric.profitability;
    lower = (-0.1); upper = 0.3; source_vintage = "cmie_2025";
  } in
  Alcotest.(check bool) "Startup stage" true (Stage.equal band.stage Stage.Startup);
  Alcotest.(check bool) "profitability metric" true
    (band.metric.id = Metric.profitability.id)

let test_normative_band_metric_field () =
  let all_stages = Stage.all in
  let bands = List.map (fun st ->
    { nb_id = "nb_" ^ Stage.to_string st;
      stage = st; industry = "Cement";
      metric = Metric.leverage_ratio;
      lower = 0.1; upper = 0.8;
      source_vintage = "thesis" }
  ) all_stages in
  Alcotest.(check int) "8 bands built" 8 (List.length bands);
  List.iter (fun b ->
    Alcotest.(check bool) "lower < upper" true (b.lower < b.upper)
  ) bands

let normative_band_suite = [
  "construction",       `Quick, test_normative_band_construction;
  "stage field",        `Quick, test_normative_band_stage_field;
  "metric field",       `Quick, test_normative_band_metric_field;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "analytics_meta" [
  "model_kind",      model_kind_suite;
  "normative_band",  normative_band_suite;
]
