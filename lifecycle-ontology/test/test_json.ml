(** Phase 3 — JSON round-trip tests for domain and analytics_meta types. *)

open Domain
open Analytics_meta

(* ── Helpers ─────────────────────────────────────────────────────────────── *)

let check_ok_eq pp eq name expected result =
  match result with
  | Error msg -> Alcotest.failf "%s: unexpected Error: %s" name msg
  | Ok got    ->
      if not (eq expected got) then
        Alcotest.failf "%s: expected %s but got %s" name
          (Yojson.Safe.to_string (pp expected))
          (Yojson.Safe.to_string (pp got))

let check_error name result =
  match result with
  | Ok _    -> Alcotest.failf "%s: expected Error but got Ok" name
  | Error _ -> ()

(* ── Stage round-trips ───────────────────────────────────────────────────── *)

let test_stage_round_trip () =
  List.iter (fun s ->
    let j   = Stage.to_yojson s in
    let r   = Stage.of_yojson j in
    check_ok_eq Stage.to_yojson Stage.equal (Stage.to_string s) s r
  ) Stage.all

let test_stage_of_yojson_unknown () =
  check_error "unknown stage" (Stage.of_yojson (`String "Zombie"))

let test_stage_of_yojson_wrong_type () =
  check_error "int not string" (Stage.of_yojson (`Int 3))

let stage_suite = [
  "round-trip all",     `Quick, test_stage_round_trip;
  "unknown string",     `Quick, test_stage_of_yojson_unknown;
  "wrong type",         `Quick, test_stage_of_yojson_wrong_type;
]

(* ── Period round-trips ──────────────────────────────────────────────────── *)

let period_equal a b =
  a.Period.id = b.Period.id &&
  a.fiscal_year = b.fiscal_year &&
  a.quarter = b.quarter &&
  a.basis = b.basis &&
  a.kind = b.kind &&
  a.events = b.events

let test_period_annual_round_trip () =
  let p = Period.make ~fiscal_year:2024 () in
  let j = Period.to_yojson p in
  let r = Period.of_yojson j in
  check_ok_eq Period.to_yojson period_equal "annual" p r

let test_period_quarterly_round_trip () =
  let p = Period.make ~fiscal_year:2024 ~quarter:(Some 2)
            ~kind:Period.Quarterly ~basis:Period.Consolidated () in
  let j = Period.to_yojson p in
  let r = Period.of_yojson j in
  check_ok_eq Period.to_yojson period_equal "quarterly" p r

let test_period_crisis_round_trip () =
  let p = Period.make ~fiscal_year:2009 ~events:[Period.GFC; Period.IBC] () in
  let j = Period.to_yojson p in
  let r = Period.of_yojson j in
  check_ok_eq Period.to_yojson period_equal "crisis period" p r

let test_period_event_round_trips () =
  List.iter (fun ev ->
    let j = Period.event_to_yojson ev in
    match Period.event_of_yojson j with
    | Error msg -> Alcotest.failf "event round-trip: %s" msg
    | Ok ev2    -> Alcotest.(check bool) (Period.event_to_string ev) true (ev = ev2)
  ) [ Period.GFC; Period.IBC; Period.COVID ]

let test_period_basis_round_trips () =
  List.iter (fun b ->
    let j = Period.basis_to_yojson b in
    match Period.basis_of_yojson j with
    | Error msg -> Alcotest.failf "basis round-trip: %s" msg
    | Ok b2     -> Alcotest.(check bool) (Period.basis_to_string b) true (b = b2)
  ) [ Period.Standalone; Period.Consolidated ]

let test_period_of_yojson_error () =
  check_error "null not object" (Period.of_yojson `Null)

let period_suite = [
  "annual round-trip",    `Quick, test_period_annual_round_trip;
  "quarterly round-trip", `Quick, test_period_quarterly_round_trip;
  "crisis round-trip",    `Quick, test_period_crisis_round_trip;
  "event round-trips",    `Quick, test_period_event_round_trips;
  "basis round-trips",    `Quick, test_period_basis_round_trips;
  "error on null",        `Quick, test_period_of_yojson_error;
]

(* ── Metric round-trips ──────────────────────────────────────────────────── *)

let metric_equal a b = a.Metric.id = b.Metric.id

let test_metric_catalogue_round_trip () =
  List.iter (fun m ->
    let j = Metric.to_yojson m in
    let r = Metric.of_yojson j in
    check_ok_eq Metric.to_yojson metric_equal m.id m r
  ) Metric.catalogue

let test_metric_id_shorthand () =
  let j = `String "leverage_ratio" in
  let r = Metric.of_yojson j in
  check_ok_eq Metric.to_yojson metric_equal "shorthand id" Metric.leverage_ratio r

let test_metric_unknown_id_error () =
  check_error "unknown id" (Metric.of_yojson (`String "bogus_metric"))

let test_metric_unit_round_trips () =
  let units = [ Metric.Ratio; Metric.Percent; Metric.CurrencyInrCr;
                Metric.Count; Metric.Years ] in
  List.iter (fun u ->
    let j = Metric.unit_to_yojson u in
    match Metric.unit_of_yojson j with
    | Error msg -> Alcotest.failf "unit round-trip: %s" msg
    | Ok u2     ->
        Alcotest.(check string) "unit string"
          (Metric.unit_to_string u) (Metric.unit_to_string u2)
  ) units

let metric_suite = [
  "catalogue round-trip", `Quick, test_metric_catalogue_round_trip;
  "id shorthand",         `Quick, test_metric_id_shorthand;
  "unknown id error",     `Quick, test_metric_unknown_id_error;
  "unit round-trips",     `Quick, test_metric_unit_round_trips;
]

(* ── Company round-trips ─────────────────────────────────────────────────── *)

let company_equal a b = Company.equal a b

let test_company_unlisted_round_trip () =
  let c = Company.make ~code:"C001" ~name:"TataSteel" ~industry:"Steel" () in
  let j = Company.to_yojson c in
  let r = Company.of_yojson j in
  check_ok_eq Company.to_yojson company_equal "unlisted" c r

let test_company_listed_round_trip () =
  let c = Company.make ~code:"C002" ~name:"Infosys" ~industry:"IT"
            ~listing:(Some "NSE,BSE") ~ipo_year:(Some 1993) () in
  let j = Company.to_yojson c in
  let r = Company.of_yojson j in
  check_ok_eq Company.to_yojson company_equal "listed with IPO" c r;
  (* also check listing and ipo_year preserved *)
  (match r with
   | Ok got ->
       Alcotest.(check (option string)) "listing"  (Some "NSE,BSE") got.listing;
       Alcotest.(check (option int))    "ipo_year" (Some 1993)      got.ipo_year
   | Error _ -> ())

let test_company_of_yojson_error () =
  check_error "bool not object" (Company.of_yojson (`Bool true))

let company_suite = [
  "unlisted round-trip",  `Quick, test_company_unlisted_round_trip;
  "listed round-trip",    `Quick, test_company_listed_round_trip;
  "error on bool",        `Quick, test_company_of_yojson_error;
]

(* ── Persona round-trips ─────────────────────────────────────────────────── *)

let test_persona_round_trip () =
  List.iter (fun p ->
    let j = Persona.to_yojson p in
    let r = Persona.of_yojson j in
    match r with
    | Error msg -> Alcotest.failf "persona round-trip: %s" msg
    | Ok p2     -> Alcotest.(check bool) (Persona.to_string p) true (Persona.equal p p2)
  ) Persona.all

let test_persona_unknown_error () =
  check_error "unknown persona" (Persona.of_yojson (`String "AlgoTrader"))

let persona_suite = [
  "round-trip all",   `Quick, test_persona_round_trip;
  "unknown error",    `Quick, test_persona_unknown_error;
]

(* ── Analytics_meta round-trips ──────────────────────────────────────────── *)

let test_model_kind_round_trip () =
  let kinds = [ Fe; Re; Ols; Gmm; Rf; Xgboost; Lstm; Gru ] in
  List.iter (fun k ->
    let j = model_kind_to_yojson k in
    match model_kind_of_yojson j with
    | Error msg -> Alcotest.failf "model_kind round-trip: %s" msg
    | Ok k2     ->
        Alcotest.(check string) "kind string"
          (model_kind_to_string k) (model_kind_to_string k2)
  ) kinds

let test_model_kind_unknown_error () =
  check_error "unknown kind" (model_kind_of_yojson (`String "Transformer"))

let test_normative_band_round_trip () =
  let nb : normative_band = {
    nb_id          = "nb_maturity_steel_lev";
    stage          = Stage.Maturity;
    industry       = "Steel";
    metric         = Metric.leverage_ratio;
    lower          = 0.25;
    upper          = 0.45;
    source_vintage = "thesis";
  } in
  let j  = normative_band_to_yojson nb in
  let r  = normative_band_of_yojson j in
  match r with
  | Error msg -> Alcotest.failf "normative_band round-trip: %s" msg
  | Ok nb2 ->
      Alcotest.(check string) "nb_id"          nb.nb_id          nb2.nb_id;
      Alcotest.(check string) "industry"       nb.industry       nb2.industry;
      Alcotest.(check string) "metric_id"      nb.metric.id      nb2.metric.id;
      Alcotest.(check bool)   "stage equal"    true (Stage.equal nb.stage nb2.stage);
      Alcotest.(check (float 1e-9)) "lower"    nb.lower          nb2.lower;
      Alcotest.(check (float 1e-9)) "upper"    nb.upper          nb2.upper

let test_normative_band_all_stages () =
  List.iter (fun st ->
    let nb : normative_band = {
      nb_id = "nb_" ^ Stage.to_string st; stage = st;
      industry = "Pharma"; metric = Metric.profitability;
      lower = 0.0; upper = 0.3; source_vintage = "test";
    } in
    let j = normative_band_to_yojson nb in
    match normative_band_of_yojson j with
    | Error msg -> Alcotest.failf "stage %s: %s" (Stage.to_string st) msg
    | Ok nb2    ->
        Alcotest.(check bool) (Stage.to_string st)
          true (Stage.equal nb.stage nb2.stage)
  ) Stage.all

let test_explanation_round_trip () =
  let e : explanation = {
    expl_id  = "expl_leverage_drop";
    personas = [ Persona.RatingAnalyst; Persona.CorporateCFO ];
    template = "Leverage dropped due to {{cause}} in stage {{stage}}.";
  } in
  let j = explanation_to_yojson e in
  let r = explanation_of_yojson j in
  match r with
  | Error msg -> Alcotest.failf "explanation round-trip: %s" msg
  | Ok e2 ->
      Alcotest.(check string) "expl_id"  e.expl_id  e2.expl_id;
      Alcotest.(check string) "template" e.template e2.template;
      Alcotest.(check int)    "personas" (List.length e.personas)
                                         (List.length e2.personas)

let analytics_meta_suite = [
  "model_kind round-trip",          `Quick, test_model_kind_round_trip;
  "model_kind unknown error",       `Quick, test_model_kind_unknown_error;
  "normative_band round-trip",      `Quick, test_normative_band_round_trip;
  "normative_band all stages",      `Quick, test_normative_band_all_stages;
  "explanation round-trip",         `Quick, test_explanation_round_trip;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "json_round_trip" [
  "stage",          stage_suite;
  "period",         period_suite;
  "metric",         metric_suite;
  "company",        company_suite;
  "persona",        persona_suite;
  "analytics_meta", analytics_meta_suite;
]
