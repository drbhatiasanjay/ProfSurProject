(** PROV-O provenance layer — Phase 8.

    Implements a subset of the W3C PROV Ontology:
      Entity, Activity, Agent, wasGeneratedBy, wasAttributedTo,
      used, wasAssociatedWith, wasDerivedFrom.

    Serialises to JSON-LD (application/ld+json) and provides Schema.org
    metadata helpers for model runs and dataset descriptions. *)

open Domain

(* ── IRI helpers ─────────────────────────────────────────────────────────── *)

type iri = string

let base_iri = "https://lifecycle-leverage.dev/prov/"

let make_iri kind id = base_iri ^ kind ^ "/" ^ id

(* ── Core types ──────────────────────────────────────────────────────────── *)

type entity = {
  e_id    : iri;
  e_type  : string;
  e_label : string;
  e_attrs : (string * string) list;
}

type activity = {
  a_id      : iri;
  a_type    : string;
  a_label   : string;
  a_started : string option;
  a_ended   : string option;
  a_attrs   : (string * string) list;
}

type agent = {
  ag_id    : iri;
  ag_type  : string;
  ag_label : string;
}

type relation =
  | WasGeneratedBy    of { entity: iri; activity: iri; time: string option }
  | WasAttributedTo   of { entity: iri; agent: iri }
  | Used              of { activity: iri; entity: iri; time: string option }
  | WasAssociatedWith of { activity: iri; agent: iri; role: string option }
  | WasDerivedFrom    of { derived: iri; source: iri }

type provenance_doc = {
  entities   : entity list;
  activities : activity list;
  agents     : agent list;
  relations  : relation list;
}

(* ── Smart constructors ──────────────────────────────────────────────────── *)

let make_entity ~id ~type_ ~label ?(attrs = []) () =
  { e_id = id; e_type = type_; e_label = label; e_attrs = attrs }

let make_activity ~id ~type_ ~label ?started ?ended ?(attrs = []) () =
  { a_id = id; a_type = type_; a_label = label;
    a_started = started; a_ended = ended; a_attrs = attrs }

let make_agent ~id ~type_ ~label =
  { ag_id = id; ag_type = type_; ag_label = label }

let empty_doc = { entities = []; activities = []; agents = []; relations = [] }

(* ── JSON-LD serialiser ──────────────────────────────────────────────────── *)

let jsonld_context = `Assoc [
  "prov",   `String "http://www.w3.org/ns/prov#";
  "schema", `String "http://schema.org/";
  "xsd",    `String "http://www.w3.org/2001/XMLSchema#";
  "llev",   `String "https://lifecycle-leverage.dev/prov/";
]

let entity_to_jsonld (e : entity) : Yojson.Safe.t =
  let base = [
    "@id",        `String e.e_id;
    "@type",      `List [`String "prov:Entity"; `String ("llev:" ^ e.e_type)];
    "prov:label", `String e.e_label;
  ] in
  let extras = List.map (fun (k, v) -> k, `String v) e.e_attrs in
  `Assoc (base @ extras)

let activity_to_jsonld (a : activity) : Yojson.Safe.t =
  let base = [
    "@id",        `String a.a_id;
    "@type",      `List [`String "prov:Activity"; `String ("llev:" ^ a.a_type)];
    "prov:label", `String a.a_label;
  ] in
  let opt_field k = function
    | None   -> []
    | Some v -> [k, `Assoc ["@value", `String v;
                              "@type",  `String "xsd:dateTime"]]
  in
  let time_fields =
    opt_field "prov:startedAtTime" a.a_started @
    opt_field "prov:endedAtTime"   a.a_ended
  in
  let extras = List.map (fun (k, v) -> k, `String v) a.a_attrs in
  `Assoc (base @ time_fields @ extras)

let agent_to_jsonld (ag : agent) : Yojson.Safe.t =
  `Assoc [
    "@id",        `String ag.ag_id;
    "@type",      `List [`String "prov:Agent"; `String ("llev:" ^ ag.ag_type)];
    "prov:label", `String ag.ag_label;
  ]

let relation_to_jsonld (r : relation) : Yojson.Safe.t =
  match r with
  | WasGeneratedBy { entity; activity; time } ->
      let base = [
        "@type",               `String "prov:wasGeneratedBy";
        "prov:entity",         `Assoc ["@id", `String entity];
        "prov:activity",       `Assoc ["@id", `String activity];
      ] in
      let tf = match time with
        | None -> []
        | Some t -> ["prov:atTime", `Assoc ["@value", `String t;
                                             "@type",  `String "xsd:dateTime"]]
      in
      `Assoc (base @ tf)
  | WasAttributedTo { entity; agent } ->
      `Assoc [
        "@type",         `String "prov:wasAttributedTo";
        "prov:entity",   `Assoc ["@id", `String entity];
        "prov:agent",    `Assoc ["@id", `String agent];
      ]
  | Used { activity; entity; time } ->
      let base = [
        "@type",           `String "prov:used";
        "prov:activity",   `Assoc ["@id", `String activity];
        "prov:entity",     `Assoc ["@id", `String entity];
      ] in
      let tf = match time with
        | None -> []
        | Some t -> ["prov:atTime", `Assoc ["@value", `String t;
                                             "@type",  `String "xsd:dateTime"]]
      in
      `Assoc (base @ tf)
  | WasAssociatedWith { activity; agent; role } ->
      let base = [
        "@type",           `String "prov:wasAssociatedWith";
        "prov:activity",   `Assoc ["@id", `String activity];
        "prov:agent",      `Assoc ["@id", `String agent];
      ] in
      let rf = match role with
        | None   -> []
        | Some r -> ["prov:hadRole", `String r]
      in
      `Assoc (base @ rf)
  | WasDerivedFrom { derived; source } ->
      `Assoc [
        "@type",             `String "prov:wasDerivedFrom";
        "prov:generatedEntity", `Assoc ["@id", `String derived];
        "prov:usedEntity",   `Assoc ["@id", `String source];
      ]

let to_jsonld (doc : provenance_doc) : Yojson.Safe.t =
  let graph =
    List.map entity_to_jsonld   doc.entities   @
    List.map activity_to_jsonld doc.activities @
    List.map agent_to_jsonld    doc.agents     @
    List.map relation_to_jsonld doc.relations
  in
  `Assoc [
    "@context", jsonld_context;
    "@graph",   `List graph;
  ]

(* ── Schema.org metadata helpers ─────────────────────────────────────────── *)

let software_version = "0.2.0-phase8"

let schema_software_application () : Yojson.Safe.t =
  `Assoc [
    "@context",              `String "http://schema.org/";
    "@type",                 `String "SoftwareApplication";
    "name",                  `String "LifeCycle Leverage OCaml Service";
    "softwareVersion",       `String software_version;
    "applicationCategory",   `String "FinancialAnalysis";
    "operatingSystem",       `String "Linux/Windows/macOS";
    "url",                   `String "https://lifecycle-leverage.dev";
  ]

let schema_dataset ~id ~name ~description : Yojson.Safe.t =
  `Assoc [
    "@context",   `String "http://schema.org/";
    "@type",      `String "Dataset";
    "@id",        `String id;
    "name",       `String name;
    "description",`String description;
    "creator",    `Assoc [
      "@type", `String "SoftwareApplication";
      "name",  `String "LifeCycle Leverage OCaml Service";
    ];
  ]

(* ── Convenience builders ────────────────────────────────────────────────── *)

let service_agent =
  make_agent
    ~id:(make_iri "agent" "lifecycle-ocaml-service")
    ~type_:"software"
    ~label:("lifecycle-ontology v" ^ software_version)

let for_graph_export ~level ~persona ~panel_mode ~graph_id : provenance_doc =
  let act_id = make_iri "activity" ("graph_export_" ^ level) in
  let activity = make_activity
    ~id:act_id ~type_:"graph_export"
    ~label:(Printf.sprintf "Graph export: %s/%s/%s" level persona panel_mode)
    ~attrs:["llev:level", level; "llev:persona", persona;
            "llev:panel_mode", panel_mode]
    () in
  let entity = make_entity
    ~id:graph_id ~type_:"graph_json"
    ~label:(Printf.sprintf "%s graph for %s" level persona)
    () in
  let persona_agent = make_agent
    ~id:(make_iri "agent" ("persona_" ^ persona))
    ~type_:"persona"
    ~label:persona in
  { entities   = [entity];
    activities = [activity];
    agents     = [service_agent; persona_agent];
    relations  = [
      WasGeneratedBy    { entity = graph_id; activity = act_id; time = None };
      WasAttributedTo   { entity = graph_id; agent = service_agent.ag_id };
      WasAssociatedWith { activity = act_id; agent = persona_agent.ag_id;
                          role = Some "requestingPersona" };
    ];
  }

let for_model_run ~model_kind ~persona ~run_id : provenance_doc =
  let act_id = make_iri "activity" ("model_run_" ^ run_id) in
  let result_id = make_iri "entity" ("result_" ^ run_id) in
  let activity = make_activity
    ~id:act_id ~type_:"model_run"
    ~label:(Printf.sprintf "Model run: %s (persona=%s)" model_kind persona)
    ~attrs:["llev:model_kind", model_kind; "llev:persona", persona]
    () in
  let entity = make_entity
    ~id:result_id ~type_:"model_result"
    ~label:(Printf.sprintf "%s result for %s" model_kind persona)
    () in
  let persona_agent = make_agent
    ~id:(make_iri "agent" ("persona_" ^ persona))
    ~type_:"persona"
    ~label:persona in
  { entities   = [entity];
    activities = [activity];
    agents     = [service_agent; persona_agent];
    relations  = [
      WasGeneratedBy    { entity = result_id; activity = act_id; time = None };
      WasAttributedTo   { entity = result_id; agent = service_agent.ag_id };
      WasAssociatedWith { activity = act_id; agent = persona_agent.ag_id;
                          role = Some "requestingPersona" };
    ];
  }

let for_normative_eval ~stat_id ~persona ~eval_id : provenance_doc =
  let act_id    = make_iri "activity" ("normative_eval_" ^ eval_id) in
  let result_id = make_iri "entity"   ("normative_result_" ^ eval_id) in
  let input_id  = make_iri "entity"   ("input_band_" ^ stat_id) in
  let activity = make_activity
    ~id:act_id ~type_:"normative_evaluation"
    ~label:(Printf.sprintf "Normative evaluation of %s (persona=%s)" stat_id persona)
    ~attrs:["llev:stat_id", stat_id; "llev:persona", persona]
    () in
  let result_entity = make_entity
    ~id:result_id ~type_:"normative_result"
    ~label:(Printf.sprintf "Normative result: %s/%s" stat_id persona)
    () in
  let input_entity = make_entity
    ~id:input_id ~type_:"normative_band"
    ~label:("Normative band: " ^ stat_id)
    () in
  let persona_agent = make_agent
    ~id:(make_iri "agent" ("persona_" ^ persona))
    ~type_:"persona"
    ~label:persona in
  { entities   = [result_entity; input_entity];
    activities = [activity];
    agents     = [service_agent; persona_agent];
    relations  = [
      WasGeneratedBy    { entity = result_id; activity = act_id; time = None };
      Used              { activity = act_id; entity = input_id; time = None };
      WasDerivedFrom    { derived = result_id; source = input_id };
      WasAttributedTo   { entity = result_id; agent = service_agent.ag_id };
      WasAssociatedWith { activity = act_id; agent = persona_agent.ag_id;
                          role = Some "evaluatingPersona" };
    ];
  }

(* ── Persona-aware agent constructor ─────────────────────────────────────── *)

let agent_of_persona (p : Persona.t) : agent =
  let s = Persona.to_string p in
  make_agent
    ~id:(make_iri "agent" ("persona_" ^ s))
    ~type_:"persona"
    ~label:(Persona.display_name p)
