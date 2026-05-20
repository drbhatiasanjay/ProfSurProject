(** Phase 6 — API handler integration tests.
    Handlers are pure functions (JSON string → JSON string) so no server is needed. *)

open Yojson.Safe.Util

(* ── Helpers ─────────────────────────────────────────────────────────────── *)

let parse body =
  try Yojson.Safe.from_string body
  with Yojson.Json_error msg -> Alcotest.failf "bad JSON response: %s" msg

let field_str j k =
  match j |> member k with
  | `String s -> s
  | _ -> Alcotest.failf "field '%s' missing or not a string" k

let has_error j = match j |> member "error" with `String _ -> true | _ -> false

(* ── /health ─────────────────────────────────────────────────────────────── *)

let test_health () =
  let j = parse (Api.handle_health ()) in
  Alcotest.(check string) "status ok" "ok" (field_str j "status");
  Alcotest.(check bool)   "version present" true
    (String.length (field_str j "version") > 0)

let health_suite = [
  "health ok", `Quick, test_health;
]

(* ── /lifecycle_query — macro ────────────────────────────────────────────── *)

let macro_body = {|{
  "level": "macro",
  "persona": "CorporateCFO",
  "panel_mode": "thesis",
  "stage_industry_counts": [
    ["Startup", "Steel", 8], ["Growth", "IT", 22],
    ["Maturity", "Steel", 25], ["Maturity", "IT", 18]
  ],
  "stage_transitions": [
    ["Startup", "Growth", 0.55], ["Growth", "Maturity", 0.48]
  ],
  "crisis_stages": [
    ["GFC", ["Maturity", "Shakeout1"]],
    ["COVID", ["Growth", "Maturity"]]
  ]
}|}

let test_lifecycle_query_macro_level () =
  let j = parse (Api.handle_lifecycle_query macro_body) in
  Alcotest.(check string) "level = macro" "macro" (field_str j "level")

let test_lifecycle_query_macro_node_count () =
  let j = parse (Api.handle_lifecycle_query macro_body) in
  let nc = j |> member "node_count" |> to_int in
  Alcotest.(check bool) "node_count > 0" true (nc > 0);
  Alcotest.(check bool) "node_count ≤ 21" true (nc <= 21)

let test_lifecycle_query_macro_schema () =
  let j = parse (Api.handle_lifecycle_query macro_body) in
  List.iter (fun f ->
    Alcotest.(check bool) ("field " ^ f) true
      (j |> member f <> `Null)
  ) ["level"; "persona"; "panel_mode"; "node_count"; "nodes"; "edges"]

let test_lifecycle_query_macro_persona () =
  let j = parse (Api.handle_lifecycle_query macro_body) in
  Alcotest.(check string) "persona = CorporateCFO" "CorporateCFO"
    (field_str j "persona")

let test_lifecycle_query_bad_json () =
  let j = parse (Api.handle_lifecycle_query "{not valid json") in
  Alcotest.(check bool) "error field present" true (has_error j)

let lifecycle_macro_suite = [
  "macro level field",    `Quick, test_lifecycle_query_macro_level;
  "macro node_count",     `Quick, test_lifecycle_query_macro_node_count;
  "macro schema fields",  `Quick, test_lifecycle_query_macro_schema;
  "macro persona",        `Quick, test_lifecycle_query_macro_persona;
  "bad JSON → error",     `Quick, test_lifecycle_query_bad_json;
]

(* ── /lifecycle_query — meso ─────────────────────────────────────────────── *)

let meso_body = {|{
  "level": "meso",
  "persona": "RatingAnalyst",
  "panel_mode": "latest",
  "companies": [
    ["C001", "TataSteel",   "Maturity",  "Steel", 0.38],
    ["C002", "JSW Steel",   "Maturity",  "Steel", 0.42],
    ["C003", "Infosys",     "Growth",    "IT",    0.15],
    ["C004", "TCS",         "Maturity",  "IT",    0.08],
    ["C005", "SunPharma",   "Startup",   "Pharma",0.22]
  ]
}|}

let test_lifecycle_query_meso_level () =
  let j = parse (Api.handle_lifecycle_query meso_body) in
  Alcotest.(check string) "level = meso" "meso" (field_str j "level")

let test_lifecycle_query_meso_nodes_include_companies () =
  let j = parse (Api.handle_lifecycle_query meso_body) in
  let nodes = j |> member "nodes" |> to_list in
  let company_nodes = List.filter (fun n ->
    field_str n "type" = "company") nodes in
  Alcotest.(check int) "5 company nodes" 5 (List.length company_nodes)

let lifecycle_meso_suite = [
  "meso level field",        `Quick, test_lifecycle_query_meso_level;
  "meso company nodes",      `Quick, test_lifecycle_query_meso_nodes_include_companies;
]

(* ── /lifecycle_query — micro ────────────────────────────────────────────── *)

let micro_body = {|{
  "level": "micro",
  "persona": "PEVCInvestor",
  "panel_mode": "latest",
  "focal_code": "C001",
  "focal_name": "TataSteel",
  "focal_stage": "Maturity",
  "focal_leverage": 0.38,
  "peers": [
    ["C002", "JSW Steel",  "Maturity", 0.42, 0.94],
    ["C003", "SAIL",       "Shakeout1",0.55, 0.88],
    ["C004", "Bhushan",    "Decline",  0.72, 0.75]
  ],
  "crisis_events": ["GFC", "COVID"]
}|}

let test_lifecycle_query_micro_level () =
  let j = parse (Api.handle_lifecycle_query micro_body) in
  Alcotest.(check string) "level = micro" "micro" (field_str j "level")

let test_lifecycle_query_micro_focal_present () =
  let j = parse (Api.handle_lifecycle_query micro_body) in
  let nodes = j |> member "nodes" |> to_list in
  Alcotest.(check bool) "focal node C001 present" true
    (List.exists (fun n ->
       try field_str n "id" = "company_C001" with _ -> false) nodes)

let test_lifecycle_query_micro_event_nodes () =
  let j = parse (Api.handle_lifecycle_query micro_body) in
  let nodes = j |> member "nodes" |> to_list in
  let ev_nodes = List.filter (fun n ->
    try field_str n "type" = "event" with _ -> false) nodes in
  Alcotest.(check int) "2 event nodes (GFC+COVID)" 2 (List.length ev_nodes)

let lifecycle_micro_suite = [
  "micro level field",       `Quick, test_lifecycle_query_micro_level;
  "micro focal node",        `Quick, test_lifecycle_query_micro_focal_present;
  "micro event nodes",       `Quick, test_lifecycle_query_micro_event_nodes;
]

(* ── /explain_stat ───────────────────────────────────────────────────────── *)

let explain_body = {|{
  "stat_id": "leverage_ratio",
  "persona": "RatingAnalyst",
  "value": 0.65,
  "stage": "Maturity",
  "industry": "Steel"
}|}

let test_explain_stat_fields () =
  let j = parse (Api.handle_explain_stat explain_body) in
  List.iter (fun f ->
    Alcotest.(check bool) ("field " ^ f) true (j |> member f <> `Null)
  ) ["stat_id"; "persona"; "tone"; "explanation"; "flag"; "anomaly_score"]

let test_explain_stat_tone () =
  let j = parse (Api.handle_explain_stat explain_body) in
  Alcotest.(check string) "tone = credit-focused" "credit-focused"
    (field_str j "tone")

let test_explain_stat_bad_json () =
  let j = parse (Api.handle_explain_stat "broken{") in
  Alcotest.(check bool) "error field present" true (has_error j)

let explain_suite = [
  "explain fields present",  `Quick, test_explain_stat_fields;
  "explain tone",            `Quick, test_explain_stat_tone;
  "explain bad JSON",        `Quick, test_explain_stat_bad_json;
]

(* ── /scenario_runner ────────────────────────────────────────────────────── *)

let scenario_body = {|{
  "id": "stress_test_1",
  "persona": "CorporateCFO",
  "stage": "Maturity",
  "shocks": [
    {"metric_id": "leverage_ratio", "delta": -0.08},
    {"metric_id": "profitability",  "delta":  0.03}
  ],
  "baseline": {
    "leverage_ratio": 0.40,
    "profitability":  0.12,
    "tangibility":    0.55
  }
}|}

let test_scenario_runner_fields () =
  let j = parse (Api.handle_scenario_runner scenario_body) in
  List.iter (fun f ->
    Alcotest.(check bool) ("field " ^ f) true (j |> member f <> `Null)
  ) ["scenario_id"; "persona"; "stage"; "is_stress"; "total_magnitude"; "shock_results"]

let test_scenario_runner_is_stress () =
  let j = parse (Api.handle_scenario_runner scenario_body) in
  Alcotest.(check bool) "is_stress = true" true
    (j |> member "is_stress" |> to_bool)

let test_scenario_runner_shock_results_count () =
  let j = parse (Api.handle_scenario_runner scenario_body) in
  let results = j |> member "shock_results" |> to_list in
  Alcotest.(check int) "2 shock results" 2 (List.length results)

let test_scenario_runner_magnitude () =
  let j = parse (Api.handle_scenario_runner scenario_body) in
  let mag = j |> member "total_magnitude" |> to_float in
  Alcotest.(check bool) "magnitude ≈ 0.11" true (abs_float (mag -. 0.11) < 1e-9)

let test_scenario_runner_bad_json () =
  let j = parse (Api.handle_scenario_runner "{}") in
  Alcotest.(check bool) "error on missing fields" true (has_error j)

let scenario_suite = [
  "scenario fields",          `Quick, test_scenario_runner_fields;
  "is_stress = true",         `Quick, test_scenario_runner_is_stress;
  "2 shock results",          `Quick, test_scenario_runner_shock_results_count;
  "total_magnitude ≈ 0.11",   `Quick, test_scenario_runner_magnitude;
  "bad JSON → error",         `Quick, test_scenario_runner_bad_json;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "api" [
  "health",          health_suite;
  "lifecycle_macro", lifecycle_macro_suite;
  "lifecycle_meso",  lifecycle_meso_suite;
  "lifecycle_micro", lifecycle_micro_suite;
  "explain_stat",    explain_suite;
  "scenario_runner", scenario_suite;
]
