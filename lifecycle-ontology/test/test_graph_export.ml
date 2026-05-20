(** Phase 5 — Macro/Meso/Micro JSON contract tests. *)

open Domain
open Graph_export

(* ── Test data fixtures ──────────────────────────────────────────────────── *)

let sample_si_counts = [
  (Stage.Startup,   "Pharma",  8);
  (Stage.Growth,    "IT",     22);
  (Stage.Growth,    "Steel",  15);
  (Stage.Maturity,  "IT",     18);
  (Stage.Maturity,  "Steel",  25);
  (Stage.Maturity,  "Cement",  9);
  (Stage.Shakeout1, "Steel",  12);
  (Stage.Decline,   "Pharma",  5);
]

let sample_transitions = [
  (Stage.Startup,  Stage.Growth,    0.55);
  (Stage.Growth,   Stage.Maturity,  0.48);
  (Stage.Maturity, Stage.Shakeout1, 0.22);
  (Stage.Decline,  Stage.Decay,     0.38);
]

let sample_crisis = [
  (Period.GFC,   [Stage.Maturity; Stage.Shakeout1]);
  (Period.COVID, [Stage.Growth; Stage.Maturity]);
]

let sample_companies = List.init 10 (fun i ->
  let code = Printf.sprintf "C%03d" (i + 1) in
  let stage = Stage.of_index (i mod 4) in
  (code, "Company " ^ code, stage, "Steel", 0.30 +. float_of_int i *. 0.03))

(* ── Helpers ─────────────────────────────────────────────────────────────── *)

let get_field j key =
  match j with
  | `Assoc pairs -> List.assoc_opt key pairs
  | _            -> None

let has_field j key = get_field j key <> None

let string_field j key =
  match get_field j key with
  | Some (`String s) -> s
  | _ -> Alcotest.failf "field '%s' missing or not a string" key

let int_field j key =
  match get_field j key with
  | Some (`Int n) -> n
  | _ -> Alcotest.failf "field '%s' missing or not an int" key

let list_field j key =
  match get_field j key with
  | Some (`List l) -> l
  | _ -> Alcotest.failf "field '%s' missing or not a list" key

(* ── Node builder tests ──────────────────────────────────────────────────── *)

let test_stage_node_id () =
  let n = make_stage_node Stage.Maturity in
  Alcotest.(check string) "id"    "stage_maturity"  n.id;
  Alcotest.(check string) "label" "Maturity"         n.label;
  Alcotest.(check string) "type"  "stage" (node_type_to_string n.kind)

let test_all_stage_nodes_unique_ids () =
  let ids = List.map (fun s -> (make_stage_node s).id) Stage.all in
  let uniq = List.sort_uniq String.compare ids in
  Alcotest.(check int) "8 unique stage node IDs" 8 (List.length uniq)

let test_industry_node () =
  let n = make_industry_node "Information Technology" ~company_count:22 in
  Alcotest.(check string) "type"  "industry" (node_type_to_string n.kind);
  Alcotest.(check bool)   "id has industry_ prefix" true
    (String.length n.id > 9 && String.sub n.id 0 9 = "industry_")

let test_event_node_ids () =
  let events = [ Period.GFC; Period.IBC; Period.COVID ] in
  let ids = List.map (fun ev -> (make_event_node ev).id) events in
  let uniq = List.sort_uniq String.compare ids in
  Alcotest.(check int) "3 unique event node IDs" 3 (List.length uniq);
  Alcotest.(check string) "GFC type" "event"
    (node_type_to_string (make_event_node Period.GFC).kind)

let test_company_node () =
  let n = make_company_node ~code:"C001" ~name:"TataSteel"
            ~stage:Stage.Maturity ~leverage:0.35 in
  Alcotest.(check string) "id"    "company_C001" n.id;
  Alcotest.(check string) "label" "TataSteel"    n.label;
  Alcotest.(check string) "type"  "company" (node_type_to_string n.kind)

let node_builder_suite = [
  "stage node id",           `Quick, test_stage_node_id;
  "all stage IDs unique",    `Quick, test_all_stage_nodes_unique_ids;
  "industry node",           `Quick, test_industry_node;
  "event node ids",          `Quick, test_event_node_ids;
  "company node",            `Quick, test_company_node;
]

(* ── JSON schema tests ───────────────────────────────────────────────────── *)

let node_required_fields = ["id"; "type"; "label"; "color"; "size"; "tooltip"]
let edge_required_fields  = ["from"; "to"; "type"; "weight"; "label"]
let graph_required_fields = ["level"; "persona"; "panel_mode"; "node_count"; "nodes"; "edges"]

let test_node_json_schema () =
  let n = make_stage_node Stage.Growth in
  let j = node_to_yojson n in
  List.iter (fun f ->
    Alcotest.(check bool) ("node has field " ^ f) true (has_field j f)
  ) node_required_fields;
  Alcotest.(check string) "type = stage" "stage" (string_field j "type");
  Alcotest.(check bool) "size > 0" true (int_field j "size" > 0)

let test_node_json_all_types () =
  let nodes = [
    make_stage_node Stage.Maturity;
    make_industry_node "Steel" ~company_count:5;
    make_event_node Period.GFC;
    make_company_node ~code:"X1" ~name:"Co" ~stage:Stage.Growth ~leverage:0.3;
  ] in
  let expected_types = ["stage"; "industry"; "event"; "company"] in
  List.iter2 (fun n expected ->
    let j = node_to_yojson n in
    Alcotest.(check string) ("type=" ^ expected) expected (string_field j "type")
  ) nodes expected_types

let test_edge_json_schema () =
  let e = { from_id = "stage_growth"; to_id = "stage_maturity";
            kind = Transition { from_stage = Stage.Growth;
                                to_stage   = Stage.Maturity };
            weight = 0.48 } in
  let j = edge_to_yojson e in
  List.iter (fun f ->
    Alcotest.(check bool) ("edge has field " ^ f) true (has_field j f)
  ) edge_required_fields;
  Alcotest.(check string) "type = transition" "transition" (string_field j "type")

let test_edge_json_all_types () =
  let kinds = [
    InIndustry; AtStage;
    Transition { from_stage = Stage.Startup; to_stage = Stage.Growth };
    IsPeerOf { similarity_score = 0.92 };
    ExperiencedEvent; HasNorm;
  ] in
  List.iter (fun k ->
    let e = { from_id = "a"; to_id = "b"; kind = k; weight = 1.0 } in
    let j = edge_to_yojson e in
    Alcotest.(check bool) (edge_type_to_string k ^ " type present") true
      (has_field j "type")
  ) kinds

let test_graph_json_schema () =
  let g = build_macro
    ~stage_industry_counts:sample_si_counts
    ~stage_transitions:sample_transitions
    ~crisis_stages:sample_crisis () in
  let j = graph_to_yojson g in
  List.iter (fun f ->
    Alcotest.(check bool) ("graph has field " ^ f) true (has_field j f)
  ) graph_required_fields;
  Alcotest.(check string) "level = macro" "macro" (string_field j "level");
  let nc = int_field j "node_count" in
  let nodes = list_field j "nodes" in
  Alcotest.(check int) "node_count matches nodes list" nc (List.length nodes)

let schema_suite = [
  "node JSON schema",         `Quick, test_node_json_schema;
  "node JSON all types",      `Quick, test_node_json_all_types;
  "edge JSON schema",         `Quick, test_edge_json_schema;
  "edge JSON all types",      `Quick, test_edge_json_all_types;
  "graph JSON schema",        `Quick, test_graph_json_schema;
]

(* ── Macro graph tests ───────────────────────────────────────────────────── *)

let test_macro_has_8_stage_nodes () =
  let g = build_macro
    ~stage_industry_counts:sample_si_counts
    ~stage_transitions:sample_transitions
    ~crisis_stages:[] () in
  let sn = nodes_of_type_str "stage" g in
  Alcotest.(check int) "8 stage nodes" 8 (List.length sn)

let test_macro_node_cap () =
  let g = build_macro
    ~stage_industry_counts:sample_si_counts
    ~stage_transitions:sample_transitions
    ~crisis_stages:sample_crisis () in
  Alcotest.(check bool) "total nodes ≤ 21" true (node_count g <= macro_node_cap);
  Alcotest.(check (option (Alcotest.testable
    (fun ppf _ -> Format.pp_print_string ppf "violation")
    (fun _ _ -> true)))
    "no cap violation" None (validate_caps g))

let test_macro_cap_violation () =
  (* build a deliberately over-capped graph by injecting many industries *)
  let many_si = List.init 25 (fun i ->
    (Stage.Maturity, Printf.sprintf "Industry%02d" i, 5)) in
  let g = build_macro
    ~stage_industry_counts:many_si
    ~stage_transitions:[]
    ~crisis_stages:[] () in
  (* builder enforces the cap, so node_count should still be ≤ 21 *)
  Alcotest.(check bool) "builder caps at 21" true (node_count g <= macro_node_cap)

let test_macro_has_transition_edges () =
  let g = build_macro
    ~stage_industry_counts:[]
    ~stage_transitions:sample_transitions
    ~crisis_stages:[] () in
  let trans = List.filter (fun e ->
    edge_type_to_string e.kind = "transition") g.edges in
  Alcotest.(check int) "4 transition edges" 4 (List.length trans)

let test_macro_crisis_event_nodes () =
  let g = build_macro
    ~stage_industry_counts:[]
    ~stage_transitions:[]
    ~crisis_stages:sample_crisis () in
  let ev = nodes_of_type_str "event" g in
  Alcotest.(check int) "2 event nodes (GFC+COVID)" 2 (List.length ev)

let test_macro_level_field () =
  let g = build_macro
    ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] () in
  Alcotest.(check string) "level = macro" "macro" (level_to_string g.level)

let macro_suite = [
  "8 stage nodes",          `Quick, test_macro_has_8_stage_nodes;
  "node cap ≤ 21",          `Quick, test_macro_node_cap;
  "builder enforces cap",   `Quick, test_macro_cap_violation;
  "transition edges",       `Quick, test_macro_has_transition_edges;
  "crisis event nodes",     `Quick, test_macro_crisis_event_nodes;
  "level field",            `Quick, test_macro_level_field;
]

(* ── Meso graph tests ────────────────────────────────────────────────────── *)

let test_meso_company_nodes () =
  let g = build_meso ~companies:sample_companies () in
  let cn = nodes_of_type_str "company" g in
  Alcotest.(check int) "10 company nodes" 10 (List.length cn)

let test_meso_has_stage_and_industry_context () =
  let g = build_meso ~companies:sample_companies () in
  let sn = nodes_of_type_str "stage" g in
  let ind = nodes_of_type_str "industry" g in
  Alcotest.(check bool) "has stage context nodes"    true (List.length sn > 0);
  Alcotest.(check bool) "has industry context nodes" true (List.length ind > 0)

let test_meso_company_cap_enforced () =
  let many = List.init 100 (fun i ->
    let code = Printf.sprintf "M%03d" i in
    (code, "Co"^code, Stage.Maturity, "Steel", 0.35)) in
  let g = build_meso ~companies:many () in
  let cn = nodes_of_type_str "company" g in
  Alcotest.(check bool) "company nodes ≤ 80" true
    (List.length cn <= meso_company_cap);
  Alcotest.(check (option (Alcotest.testable
    (fun ppf _ -> Format.pp_print_string ppf "v") (fun _ _ -> true)))
    "no cap violation" None (validate_caps g))

let test_meso_edges_present () =
  let g = build_meso ~companies:sample_companies () in
  Alcotest.(check bool) "has edges" true (edge_count g > 0)

let test_meso_level_field () =
  let g = build_meso ~companies:[] () in
  Alcotest.(check string) "level = meso" "meso" (level_to_string g.level)

let meso_suite = [
  "company nodes",          `Quick, test_meso_company_nodes;
  "context nodes present",  `Quick, test_meso_has_stage_and_industry_context;
  "cap enforced ≤ 80",      `Quick, test_meso_company_cap_enforced;
  "edges present",          `Quick, test_meso_edges_present;
  "level field",            `Quick, test_meso_level_field;
]

(* ── Micro graph tests ───────────────────────────────────────────────────── *)

let sample_peers = List.init 15 (fun i ->
  let code = Printf.sprintf "P%02d" (i + 1) in
  (code, "Peer " ^ code, Stage.Maturity, 0.30 +. float_of_int i *. 0.02,
   0.95 -. float_of_int i *. 0.04))

let test_micro_has_focal_node () =
  let g = build_micro
    ~focal_code:"FOCAL" ~focal_name:"FocalCo"
    ~focal_stage:Stage.Maturity ~focal_leverage:0.38
    ~peers:sample_peers ~crisis_events:[] () in
  let cn = nodes_of_type_str "company" g in
  Alcotest.(check bool) "focal node present" true
    (List.exists (fun n -> n.id = "company_FOCAL") cn)

let test_micro_peer_count () =
  let g = build_micro
    ~focal_code:"FOCAL" ~focal_name:"FocalCo"
    ~focal_stage:Stage.Maturity ~focal_leverage:0.38
    ~peers:sample_peers ~crisis_events:[] () in
  let peers_in_graph = List.length (nodes_of_type_str "company" g) - 1 in
  Alcotest.(check bool) "peers ≤ micro_peer_cap" true
    (peers_in_graph <= micro_peer_cap)

let test_micro_peer_cap_enforced () =
  let many_peers = List.init 30 (fun i ->
    let c = Printf.sprintf "PP%02d" i in
    (c, "Peer"^c, Stage.Maturity, 0.3, 0.9 -. float_of_int i *. 0.02)) in
  let g = build_micro
    ~focal_code:"F" ~focal_name:"F"
    ~focal_stage:Stage.Maturity ~focal_leverage:0.35
    ~peers:many_peers ~crisis_events:[] () in
  let n_peers = List.length (nodes_of_type_str "company" g) - 1 in
  Alcotest.(check bool) "peers capped at 20" true (n_peers <= micro_peer_cap);
  Alcotest.(check (option (Alcotest.testable
    (fun ppf _ -> Format.pp_print_string ppf "v") (fun _ _ -> true)))
    "no cap violation" None (validate_caps g))

let test_micro_crisis_events () =
  let g = build_micro
    ~focal_code:"F" ~focal_name:"F"
    ~focal_stage:Stage.Growth ~focal_leverage:0.25
    ~peers:[] ~crisis_events:[Period.GFC; Period.COVID] () in
  let ev = nodes_of_type_str "event" g in
  Alcotest.(check int) "2 event nodes" 2 (List.length ev)

let test_micro_peer_edges_have_similarity () =
  let g = build_micro
    ~focal_code:"FOCAL" ~focal_name:"FocalCo"
    ~focal_stage:Stage.Maturity ~focal_leverage:0.38
    ~peers:(List.filteri (fun i _ -> i < 3) sample_peers)
    ~crisis_events:[] () in
  let peer_edges = List.filter (fun e ->
    edge_type_to_string e.kind = "is_peer_of") g.edges in
  Alcotest.(check int) "3 is_peer_of edges" 3 (List.length peer_edges);
  List.iter (fun e ->
    Alcotest.(check bool) "weight > 0" true (e.weight > 0.0)
  ) peer_edges

let test_micro_level_field () =
  let g = build_micro
    ~focal_code:"F" ~focal_name:"F"
    ~focal_stage:Stage.Startup ~focal_leverage:0.1
    ~peers:[] ~crisis_events:[] () in
  Alcotest.(check string) "level = micro" "micro" (level_to_string g.level)

let micro_suite = [
  "focal node present",      `Quick, test_micro_has_focal_node;
  "peer count ≤ 20",         `Quick, test_micro_peer_count;
  "cap enforced at 20",      `Quick, test_micro_peer_cap_enforced;
  "crisis event nodes",      `Quick, test_micro_crisis_events;
  "peer edge weights",       `Quick, test_micro_peer_edges_have_similarity;
  "level field",             `Quick, test_micro_level_field;
]

(* ── Cap validation tests ────────────────────────────────────────────────── *)

let test_cap_valid_macro () =
  let g = build_macro
    ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] () in
  Alcotest.(check bool) "8-node macro → no violation" true
    (validate_caps g = None)

let test_cap_violation_meso () =
  (* inject 81 company nodes directly to bypass builder cap *)
  let over_nodes = List.init 81 (fun i ->
    make_company_node ~code:(Printf.sprintf "O%03d" i) ~name:"Co"
      ~stage:Stage.Maturity ~leverage:0.3) in
  let g = { level = `Meso; nodes = over_nodes; edges = [] } in
  Alcotest.(check bool) "81 companies → violation" true
    (validate_caps g <> None)

let test_cap_violation_micro () =
  let over_peers = List.init 22 (fun i ->
    make_company_node ~code:(Printf.sprintf "M%02d" i) ~name:"P"
      ~stage:Stage.Maturity ~leverage:0.3) in
  let g = { level = `Micro; nodes = over_peers; edges = [] } in
  Alcotest.(check bool) "22 company nodes (21 peers) → violation" true
    (validate_caps g <> None)

let cap_suite = [
  "valid macro → None",       `Quick, test_cap_valid_macro;
  "meso 81 companies → Some", `Quick, test_cap_violation_meso;
  "micro 21 peers → Some",    `Quick, test_cap_violation_micro;
]

(* ── graph_to_yojson contract test ───────────────────────────────────────── *)

let test_graph_yojson_node_count_consistent () =
  let g = build_meso ~companies:sample_companies () in
  let j = graph_to_yojson g in
  let nc     = int_field j "node_count" in
  let nodes  = list_field j "nodes" in
  Alcotest.(check int) "node_count = len(nodes)" nc (List.length nodes)

let test_graph_yojson_persona_field () =
  let g = build_macro
    ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] () in
  let j = graph_to_yojson ~persona:Persona.RatingAnalyst g in
  Alcotest.(check string) "persona = RatingAnalyst" "RatingAnalyst"
    (string_field j "persona")

let test_graph_yojson_panel_mode () =
  let g = build_macro
    ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] () in
  let j = graph_to_yojson ~panel_mode:"thesis" g in
  Alcotest.(check string) "panel_mode = thesis" "thesis"
    (string_field j "panel_mode")

let test_graph_yojson_all_levels () =
  let macro_g = build_macro
    ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] () in
  let meso_g  = build_meso ~companies:[] () in
  let micro_g = build_micro ~focal_code:"F" ~focal_name:"F"
    ~focal_stage:Stage.Startup ~focal_leverage:0.1
    ~peers:[] ~crisis_events:[] () in
  List.iter2 (fun g expected ->
    let j = graph_to_yojson g in
    Alcotest.(check string) ("level = " ^ expected) expected
      (string_field j "level")
  ) [macro_g; meso_g; micro_g] ["macro"; "meso"; "micro"]

let contract_suite = [
  "node_count consistent",   `Quick, test_graph_yojson_node_count_consistent;
  "persona field",           `Quick, test_graph_yojson_persona_field;
  "panel_mode field",        `Quick, test_graph_yojson_panel_mode;
  "all levels serialize",    `Quick, test_graph_yojson_all_levels;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "graph_export" [
  "node_builders", node_builder_suite;
  "json_schema",   schema_suite;
  "macro",         macro_suite;
  "meso",          meso_suite;
  "micro",         micro_suite;
  "caps",          cap_suite;
  "contract",      contract_suite;
]
