(** Phase 4 — Scenario DSL / shock application tests. *)

open Domain

(* ── Helpers ─────────────────────────────────────────────────────────────── *)

let lev_shock delta   = Scenario.{ metric = Metric.leverage_ratio; delta }
let prof_shock delta  = Scenario.{ metric = Metric.profitability;  delta }
let tang_shock delta  = Scenario.{ metric = Metric.tangibility;    delta }

let baseline = [
  ("leverage_ratio", 0.40);
  ("profitability",  0.12);
  ("tangibility",    0.55);
  ("firm_size",      3.50);
]

let approx_eq a b = abs_float (a -. b) < 1e-9

(* ── make / make_validated tests ────────────────────────────────────────── *)

let test_make_basic () =
  let sc = Scenario.make ~id:"sc1" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity ~shocks:[lev_shock (-0.05)] () in
  Alcotest.(check string) "id"     "sc1"     sc.id;
  Alcotest.(check string) "stage"  "Maturity" (Stage.to_string sc.stage);
  Alcotest.(check int)    "shocks" 1         (Scenario.shock_count sc)

let test_make_validated_ok () =
  let r = Scenario.make_validated ~id:"sc2" ~persona:Persona.RatingAnalyst
            ~stage:Stage.Growth
            ~shocks:[lev_shock 0.05; prof_shock (-0.02)] () in
  Alcotest.(check bool) "Ok" true (Result.is_ok r)

let test_make_validated_empty_shocks () =
  let r = Scenario.make_validated ~id:"sc3" ~persona:Persona.CorporateCFO
            ~stage:Stage.Startup ~shocks:[] () in
  Alcotest.(check bool) "empty shocks → Error" true (Result.is_error r)

let test_make_validated_duplicate_metrics () =
  let r = Scenario.make_validated ~id:"sc4" ~persona:Persona.CorporateCFO
            ~stage:Stage.Growth
            ~shocks:[lev_shock 0.05; lev_shock (-0.03)] () in
  Alcotest.(check bool) "duplicate → Error" true (Result.is_error r)

let constructor_suite = [
  "make basic",              `Quick, test_make_basic;
  "make_validated ok",       `Quick, test_make_validated_ok;
  "empty shocks error",      `Quick, test_make_validated_empty_shocks;
  "duplicate metrics error", `Quick, test_make_validated_duplicate_metrics;
]

(* ── Predicate tests ─────────────────────────────────────────────────────── *)

let test_is_stress_all_negative () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Shakeout1
             ~shocks:[lev_shock 0.08; prof_shock (-0.03)] () in
  Alcotest.(check bool) "mixed → stress" true (Scenario.is_stress_scenario sc)

let test_is_stress_all_positive () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.PEVCInvestor
             ~stage:Stage.Growth
             ~shocks:[lev_shock 0.05; prof_shock 0.02] () in
  Alcotest.(check bool) "all positive → not stress" false (Scenario.is_stress_scenario sc)

let test_is_recovery () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.PEVCInvestor
             ~stage:Stage.Decline
             ~shocks:[lev_shock (-0.10); prof_shock 0.05] () in
  Alcotest.(check bool) "mixed → not recovery" false (Scenario.is_recovery_scenario sc);
  let sc2 = Scenario.make ~id:"s2" ~persona:Persona.CorporateCFO
              ~stage:Stage.Decline
              ~shocks:[prof_shock 0.08; tang_shock 0.03] () in
  Alcotest.(check bool) "all positive → recovery" true (Scenario.is_recovery_scenario sc2)

let test_shock_count () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.RatingAnalyst
             ~stage:Stage.Maturity
             ~shocks:[lev_shock 0.01; prof_shock (-0.02); tang_shock 0.03] () in
  Alcotest.(check int) "3 shocks" 3 (Scenario.shock_count sc)

let predicate_suite = [
  "is_stress mixed",      `Quick, test_is_stress_all_negative;
  "is_stress all positive",`Quick, test_is_stress_all_positive;
  "is_recovery",           `Quick, test_is_recovery;
  "shock_count",           `Quick, test_shock_count;
]

(* ── Shock application tests ─────────────────────────────────────────────── *)

let test_apply_single_shock () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity ~shocks:[lev_shock (-0.05)] () in
  let results = Scenario.apply sc ~baseline_map:baseline in
  Alcotest.(check int) "1 result" 1 (List.length results);
  let r = List.hd results in
  Alcotest.(check bool) "baseline 0.40"   true (approx_eq r.baseline  0.40);
  Alcotest.(check bool) "shocked  0.35"   true (approx_eq r.shocked   0.35);
  Alcotest.(check bool) "delta_abs -0.05" true (approx_eq r.delta_abs (-0.05))

let test_apply_delta_pct () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity ~shocks:[prof_shock 0.04] () in
  let results = Scenario.apply sc ~baseline_map:baseline in
  let r = List.hd results in
  (* baseline=0.12, delta=0.04, pct = 0.04/0.12*100 ≈ 33.33 *)
  Alcotest.(check bool) "delta_pct ≈ 33.33" true
    (abs_float (r.delta_pct -. (0.04 /. 0.12 *. 100.0)) < 1e-6)

let test_apply_missing_metric_baseline_zero () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Startup
             ~shocks:[Scenario.{ metric = Metric.non_debt_tax_shield; delta = 0.02 }] () in
  let results = Scenario.apply sc ~baseline_map:[] in
  let r = List.hd results in
  Alcotest.(check bool) "baseline=0"    true (approx_eq r.baseline 0.0);
  Alcotest.(check bool) "shocked=delta" true (approx_eq r.shocked  0.02);
  Alcotest.(check bool) "delta_pct=nan" true (Float.is_nan r.delta_pct)

let test_apply_multiple_shocks () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.RatingAnalyst
             ~stage:Stage.Shakeout2
             ~shocks:[lev_shock 0.10; prof_shock (-0.03); tang_shock (-0.05)] () in
  let results = Scenario.apply sc ~baseline_map:baseline in
  Alcotest.(check int) "3 results" 3 (List.length results)

let test_total_shock_magnitude () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity
             ~shocks:[lev_shock (-0.05); prof_shock 0.03] () in
  Alcotest.(check bool) "magnitude = 0.08" true
    (approx_eq (Scenario.total_shock_magnitude sc) 0.08)

let apply_suite = [
  "single shock",              `Quick, test_apply_single_shock;
  "delta_pct",                 `Quick, test_apply_delta_pct;
  "missing metric baseline 0", `Quick, test_apply_missing_metric_baseline_zero;
  "multiple shocks",           `Quick, test_apply_multiple_shocks;
  "total_shock_magnitude",     `Quick, test_total_shock_magnitude;
]

(* ── Label tests ─────────────────────────────────────────────────────────── *)

let test_to_label_stress () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.RatingAnalyst
             ~stage:Stage.Decline ~shocks:[lev_shock 0.15] () in
  let lbl = Scenario.to_label sc in
  Alcotest.(check bool) "label non-empty" true (String.length lbl > 0)

let test_shock_to_label () =
  let s = lev_shock (-0.05) in
  let lbl = Scenario.shock_to_label s in
  Alcotest.(check bool) "contains metric id" true
    (let rec has s p i =
       if i + String.length p > String.length s then false
       else if String.sub s i (String.length p) = p then true
       else has s p (i+1) in
     has lbl "leverage_ratio" 0)

let label_suite = [
  "to_label",        `Quick, test_to_label_stress;
  "shock_to_label",  `Quick, test_shock_to_label;
]

(* ── JSON round-trip tests ───────────────────────────────────────────────── *)

let test_shock_json_round_trip () =
  let s = lev_shock (-0.05) in
  let j = Scenario.shock_to_yojson s in
  match Scenario.shock_of_yojson j with
  | Error msg -> Alcotest.failf "shock round-trip: %s" msg
  | Ok s2 ->
      Alcotest.(check string) "metric_id" s.metric.id s2.metric.id;
      Alcotest.(check bool)   "delta"     true (approx_eq s.delta s2.delta)

let test_scenario_json_round_trip () =
  let sc = Scenario.make ~id:"rt1" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity
             ~shocks:[lev_shock (-0.05); prof_shock 0.02] () in
  let j = Scenario.to_yojson sc in
  match Scenario.of_yojson j with
  | Error msg -> Alcotest.failf "scenario round-trip: %s" msg
  | Ok sc2 ->
      Alcotest.(check string) "id"     sc.id    sc2.id;
      Alcotest.(check int)    "shocks" (Scenario.shock_count sc)
                                       (Scenario.shock_count sc2)

let test_scenario_json_all_personas () =
  List.iter (fun p ->
    let sc = Scenario.make ~id:"p_test" ~persona:p ~stage:Stage.Growth
               ~shocks:[lev_shock 0.01] () in
    let j = Scenario.to_yojson sc in
    match Scenario.of_yojson j with
    | Error msg -> Alcotest.failf "persona %s: %s" (Persona.to_string p) msg
    | Ok sc2    ->
        Alcotest.(check bool) (Persona.to_string p) true
          (Persona.equal sc.persona sc2.persona)
  ) Persona.all

let test_shock_result_to_yojson () =
  let sc = Scenario.make ~id:"s" ~persona:Persona.CorporateCFO
             ~stage:Stage.Maturity ~shocks:[lev_shock (-0.05)] () in
  let results = Scenario.apply sc ~baseline_map:baseline in
  let r = List.hd results in
  let j = Scenario.shock_result_to_yojson r in
  let open Yojson.Safe.Util in
  Alcotest.(check string) "metric_id"  "leverage_ratio" (j |> member "metric_id" |> to_string);
  Alcotest.(check bool)   "delta_abs"  true (j |> member "delta_abs" |> to_float < 0.0)

let json_suite = [
  "shock round-trip",           `Quick, test_shock_json_round_trip;
  "scenario round-trip",        `Quick, test_scenario_json_round_trip;
  "all personas round-trip",    `Quick, test_scenario_json_all_personas;
  "shock_result to_yojson",     `Quick, test_shock_result_to_yojson;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "scenario" [
  "constructor", constructor_suite;
  "predicates",  predicate_suite;
  "apply",       apply_suite;
  "labels",      label_suite;
  "json",        json_suite;
]
