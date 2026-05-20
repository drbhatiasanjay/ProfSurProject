(** Phase 8 — PROV-O provenance module tests. *)

open Provenance
open Yojson.Safe.Util

(* ── Helpers ─────────────────────────────────────────────────────────────── *)

let graph_of_doc doc =
  to_jsonld doc |> member "@graph" |> to_list

let find_by_type type_str nodes =
  List.filter (fun n ->
    match n |> member "@type" with
    | `String s -> s = type_str
    | `List ts  -> List.mem (`String type_str) ts
    | _         -> false) nodes

(* ── Smart constructor tests ─────────────────────────────────────────────── *)

let test_make_entity () =
  let e = make_entity ~id:"urn:test:e1" ~type_:"graph_json" ~label:"test graph" () in
  Alcotest.(check string) "id"    "urn:test:e1"  e.e_id;
  Alcotest.(check string) "type"  "graph_json"   e.e_type;
  Alcotest.(check string) "label" "test graph"   e.e_label;
  Alcotest.(check bool) "attrs empty" true (e.e_attrs = [])

let test_make_entity_with_attrs () =
  let e = make_entity ~id:"urn:e2" ~type_:"t" ~label:"l"
            ~attrs:["llev:level", "macro"] () in
  Alcotest.(check int) "1 attr" 1 (List.length e.e_attrs)

let test_make_activity () =
  let a = make_activity ~id:"urn:act:1" ~type_:"graph_export" ~label:"export" () in
  Alcotest.(check string) "id"      "urn:act:1"    a.a_id;
  Alcotest.(check bool)   "no start" true (a.a_started = None);
  Alcotest.(check bool)   "no end"   true (a.a_ended   = None)

let test_make_activity_with_times () =
  let a = make_activity ~id:"urn:act:2" ~type_:"t" ~label:"l"
            ~started:"2024-01-01T00:00:00Z" ~ended:"2024-01-01T01:00:00Z" () in
  Alcotest.(check bool) "start set" true (a.a_started <> None);
  Alcotest.(check bool) "end set"   true (a.a_ended   <> None)

let test_make_agent () =
  let ag = make_agent ~id:"urn:ag:1" ~type_:"software" ~label:"OCaml svc" in
  Alcotest.(check string) "id"    "urn:ag:1"   ag.ag_id;
  Alcotest.(check string) "type"  "software"   ag.ag_type;
  Alcotest.(check string) "label" "OCaml svc"  ag.ag_label

let constructor_suite = [
  "make_entity basic",       `Quick, test_make_entity;
  "make_entity with attrs",  `Quick, test_make_entity_with_attrs;
  "make_activity basic",     `Quick, test_make_activity;
  "make_activity with times",`Quick, test_make_activity_with_times;
  "make_agent",              `Quick, test_make_agent;
]

(* ── JSON-LD structure tests ─────────────────────────────────────────────── *)

let test_jsonld_has_context () =
  let j = to_jsonld empty_doc in
  let ctx = j |> member "@context" in
  Alcotest.(check bool) "@context present" true (ctx <> `Null);
  let prov_ns = ctx |> member "prov" |> to_string in
  Alcotest.(check string) "prov ns" "http://www.w3.org/ns/prov#" prov_ns

let test_jsonld_has_graph () =
  let j = to_jsonld empty_doc in
  let g = j |> member "@graph" in
  Alcotest.(check bool) "@graph present" true (g <> `Null);
  Alcotest.(check bool) "@graph is list" true
    (match g with `List _ -> true | _ -> false)

let test_jsonld_entity_in_graph () =
  let e = make_entity ~id:"urn:e1" ~type_:"graph_json" ~label:"test" () in
  let doc = { empty_doc with entities = [e] } in
  let g = graph_of_doc doc in
  Alcotest.(check bool) "entity in graph" true (List.length g >= 1);
  let entity_nodes = find_by_type "prov:Entity" g in
  Alcotest.(check bool) "entity typed" true (entity_nodes <> [])

let test_jsonld_activity_in_graph () =
  let a = make_activity ~id:"urn:a1" ~type_:"graph_export" ~label:"export" () in
  let doc = { empty_doc with activities = [a] } in
  let g = graph_of_doc doc in
  let act_nodes = find_by_type "prov:Activity" g in
  Alcotest.(check bool) "activity typed" true (act_nodes <> [])

let test_jsonld_agent_in_graph () =
  let ag = make_agent ~id:"urn:ag1" ~type_:"persona" ~label:"CFO" in
  let doc = { empty_doc with agents = [ag] } in
  let g = graph_of_doc doc in
  let ag_nodes = find_by_type "prov:Agent" g in
  Alcotest.(check bool) "agent typed" true (ag_nodes <> [])

let test_jsonld_relation_was_generated_by () =
  let rel = WasGeneratedBy { entity = "urn:e1"; activity = "urn:a1"; time = None } in
  let doc = { empty_doc with relations = [rel] } in
  let g = graph_of_doc doc in
  let rel_nodes = find_by_type "prov:wasGeneratedBy" g in
  Alcotest.(check bool) "wasGeneratedBy present" true (rel_nodes <> [])

let test_jsonld_relation_was_attributed_to () =
  let rel = WasAttributedTo { entity = "urn:e1"; agent = "urn:ag1" } in
  let doc = { empty_doc with relations = [rel] } in
  let g = graph_of_doc doc in
  let rel_nodes = find_by_type "prov:wasAttributedTo" g in
  Alcotest.(check bool) "wasAttributedTo present" true (rel_nodes <> [])

let test_jsonld_relation_used () =
  let rel = Used { activity = "urn:a1"; entity = "urn:e1"; time = None } in
  let doc = { empty_doc with relations = [rel] } in
  let g = graph_of_doc doc in
  let used_nodes = find_by_type "prov:used" g in
  Alcotest.(check bool) "used present" true (used_nodes <> [])

let test_jsonld_relation_was_associated_with () =
  let rel = WasAssociatedWith { activity = "urn:a1"; agent = "urn:ag1";
                                 role = Some "orchestrator" } in
  let doc = { empty_doc with relations = [rel] } in
  let g = graph_of_doc doc in
  let assoc_nodes = find_by_type "prov:wasAssociatedWith" g in
  Alcotest.(check bool) "wasAssociatedWith present" true (assoc_nodes <> []);
  let role = List.hd assoc_nodes |> member "prov:hadRole" |> to_string in
  Alcotest.(check string) "role field" "orchestrator" role

let test_jsonld_relation_was_derived_from () =
  let rel = WasDerivedFrom { derived = "urn:e2"; source = "urn:e1" } in
  let doc = { empty_doc with relations = [rel] } in
  let g = graph_of_doc doc in
  let derived_nodes = find_by_type "prov:wasDerivedFrom" g in
  Alcotest.(check bool) "wasDerivedFrom present" true (derived_nodes <> [])

let test_jsonld_activity_time_fields () =
  let a = make_activity ~id:"urn:a1" ~type_:"t" ~label:"l"
            ~started:"2024-01-01T00:00:00Z" () in
  let doc = { empty_doc with activities = [a] } in
  let g = graph_of_doc doc in
  let act = List.hd (find_by_type "prov:Activity" g) in
  let started = act |> member "prov:startedAtTime" in
  Alcotest.(check bool) "startedAtTime present" true (started <> `Null)

let jsonld_suite = [
  "has @context",               `Quick, test_jsonld_has_context;
  "has @graph",                 `Quick, test_jsonld_has_graph;
  "entity in graph",            `Quick, test_jsonld_entity_in_graph;
  "activity in graph",          `Quick, test_jsonld_activity_in_graph;
  "agent in graph",             `Quick, test_jsonld_agent_in_graph;
  "wasGeneratedBy",             `Quick, test_jsonld_relation_was_generated_by;
  "wasAttributedTo",            `Quick, test_jsonld_relation_was_attributed_to;
  "used",                       `Quick, test_jsonld_relation_used;
  "wasAssociatedWith + role",   `Quick, test_jsonld_relation_was_associated_with;
  "wasDerivedFrom",             `Quick, test_jsonld_relation_was_derived_from;
  "activity time fields",       `Quick, test_jsonld_activity_time_fields;
]

(* ── Schema.org tests ────────────────────────────────────────────────────── *)

let test_schema_software_application () =
  let j = schema_software_application () in
  let t = j |> member "@type" |> to_string in
  Alcotest.(check string) "type = SoftwareApplication" "SoftwareApplication" t;
  Alcotest.(check bool) "version present" true
    (String.length (j |> member "softwareVersion" |> to_string) > 0)

let test_schema_dataset () =
  let j = schema_dataset
            ~id:"urn:ds:1"
            ~name:"Test Dataset"
            ~description:"A test dataset" in
  Alcotest.(check string) "type = Dataset" "Dataset"
    (j |> member "@type" |> to_string);
  Alcotest.(check string) "name" "Test Dataset"
    (j |> member "name" |> to_string)

let schema_suite = [
  "schema:SoftwareApplication",  `Quick, test_schema_software_application;
  "schema:Dataset",              `Quick, test_schema_dataset;
]

(* ── Convenience builder tests ───────────────────────────────────────────── *)

let test_for_graph_export () =
  let gid = make_iri "entity" "graph_macro_test" in
  let doc = for_graph_export
              ~level:"macro" ~persona:"CorporateCFO"
              ~panel_mode:"latest" ~graph_id:gid in
  Alcotest.(check bool) "has entities"   true (doc.entities   <> []);
  Alcotest.(check bool) "has activities" true (doc.activities <> []);
  Alcotest.(check bool) "has agents"     true (doc.agents     <> []);
  Alcotest.(check bool) "has relations"  true (doc.relations  <> [])

let test_for_graph_export_jsonld_valid () =
  let gid = make_iri "entity" "graph_macro_test" in
  let doc = for_graph_export
              ~level:"macro" ~persona:"RatingAnalyst"
              ~panel_mode:"thesis" ~graph_id:gid in
  let j = to_jsonld doc in
  let g = j |> member "@graph" |> to_list in
  Alcotest.(check bool) "graph non-empty" true (List.length g > 0)

let test_for_model_run () =
  let doc = for_model_run
              ~model_kind:"OLS" ~persona:"FacultyPhDSupervisor"
              ~run_id:"run_42" in
  Alcotest.(check bool) "has entities"  true (doc.entities  <> []);
  Alcotest.(check bool) "has relations" true (doc.relations <> [])

let test_for_normative_eval () =
  let doc = for_normative_eval
              ~stat_id:"leverage_ratio" ~persona:"RatingAnalyst"
              ~eval_id:"eval_99" in
  Alcotest.(check int) "2 entities" 2 (List.length doc.entities);
  let derived = List.filter
    (function WasDerivedFrom _ -> true | _ -> false) doc.relations in
  Alcotest.(check bool) "wasDerivedFrom present" true (derived <> [])

let test_agent_of_persona () =
  let open Domain.Persona in
  let ag = agent_of_persona RatingAnalyst in
  Alcotest.(check string) "type = persona" "persona" ag.ag_type;
  Alcotest.(check bool)   "label non-empty" true (String.length ag.ag_label > 0)

let convenience_suite = [
  "for_graph_export",            `Quick, test_for_graph_export;
  "for_graph_export jsonld",     `Quick, test_for_graph_export_jsonld_valid;
  "for_model_run",               `Quick, test_for_model_run;
  "for_normative_eval",          `Quick, test_for_normative_eval;
  "agent_of_persona",            `Quick, test_agent_of_persona;
]

(* ── Entry point ─────────────────────────────────────────────────────────── *)

let () = Alcotest.run "provenance" [
  "constructors",  constructor_suite;
  "jsonld",        jsonld_suite;
  "schema_org",    schema_suite;
  "convenience",   convenience_suite;
]
