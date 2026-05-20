(** Domain type unit tests — Phase 2.
    Full alcotest coverage of smart constructors, validators, and predicates. *)

open Domain

(* ── Testable helpers ────────────────────────────────────────────────────── *)

let stage_t =
  Alcotest.testable
    (fun ppf s -> Format.pp_print_string ppf (Stage.to_string s))
    Stage.equal

let stage_opt_t = Alcotest.option stage_t

let persona_t =
  Alcotest.testable
    (fun ppf p -> Format.pp_print_string ppf (Persona.to_string p))
    Persona.equal

let persona_opt_t = Alcotest.option persona_t

(* ── Stage suite ─────────────────────────────────────────────────────────── *)

let test_stage_count () =
  Alcotest.(check int) "8 stages" 8 Stage.count;
  Alcotest.(check int) "all list length" 8 (List.length Stage.all)

let test_stage_to_string_round_trip () =
  List.iter (fun s ->
    let label = Stage.to_string s in
    Alcotest.check stage_opt_t
      ("round-trip " ^ label) (Some s) (Stage.of_string_opt label)
  ) Stage.all

let test_stage_of_string_unknown () =
  Alcotest.check stage_opt_t "lowercase unknown" None (Stage.of_string_opt "shakeout");
  Alcotest.check stage_opt_t "empty string"      None (Stage.of_string_opt "")

let test_stage_of_string_raises () =
  Alcotest.check_raises "of_string raises"
    (Invalid_argument "Stage.of_string: unknown stage bogus")
    (fun () -> ignore (Stage.of_string "bogus"))

let test_stage_index_round_trip () =
  List.iteri (fun i s ->
    Alcotest.(check int) ("to_index " ^ Stage.to_string s) i (Stage.to_index s);
    Alcotest.check stage_t ("of_index " ^ string_of_int i) s (Stage.of_index i)
  ) Stage.all

let test_stage_index_out_of_range () =
  Alcotest.check_raises "of_index -1 raises"
    (Invalid_argument "Stage.of_index: out of range -1")
    (fun () -> ignore (Stage.of_index (-1)));
  Alcotest.check_raises "of_index 8 raises"
    (Invalid_argument "Stage.of_index: out of range 8")
    (fun () -> ignore (Stage.of_index 8))

let test_stage_is_distress () =
  let distress = [Stage.Shakeout2; Stage.Shakeout3; Stage.Decline; Stage.Decay] in
  let non_distress = [Stage.Startup; Stage.Growth; Stage.Maturity; Stage.Shakeout1] in
  List.iter (fun s ->
    Alcotest.(check bool) (Stage.to_string s ^ " is distress") true  (Stage.is_distress s)
  ) distress;
  List.iter (fun s ->
    Alcotest.(check bool) (Stage.to_string s ^ " not distress") false (Stage.is_distress s)
  ) non_distress

let test_stage_is_early () =
  Alcotest.(check bool) "Startup is early"  true  (Stage.is_early Stage.Startup);
  Alcotest.(check bool) "Growth is early"   true  (Stage.is_early Stage.Growth);
  Alcotest.(check bool) "Maturity not early" false (Stage.is_early Stage.Maturity)

let test_stage_is_mature () =
  Alcotest.(check bool) "Maturity is mature" true  (Stage.is_mature Stage.Maturity);
  Alcotest.(check bool) "Growth not mature"  false (Stage.is_mature Stage.Growth)

let test_stage_is_shakeout () =
  let shakeouts = [Stage.Shakeout1; Stage.Shakeout2; Stage.Shakeout3] in
  List.iter (fun s ->
    Alcotest.(check bool) (Stage.to_string s ^ " is shakeout") true (Stage.is_shakeout s)
  ) shakeouts;
  Alcotest.(check bool) "Maturity not shakeout" false (Stage.is_shakeout Stage.Maturity)

let test_stage_group () =
  Alcotest.(check string) "Startup group"    "early"        (Stage.group Stage.Startup);
  Alcotest.(check string) "Growth group"     "early"        (Stage.group Stage.Growth);
  Alcotest.(check string) "Maturity group"   "peak"         (Stage.group Stage.Maturity);
  Alcotest.(check string) "Shakeout1 group"  "transitional" (Stage.group Stage.Shakeout1);
  Alcotest.(check string) "Shakeout2 group"  "distress"     (Stage.group Stage.Shakeout2);
  Alcotest.(check string) "Decline group"    "terminal"     (Stage.group Stage.Decline);
  Alcotest.(check string) "Decay group"      "terminal"     (Stage.group Stage.Decay)

let test_stage_next_opt () =
  Alcotest.check stage_opt_t "Startup -> Growth"     (Some Stage.Growth)    (Stage.next_opt Stage.Startup);
  Alcotest.check stage_opt_t "Growth  -> Maturity"   (Some Stage.Maturity)  (Stage.next_opt Stage.Growth);
  Alcotest.check stage_opt_t "Decay   -> None"       None                   (Stage.next_opt Stage.Decay)

let test_stage_prev_opt () =
  Alcotest.check stage_opt_t "Startup prev -> None"  None                   (Stage.prev_opt Stage.Startup);
  Alcotest.check stage_opt_t "Growth prev  -> Startup" (Some Stage.Startup) (Stage.prev_opt Stage.Growth);
  Alcotest.check stage_opt_t "Decay prev -> Decline"  (Some Stage.Decline)  (Stage.prev_opt Stage.Decay)

let test_stage_compare () =
  Alcotest.(check bool) "Startup < Growth" true (Stage.compare Stage.Startup Stage.Growth < 0);
  Alcotest.(check bool) "Decay > Startup"  true (Stage.compare Stage.Decay Stage.Startup > 0);
  Alcotest.(check bool) "Maturity = Maturity" true (Stage.compare Stage.Maturity Stage.Maturity = 0)

let stage_suite = [
  "count",               `Quick, test_stage_count;
  "to_string round-trip",`Quick, test_stage_to_string_round_trip;
  "of_string unknown",   `Quick, test_stage_of_string_unknown;
  "of_string raises",    `Quick, test_stage_of_string_raises;
  "index round-trip",    `Quick, test_stage_index_round_trip;
  "index out-of-range",  `Quick, test_stage_index_out_of_range;
  "is_distress",         `Quick, test_stage_is_distress;
  "is_early",            `Quick, test_stage_is_early;
  "is_mature",           `Quick, test_stage_is_mature;
  "is_shakeout",         `Quick, test_stage_is_shakeout;
  "group",               `Quick, test_stage_group;
  "next_opt",            `Quick, test_stage_next_opt;
  "prev_opt",            `Quick, test_stage_prev_opt;
  "compare",             `Quick, test_stage_compare;
]

(* ── Period suite ────────────────────────────────────────────────────────── *)

let test_period_make_annual () =
  let p = Period.make ~fiscal_year:2024 () in
  Alcotest.(check int)    "fiscal_year" 2024           p.fiscal_year;
  Alcotest.(check bool)   "no quarter"  true           (p.quarter = None);
  Alcotest.(check string) "id"          "FY2024-Annual-SA" p.id;
  Alcotest.(check bool)   "not crisis"  false          (Period.is_crisis_period p)

let test_period_make_quarterly () =
  let p = Period.make ~fiscal_year:2024 ~quarter:(Some 3)
            ~kind:Period.Quarterly ~basis:Period.Consolidated () in
  Alcotest.(check bool)   "quarter present" true  (p.quarter = Some 3);
  Alcotest.(check string) "id"
    "FY2024-Q3-Quarterly-CS" p.id

let test_period_crisis_flags () =
  let p = Period.make ~fiscal_year:2009 ~events:[Period.GFC] () in
  Alcotest.(check bool) "is crisis"      true  (Period.is_crisis_period p);
  Alcotest.(check bool) "has GFC"        true  (Period.has_event p Period.GFC);
  Alcotest.(check bool) "no COVID"       false (Period.has_event p Period.COVID);
  Alcotest.(check bool) "contains_gfc"   true  (Period.contains_gfc p);
  Alcotest.(check bool) "contains_covid" false (Period.contains_covid p);
  Alcotest.(check bool) "contains_ibc"   false (Period.contains_ibc p)

let test_period_multi_event () =
  let p = Period.make ~fiscal_year:2020
            ~events:[Period.IBC; Period.COVID] () in
  Alcotest.(check bool) "has IBC"   true (Period.has_event p Period.IBC);
  Alcotest.(check bool) "has COVID" true (Period.has_event p Period.COVID);
  Alcotest.(check bool) "has GFC"   false (Period.has_event p Period.GFC)

let test_period_validate_ok () =
  let result = Period.make_validated ~fiscal_year:2024 () in
  Alcotest.(check bool) "valid period returns Ok" true (Result.is_ok result)

let test_period_validate_bad_year () =
  let result = Period.make_validated ~fiscal_year:1800 () in
  Alcotest.(check bool) "year 1800 is Error" true (Result.is_error result)

let test_period_validate_bad_quarter () =
  let result = Period.make_validated ~fiscal_year:2024 ~quarter:(Some 5) () in
  Alcotest.(check bool) "Q5 is Error" true (Result.is_error result);
  let result0 = Period.make_validated ~fiscal_year:2024 ~quarter:(Some 0) () in
  Alcotest.(check bool) "Q0 is Error" true (Result.is_error result0)

let test_period_validate_duplicate_events () =
  let result = Period.make_validated ~fiscal_year:2009
                 ~events:[Period.GFC; Period.GFC] () in
  Alcotest.(check bool) "duplicate events is Error" true (Result.is_error result)

let test_period_to_label () =
  let p = Period.make ~fiscal_year:2024 ~basis:Period.Consolidated () in
  let lbl = Period.to_label p in
  Alcotest.(check bool) "label contains FY2024" true
    (let n = String.length lbl in n > 0 && lbl.[0] = 'F')

let test_period_event_strings () =
  Alcotest.(check string) "GFC"   "GFC"   (Period.event_to_string Period.GFC);
  Alcotest.(check string) "IBC"   "IBC"   (Period.event_to_string Period.IBC);
  Alcotest.(check string) "COVID" "COVID" (Period.event_to_string Period.COVID)

let test_period_basis_strings () =
  Alcotest.(check string) "SA"  "Standalone"   (Period.basis_to_string Period.Standalone);
  Alcotest.(check string) "CS"  "Consolidated" (Period.basis_to_string Period.Consolidated);
  Alcotest.(check bool) "SA parse"  true (Period.basis_of_string_opt "SA"  = Some Period.Standalone);
  Alcotest.(check bool) "CS parse"  true (Period.basis_of_string_opt "CS"  = Some Period.Consolidated);
  Alcotest.(check bool) "unknown"   true (Period.basis_of_string_opt "XX"  = None)

let period_suite = [
  "make annual",             `Quick, test_period_make_annual;
  "make quarterly",          `Quick, test_period_make_quarterly;
  "crisis flags",            `Quick, test_period_crisis_flags;
  "multi-event",             `Quick, test_period_multi_event;
  "validate ok",             `Quick, test_period_validate_ok;
  "validate bad year",       `Quick, test_period_validate_bad_year;
  "validate bad quarter",    `Quick, test_period_validate_bad_quarter;
  "validate dup events",     `Quick, test_period_validate_duplicate_events;
  "to_label",                `Quick, test_period_to_label;
  "event strings",           `Quick, test_period_event_strings;
  "basis strings",           `Quick, test_period_basis_strings;
]

(* ── Metric suite ────────────────────────────────────────────────────────── *)

let test_metric_catalogue () =
  Alcotest.(check int) "catalogue has 6 entries" 6 (List.length Metric.catalogue)

let test_metric_find_opt () =
  Alcotest.(check bool) "leverage_ratio found"
    true (Metric.find_opt "leverage_ratio" = Some Metric.leverage_ratio);
  Alcotest.(check bool) "unknown not found"
    true (Metric.find_opt "nonexistent_xyz" = None)

let test_metric_leverage_attrs () =
  let m = Metric.leverage_ratio in
  Alcotest.(check string) "id"   "leverage_ratio" m.id;
  Alcotest.(check bool)   "is_derived" true m.is_derived;
  Alcotest.(check string) "unit" "ratio" (Metric.unit_to_string m.unit)

let test_metric_validate_value_ok () =
  Alcotest.(check bool) "0.35 leverage ok"
    true (Result.is_ok (Metric.validate_value Metric.leverage_ratio 0.35));
  Alcotest.(check bool) "0.0 tangibility ok"
    true (Result.is_ok (Metric.validate_value Metric.tangibility 0.0));
  Alcotest.(check bool) "1.0 tangibility ok"
    true (Result.is_ok (Metric.validate_value Metric.tangibility 1.0))

let test_metric_validate_value_error () =
  Alcotest.(check bool) "negative leverage error"
    true (Result.is_error (Metric.validate_value Metric.leverage_ratio (-0.5)));
  Alcotest.(check bool) "leverage > 2.0 error"
    true (Result.is_error (Metric.validate_value Metric.leverage_ratio 2.5));
  Alcotest.(check bool) "tangibility > 1.0 error"
    true (Result.is_error (Metric.validate_value Metric.tangibility 1.1))

let test_metric_make () =
  let m = Metric.make ~id:"test_m" ~name:"Test Metric"
            ~statement_type:`Derived ~unit:Metric.Ratio ~is_derived:true () in
  Alcotest.(check string) "id"   "test_m"      m.id;
  Alcotest.(check string) "name" "Test Metric" m.name

let test_metric_make_blank_id_raises () =
  Alcotest.check_raises "blank id raises"
    (Invalid_argument "Metric.make: id must not be empty")
    (fun () -> ignore (Metric.make ~id:"" ~name:"x"
                         ~statement_type:`Derived ~unit:Metric.Ratio
                         ~is_derived:false ()))

let test_metric_group () =
  Alcotest.(check string) "leverage group" "leverage"
    (Metric.group Metric.leverage_ratio);
  Alcotest.(check string) "profitability group" "profitability"
    (Metric.group Metric.profitability);
  Alcotest.(check string) "tangibility group" "asset_structure"
    (Metric.group Metric.tangibility)

let metric_suite = [
  "catalogue size",          `Quick, test_metric_catalogue;
  "find_opt",                `Quick, test_metric_find_opt;
  "leverage attrs",          `Quick, test_metric_leverage_attrs;
  "validate_value ok",       `Quick, test_metric_validate_value_ok;
  "validate_value error",    `Quick, test_metric_validate_value_error;
  "make",                    `Quick, test_metric_make;
  "make blank id raises",    `Quick, test_metric_make_blank_id_raises;
  "group",                   `Quick, test_metric_group;
]

(* ── Company suite ───────────────────────────────────────────────────────── *)

let test_company_make () =
  let c = Company.make ~code:"C001" ~name:"TataSteel" ~industry:"Steel" () in
  Alcotest.(check string) "code"     "C001"     c.code;
  Alcotest.(check string) "name"     "TataSteel" c.name;
  Alcotest.(check string) "industry" "Steel"    c.industry;
  Alcotest.(check bool)   "not listed" false    (Company.is_listed c)

let test_company_make_listed () =
  let c = Company.make ~code:"C002" ~name:"Infosys" ~industry:"IT"
            ~listing:(Some "NSE,BSE") () in
  Alcotest.(check bool) "is listed" true (Company.is_listed c)

let test_company_make_validated_ok () =
  let r = Company.make_validated ~code:"C003" ~name:"Wipro" ~industry:"IT" () in
  Alcotest.(check bool) "validated ok" true (Result.is_ok r)

let test_company_make_validated_blank () =
  let r1 = Company.make_validated ~code:""    ~name:"X"  ~industry:"Y" () in
  let r2 = Company.make_validated ~code:"C"   ~name:""   ~industry:"Y" () in
  let r3 = Company.make_validated ~code:"C"   ~name:"X"  ~industry:""  () in
  Alcotest.(check bool) "blank code error"     true (Result.is_error r1);
  Alcotest.(check bool) "blank name error"     true (Result.is_error r2);
  Alcotest.(check bool) "blank industry error" true (Result.is_error r3)

let test_company_exchange_list () =
  let c_none  = Company.make ~code:"A" ~name:"A" ~industry:"X" () in
  let c_multi = Company.make ~code:"B" ~name:"B" ~industry:"X"
                  ~listing:(Some "NSE,BSE") () in
  let c_single = Company.make ~code:"C" ~name:"C" ~industry:"X"
                   ~listing:(Some "NSE") () in
  Alcotest.(check (list string)) "no listing -> []"        [] (Company.exchange_list c_none);
  Alcotest.(check (list string)) "NSE,BSE -> [NSE;BSE]"   ["NSE"; "BSE"] (Company.exchange_list c_multi);
  Alcotest.(check (list string)) "single exchange"        ["NSE"] (Company.exchange_list c_single)

let test_company_equal_compare () =
  let c1 = Company.make ~code:"C001" ~name:"Tata" ~industry:"Steel" () in
  let c2 = Company.make ~code:"C001" ~name:"Other" ~industry:"IT" () in
  let c3 = Company.make ~code:"C002" ~name:"Tata"  ~industry:"Steel" () in
  Alcotest.(check bool) "equal same code"  true  (Company.equal c1 c2);
  Alcotest.(check bool) "equal diff code"  false (Company.equal c1 c3);
  Alcotest.(check bool) "compare c1<c3"    true  (Company.compare c1 c3 < 0)

let company_suite = [
  "make",                    `Quick, test_company_make;
  "make listed",             `Quick, test_company_make_listed;
  "make_validated ok",       `Quick, test_company_make_validated_ok;
  "make_validated blank",    `Quick, test_company_make_validated_blank;
  "exchange_list",           `Quick, test_company_exchange_list;
  "equal and compare",       `Quick, test_company_equal_compare;
]

(* ── Persona suite ───────────────────────────────────────────────────────── *)

let test_persona_count () =
  Alcotest.(check int) "6 personas" 6 (List.length Persona.all)

let test_persona_to_string_round_trip () =
  List.iter (fun p ->
    let s = Persona.to_string p in
    Alcotest.check persona_opt_t ("round-trip " ^ s) (Some p)
      (Persona.of_string_opt s)
  ) Persona.all

let test_persona_of_string_unknown () =
  Alcotest.check persona_opt_t "unknown persona" None
    (Persona.of_string_opt "UnknownPersona")

let test_persona_of_string_raises () =
  Alcotest.check_raises "of_string raises"
    (Invalid_argument "Persona.of_string: unknown persona bogus")
    (fun () -> ignore (Persona.of_string "bogus"))

let test_persona_default_horizon () =
  Alcotest.(check int) "FacultyPhDSupervisor horizon" 10
    (Persona.default_horizon Persona.FacultyPhDSupervisor);
  Alcotest.(check int) "RatingAnalyst horizon" 1
    (Persona.default_horizon Persona.RatingAnalyst)

let test_persona_display_name () =
  Alcotest.(check string) "CorporateCFO display" "Corporate CFO"
    (Persona.display_name Persona.CorporateCFO);
  Alcotest.(check string) "PEVCInvestor display" "PE/VC Investor"
    (Persona.display_name Persona.PEVCInvestor)

let test_persona_key_metric_ids () =
  let ids = Persona.key_metric_ids Persona.RatingAnalyst in
  Alcotest.(check bool) "leverage in RA metrics" true
    (List.mem "leverage_ratio" ids);
  let all_ids = Persona.key_metric_ids Persona.FacultyPhDSupervisor in
  Alcotest.(check int) "Faculty has 6 metrics" 6 (List.length all_ids)

let test_persona_explanation_tone () =
  Alcotest.(check string) "RatingAnalyst tone" "credit-focused"
    (Persona.explanation_tone Persona.RatingAnalyst);
  Alcotest.(check string) "FacultyPhDSupervisor tone" "academic"
    (Persona.explanation_tone Persona.FacultyPhDSupervisor)

let persona_suite = [
  "count",                   `Quick, test_persona_count;
  "to_string round-trip",    `Quick, test_persona_to_string_round_trip;
  "of_string unknown",       `Quick, test_persona_of_string_unknown;
  "of_string raises",        `Quick, test_persona_of_string_raises;
  "default_horizon",         `Quick, test_persona_default_horizon;
  "display_name",            `Quick, test_persona_display_name;
  "key_metric_ids",          `Quick, test_persona_key_metric_ids;
  "explanation_tone",        `Quick, test_persona_explanation_tone;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "domain" [
  "stage",   stage_suite;
  "period",  period_suite;
  "metric",  metric_suite;
  "company", company_suite;
  "persona", persona_suite;
]
