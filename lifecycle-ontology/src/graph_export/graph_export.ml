(** Graph export — Phase 5.

    Builds Macro / Meso / Micro graphs from pre-loaded domain data and
    serialises them to JSON matching the graph_bridge.py contract.
    No DB calls here — data arrives as plain OCaml lists from the API layer. *)

open Domain

(* ── Core types ──────────────────────────────────────────────────────────── *)

type node_type =
  | StageNode     of Stage.t
  | IndustryNode  of string
  | EventNode     of Period.event
  | CompanyNode   of { code : string; name : string }

type edge_type =
  | InIndustry
  | AtStage
  | Transition    of { from_stage : Stage.t; to_stage : Stage.t }
  | IsPeerOf      of { similarity_score : float }
  | ExperiencedEvent
  | HasNorm

type node = {
  id      : string;
  kind    : node_type;
  label   : string;
  tooltip : string;
}

type edge = {
  from_id : string;
  to_id   : string;
  kind    : edge_type;
  weight  : float;
}

type graph = {
  level : [ `Macro | `Meso | `Micro ];
  nodes : node list;
  edges : edge list;
}

(* ── Hard node caps (OCaml contract — Python stub must match) ────────────── *)

let macro_node_cap   = 21
let meso_company_cap = 80
let micro_peer_cap   = 20

(* ── Visual properties (consistent with graph_bridge.py) ────────────────── *)

let stage_color = function
  | Stage.Startup   -> "#4CAF50"
  | Stage.Growth    -> "#8BC34A"
  | Stage.Maturity  -> "#2196F3"
  | Stage.Shakeout1 -> "#FF9800"
  | Stage.Shakeout2 -> "#FF5722"
  | Stage.Shakeout3 -> "#F44336"
  | Stage.Decline   -> "#9C27B0"
  | Stage.Decay     -> "#607D8B"

let event_color = function
  | Period.GFC   -> "#E91E63"
  | Period.IBC   -> "#9C27B0"
  | Period.COVID -> "#FF5722"

let industry_color = "#90A4AE"
let company_color  = "#78909C"

let node_color = function
  | StageNode s    -> stage_color s
  | IndustryNode _ -> industry_color
  | EventNode ev   -> event_color ev
  | CompanyNode _  -> company_color

let node_size = function
  | StageNode _    -> 28
  | IndustryNode _ -> 18
  | EventNode _    -> 14
  | CompanyNode _  -> 12

(* ── Type-string helpers ─────────────────────────────────────────────────── *)

let node_type_to_string = function
  | StageNode _    -> "stage"
  | IndustryNode _ -> "industry"
  | EventNode _    -> "event"
  | CompanyNode _  -> "company"

let edge_type_to_string = function
  | InIndustry       -> "in_industry"
  | AtStage          -> "at_stage"
  | Transition _     -> "transition"
  | IsPeerOf _       -> "is_peer_of"
  | ExperiencedEvent -> "experienced_event"
  | HasNorm          -> "has_norm"

let edge_type_label = function
  | InIndustry                           -> "in_industry"
  | AtStage                              -> "at_stage"
  | Transition { from_stage; to_stage }  ->
      Stage.to_string from_stage ^ "\xe2\x86\x92" ^ Stage.to_string to_stage
  | IsPeerOf _                           -> "is_peer_of"
  | ExperiencedEvent                     -> "experienced_event"
  | HasNorm                              -> "has_norm"

let level_to_string = function
  | `Macro -> "macro"
  | `Meso  -> "meso"
  | `Micro -> "micro"

(* ── ID helpers ──────────────────────────────────────────────────────────── *)

let slug s =
  String.lowercase_ascii s
  |> String.split_on_char ' '
  |> String.concat "_"

let stage_id  s  = "stage_"    ^ slug (Stage.to_string s)
let industry_id i = "industry_" ^ slug i
let event_id  ev = "event_"    ^ String.lowercase_ascii (Period.event_to_string ev)
let company_id c = "company_"  ^ c

(* ── Node builders ───────────────────────────────────────────────────────── *)

let make_stage_node (s : Stage.t) : node =
  { id      = stage_id s;
    kind    = StageNode s;
    label   = Stage.to_string s;
    tooltip = Printf.sprintf "%s stage — %s lifecycle phase"
                (Stage.to_string s) (Stage.group s) }

let make_industry_node industry ~company_count : node =
  { id      = industry_id industry;
    kind    = IndustryNode industry;
    label   = industry;
    tooltip = Printf.sprintf "%s — %d companies" industry company_count }

let make_event_node (ev : Period.event) : node =
  { id      = event_id ev;
    kind    = EventNode ev;
    label   = Period.event_to_string ev;
    tooltip = (match ev with
               | Period.GFC   -> "Global Financial Crisis (2007-09)"
               | Period.IBC   -> "Insolvency & Bankruptcy Code (2016)"
               | Period.COVID -> "COVID-19 Pandemic (2020-21)") }

let make_company_node ~code ~name ~(stage : Stage.t) ~leverage : node =
  { id      = company_id code;
    kind    = CompanyNode { code; name };
    label   = name;
    tooltip = Printf.sprintf "%s | Stage: %s | Leverage: %.2f"
                name (Stage.to_string stage) leverage }

(* ── JSON serialisers — matches graph_bridge.py JSON contract ────────────── *)

let node_to_yojson (n : node) : Yojson.Safe.t =
  `Assoc [
    "id",      `String n.id;
    "type",    `String (node_type_to_string n.kind);
    "label",   `String n.label;
    "color",   `String (node_color n.kind);
    "size",    `Int    (node_size n.kind);
    "tooltip", `String n.tooltip;
  ]

let edge_to_yojson (e : edge) : Yojson.Safe.t =
  `Assoc [
    "from",   `String e.from_id;
    "to",     `String e.to_id;
    "type",   `String (edge_type_to_string e.kind);
    "weight", `Float  e.weight;
    "label",  `String (edge_type_label e.kind);
  ]

let graph_to_yojson ?(persona = Persona.CorporateCFO) ?(panel_mode = "latest")
    (g : graph) : Yojson.Safe.t =
  `Assoc [
    "level",      `String (level_to_string g.level);
    "persona",    Persona.to_yojson persona;
    "panel_mode", `String panel_mode;
    "node_count", `Int (List.length g.nodes);
    "nodes",      `List (List.map node_to_yojson g.nodes);
    "edges",      `List (List.map edge_to_yojson g.edges);
  ]

(* ── Cap validation ──────────────────────────────────────────────────────── *)

let node_count  g = List.length g.nodes
let edge_count  g = List.length g.edges

let nodes_of_type_str t g =
  List.filter (fun (n : node) -> node_type_to_string n.kind = t) g.nodes

type cap_violation =
  | MacroNodeCap    of int
  | MesoCompanyCap  of int
  | MicroPeerCap    of int

let validate_caps (g : graph) : cap_violation option =
  match g.level with
  | `Macro ->
      let n = node_count g in
      if n > macro_node_cap then Some (MacroNodeCap n) else None
  | `Meso ->
      let n = List.length (nodes_of_type_str "company" g) in
      if n > meso_company_cap then Some (MesoCompanyCap n) else None
  | `Micro ->
      let n_peers = max 0 (List.length (nodes_of_type_str "company" g) - 1) in
      if n_peers > micro_peer_cap then Some (MicroPeerCap n_peers) else None

(* ── Graph builders ──────────────────────────────────────────────────────── *)

(** Build a Macro graph from pre-aggregated data.
    [stage_industry_counts] : (stage, industry, count)
    [stage_transitions]     : (from_stage, to_stage, probability)
    [crisis_stages]         : (event, affected_stages) *)
let build_macro
    ~(stage_industry_counts : (Stage.t * string * int) list)
    ~(stage_transitions     : (Stage.t * Stage.t * float) list)
    ~(crisis_stages         : (Period.event * Stage.t list) list)
    () : graph =
  (* 8 stage nodes always present *)
  let stage_nodes = List.map make_stage_node Stage.all in
  (* Industry nodes — aggregate counts, keep top N so total ≤ macro_node_cap *)
  let industry_totals =
    let tbl = Hashtbl.create 16 in
    List.iter (fun (_, ind, cnt) ->
      Hashtbl.replace tbl ind
        (cnt + try Hashtbl.find tbl ind with Not_found -> 0)
    ) stage_industry_counts;
    Hashtbl.fold (fun k v acc -> (k, v) :: acc) tbl []
    |> List.sort (fun (_, a) (_, b) -> compare b a) in
  let n_event_slots  = List.length crisis_stages in
  let max_industries = macro_node_cap - List.length Stage.all - n_event_slots in
  let industry_totals = List.filteri (fun i _ -> i < (max 0 max_industries)) industry_totals in
  let industry_nodes  = List.map (fun (ind, cnt) ->
    make_industry_node ind ~company_count:cnt) industry_totals in
  let event_nodes = List.map (fun (ev, _) -> make_event_node ev) crisis_stages in
  let nodes = stage_nodes @ industry_nodes @ event_nodes in
  (* Stage→Industry edges (weight = company count) *)
  let ind_id_set = List.map (fun n -> n.id) industry_nodes in
  let si_edges = List.filter_map (fun (st, ind, cnt) ->
    let iid = industry_id ind in
    if List.mem iid ind_id_set then
      Some { from_id = stage_id st; to_id = iid;
             kind = InIndustry; weight = float_of_int cnt }
    else None) stage_industry_counts in
  (* Stage→Stage transition edges (weight = probability) *)
  let trans_edges = List.map (fun (fs, ts, p) ->
    { from_id = stage_id fs; to_id = stage_id ts;
      kind = Transition { from_stage = fs; to_stage = ts }; weight = p }
  ) stage_transitions in
  (* Event→Stage edges *)
  let ev_edges = List.concat_map (fun (ev, stages) ->
    List.map (fun st ->
      { from_id = event_id ev; to_id = stage_id st;
        kind = ExperiencedEvent; weight = 1.0 }) stages
  ) crisis_stages in
  { level = `Macro; nodes; edges = si_edges @ trans_edges @ ev_edges }

(** Build a Meso graph from a company list.
    [companies] : (code, name, stage, industry, leverage) — pre-sorted *)
let build_meso
    ~(companies : (string * string * Stage.t * string * float) list)
    () : graph =
  let companies = List.filteri (fun i _ -> i < meso_company_cap) companies in
  let cmp_nodes = List.map (fun (code, name, st, _, lev) ->
    make_company_node ~code ~name ~stage:st ~leverage:lev) companies in
  let stages = List.sort_uniq Stage.compare
                 (List.map (fun (_, _, st, _, _) -> st) companies) in
  let stage_nodes = List.map make_stage_node stages in
  let industries =
    List.sort_uniq String.compare
      (List.map (fun (_, _, _, ind, _) -> ind) companies) in
  let ind_nodes = List.map (fun ind ->
    let cnt = List.length
                (List.filter (fun (_, _, _, i, _) -> i = ind) companies) in
    make_industry_node ind ~company_count:cnt) industries in
  let c_stage_edges = List.map (fun (code, _, st, _, _) ->
    { from_id = company_id code; to_id = stage_id st;
      kind = AtStage; weight = 1.0 }) companies in
  let c_ind_edges = List.map (fun (code, _, _, ind, _) ->
    { from_id = company_id code; to_id = industry_id ind;
      kind = InIndustry; weight = 1.0 }) companies in
  { level = `Meso;
    nodes = cmp_nodes @ stage_nodes @ ind_nodes;
    edges = c_stage_edges @ c_ind_edges }

(** Build a Micro graph for a focal company and its peers.
    [peers] : (code, name, stage, leverage, similarity_score) — sorted desc by sim *)
let build_micro
    ~(focal_code     : string)
    ~(focal_name     : string)
    ~(focal_stage    : Stage.t)
    ~(focal_leverage : float)
    ~(peers          : (string * string * Stage.t * float * float) list)
    ~(crisis_events  : Period.event list)
    () : graph =
  let focal_node  = make_company_node
    ~code:focal_code ~name:focal_name
    ~stage:focal_stage ~leverage:focal_leverage in
  let peers       = List.filteri (fun i _ -> i < micro_peer_cap) peers in
  let peer_nodes  = List.map (fun (code, name, st, lev, _sim) ->
    make_company_node ~code ~name ~stage:st ~leverage:lev) peers in
  let event_nodes = List.map make_event_node crisis_events in
  let peer_edges  = List.map (fun (code, _, _, _, sim) ->
    { from_id = company_id focal_code; to_id = company_id code;
      kind = IsPeerOf { similarity_score = sim }; weight = sim }) peers in
  let ev_edges    = List.map (fun ev ->
    { from_id = company_id focal_code; to_id = event_id ev;
      kind = ExperiencedEvent; weight = 1.0 }) crisis_events in
  { level = `Micro;
    nodes = focal_node :: peer_nodes @ event_nodes;
    edges = peer_edges @ ev_edges }
