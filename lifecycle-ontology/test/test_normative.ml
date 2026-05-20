(** Phase 4 — Normative band / anomaly tests. *)

open Domain
open Analytics_meta

(* ── Helper ──────────────────────────────────────────────────────────────── *)

let make_band ?(vintage = "thesis") stage lower upper =
  { nb_id          = "test_band";
    stage;
    industry       = "Steel";
    metric         = Metric.leverage_ratio;
    lower;
    upper;
    source_vintage = vintage }

let approx_eq a b = abs_float (a -. b) < 1e-9

(* ── Flag tests ──────────────────────────────────────────────────────────── *)

let test_flag_within () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  Alcotest.(check string) "at midpoint"  "within"
    (Normative.flag_to_string (Normative.check_band band ~value:0.35));
  Alcotest.(check string) "at lower"     "within"
    (Normative.flag_to_string (Normative.check_band band ~value:0.20));
  Alcotest.(check string) "at upper"     "within"
    (Normative.flag_to_string (Normative.check_band band ~value:0.50))

let test_flag_over_levered () =
  let band = make_band Stage.Growth 0.10 0.40 in
  Alcotest.(check string) "above upper" "over-levered"
    (Normative.flag_to_string (Normative.check_band band ~value:0.55))

let test_flag_under_levered () =
  let band = make_band Stage.Startup 0.05 0.30 in
  Alcotest.(check string) "below lower" "under-levered"
    (Normative.flag_to_string (Normative.check_band band ~value:0.01))

let test_flag_of_string_opt () =
  Alcotest.(check bool) "within"        true (Normative.flag_of_string_opt "within"        = Some Normative.Within);
  Alcotest.(check bool) "over-levered"  true (Normative.flag_of_string_opt "over-levered"  = Some Normative.OverLevered);
  Alcotest.(check bool) "under-levered" true (Normative.flag_of_string_opt "under-levered" = Some Normative.UnderLevered);
  Alcotest.(check bool) "unknown"       true (Normative.flag_of_string_opt "bogus"         = None)

let flag_suite = [
  "within",             `Quick, test_flag_within;
  "over-levered",       `Quick, test_flag_over_levered;
  "under-levered",      `Quick, test_flag_under_levered;
  "flag_of_string_opt", `Quick, test_flag_of_string_opt;
]

(* ── Band geometry tests ─────────────────────────────────────────────────── *)

let test_band_width () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  Alcotest.(check bool) "width = 0.30" true (approx_eq (Normative.band_width band) 0.30)

let test_band_midpoint () =
  let band = make_band Stage.Growth 0.10 0.40 in
  Alcotest.(check bool) "midpoint = 0.25" true (approx_eq (Normative.band_midpoint band) 0.25)

let test_percentile_rank_within () =
  let band = make_band Stage.Maturity 0.0 1.0 in
  Alcotest.(check bool) "0.5 → 0.5"  true (approx_eq (Normative.percentile_rank band ~value:0.5)  0.5);
  Alcotest.(check bool) "0.0 → 0.0"  true (approx_eq (Normative.percentile_rank band ~value:0.0)  0.0);
  Alcotest.(check bool) "1.0 → 1.0"  true (approx_eq (Normative.percentile_rank band ~value:1.0)  1.0)

let test_percentile_rank_zero_width () =
  let band = make_band Stage.Startup 0.3 0.3 in
  Alcotest.(check bool) "zero-width → 0.5" true
    (approx_eq (Normative.percentile_rank band ~value:0.3) 0.5)

let geometry_suite = [
  "band_width",              `Quick, test_band_width;
  "band_midpoint",           `Quick, test_band_midpoint;
  "percentile_rank within",  `Quick, test_percentile_rank_within;
  "percentile_rank zero-w",  `Quick, test_percentile_rank_zero_width;
]

(* ── Anomaly score tests ─────────────────────────────────────────────────── *)

let test_anomaly_score_within () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  Alcotest.(check bool) "midpoint → 0" true
    (approx_eq (Normative.anomaly_score band ~value:0.35) 0.0);
  Alcotest.(check bool) "at lower → 0" true
    (approx_eq (Normative.anomaly_score band ~value:0.20) 0.0)

let test_anomaly_score_over () =
  let band = make_band Stage.Growth 0.10 0.40 in
  (* value = 0.55, upper = 0.40, width = 0.30 → score = 0.15/0.30 = 0.5 *)
  Alcotest.(check bool) "score = 0.5" true
    (approx_eq (Normative.anomaly_score band ~value:0.55) 0.5)

let test_anomaly_score_under () =
  let band = make_band Stage.Startup 0.10 0.40 in
  (* value = 0.04, lower = 0.10, width = 0.30 → score = 0.06/0.30 = 0.2 *)
  Alcotest.(check bool) "score = 0.2" true
    (approx_eq (Normative.anomaly_score band ~value:0.04) 0.2)

let test_anomaly_score_zero_width () =
  let band = make_band Stage.Startup 0.3 0.3 in
  Alcotest.(check bool) "zero-width → 0" true
    (approx_eq (Normative.anomaly_score band ~value:0.5) 0.0)

let anomaly_suite = [
  "within → 0",         `Quick, test_anomaly_score_within;
  "over → positive",    `Quick, test_anomaly_score_over;
  "under → positive",   `Quick, test_anomaly_score_under;
  "zero-width → 0",     `Quick, test_anomaly_score_zero_width;
]

(* ── Evaluate / batch tests ──────────────────────────────────────────────── *)

let test_evaluate_within () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  let r = Normative.evaluate band ~value:0.35 in
  Alcotest.(check string) "flag"  "within"  (Normative.flag_to_string r.flag);
  Alcotest.(check bool)   "score" true      (approx_eq r.anomaly_score 0.0);
  Alcotest.(check bool)   "expl"  true      (String.length r.explanation > 0)

let test_evaluate_over () =
  let band = make_band Stage.Growth 0.10 0.40 in
  let r = Normative.evaluate band ~value:0.70 in
  Alcotest.(check string) "flag" "over-levered" (Normative.flag_to_string r.flag);
  Alcotest.(check bool)   "score > 0" true (r.anomaly_score > 0.0)

let contains_sub haystack needle =
  let hl = String.length haystack and nl = String.length needle in
  let rec go i =
    if i + nl > hl then false
    else if String.sub haystack i nl = needle then true
    else go (i + 1) in
  go 0

let test_evaluate_explanation_contains_stage () =
  let band = make_band Stage.Decay 0.05 0.25 in
  let r = Normative.evaluate band ~value:0.50 in
  Alcotest.(check bool) "explanation mentions stage" true
    (contains_sub r.explanation "Decay")

let test_batch_evaluate () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  let pairs = [(band, 0.35); (band, 0.10); (band, 0.65)] in
  let results = Normative.batch_evaluate pairs in
  Alcotest.(check int) "3 results" 3 (List.length results);
  let flags = List.map (fun r -> r.Normative.flag) results in
  Alcotest.(check bool) "first within" true
    (List.nth flags 0 = Normative.Within);
  Alcotest.(check bool) "second under" true
    (List.nth flags 1 = Normative.UnderLevered);
  Alcotest.(check bool) "third over"   true
    (List.nth flags 2 = Normative.OverLevered)

let test_count_flags () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  let pairs = [(band, 0.35); (band, 0.35); (band, 0.10); (band, 0.65); (band, 0.80)] in
  let results = Normative.batch_evaluate pairs in
  let (w, o, u) = Normative.count_flags results in
  Alcotest.(check int) "within=2"       2 w;
  Alcotest.(check int) "over-levered=2" 2 o;
  Alcotest.(check int) "under-levered=1" 1 u

let eval_suite = [
  "evaluate within",         `Quick, test_evaluate_within;
  "evaluate over",           `Quick, test_evaluate_over;
  "explanation has stage",   `Quick, test_evaluate_explanation_contains_stage;
  "batch_evaluate",          `Quick, test_batch_evaluate;
  "count_flags",             `Quick, test_count_flags;
]

(* ── JSON round-trip tests ───────────────────────────────────────────────── *)

let test_flag_json_round_trip () =
  List.iter (fun f ->
    let j = Normative.flag_to_yojson f in
    match Normative.flag_of_yojson j with
    | Error msg -> Alcotest.failf "flag round-trip: %s" msg
    | Ok f2     ->
        Alcotest.(check string) (Normative.flag_to_string f)
          (Normative.flag_to_string f) (Normative.flag_to_string f2)
  ) [ Normative.Within; Normative.OverLevered; Normative.UnderLevered ]

let test_flag_json_error () =
  match Normative.flag_of_yojson (`String "bogus") with
  | Ok _    -> Alcotest.fail "expected Error"
  | Error _ -> ()

let test_normative_result_to_yojson () =
  let band = make_band Stage.Maturity 0.20 0.50 in
  let r = Normative.evaluate band ~value:0.60 in
  let j = Normative.normative_result_to_yojson r in
  let open Yojson.Safe.Util in
  Alcotest.(check string) "flag in JSON" "over-levered"
    (j |> member "flag" |> to_string);
  Alcotest.(check bool)   "anomaly_score > 0" true
    (j |> member "anomaly_score" |> to_float > 0.0)

let json_suite = [
  "flag round-trip",           `Quick, test_flag_json_round_trip;
  "flag unknown error",        `Quick, test_flag_json_error;
  "normative_result to_yojson",`Quick, test_normative_result_to_yojson;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "normative" [
  "flag",     flag_suite;
  "geometry", geometry_suite;
  "anomaly",  anomaly_suite;
  "evaluate", eval_suite;
  "json",     json_suite;
]
