(** Scenario DSL — Phase 4.

    A scenario captures a persona + stage context and a list of metric shocks
    (absolute deltas).  Applying a scenario to a baseline produces shock_result
    records that show before/after values for each shocked metric. *)

open Domain

(* ── Core types ──────────────────────────────────────────────────────────── *)

type shock = {
  metric : Metric.t;
  delta  : float;   (** absolute change, e.g. -0.02 for -200 bps profitability *)
}

type t = {
  id      : string;
  persona : Persona.t;
  stage   : Stage.t;
  shocks  : shock list;
}

(* ── Smart constructors ──────────────────────────────────────────────────── *)

let make ~id ~persona ~stage ~shocks () = { id; persona; stage; shocks }

(** Returns [Error] when shocks list is empty or contains duplicate metrics. *)
let make_validated ~id ~persona ~stage ~shocks () =
  if shocks = [] then
    Error "scenario must have at least one shock"
  else
    let ids  = List.map (fun s -> s.metric.id) shocks in
    let uniq = List.sort_uniq String.compare ids in
    if List.length uniq < List.length ids then
      Error "scenario shocks contain duplicate metrics"
    else Ok (make ~id ~persona ~stage ~shocks ())

(** Re-validate an existing scenario record. *)
let validate t =
  make_validated ~id:t.id ~persona:t.persona ~stage:t.stage ~shocks:t.shocks ()

(* ── Predicates ──────────────────────────────────────────────────────────── *)

(** True when any shock has a negative delta (tightening / stress). *)
let is_stress_scenario t =
  List.exists (fun s -> s.delta < 0.0) t.shocks

(** True when every shock has a non-negative delta (easing / recovery). *)
let is_recovery_scenario t =
  t.shocks <> [] && List.for_all (fun s -> s.delta >= 0.0) t.shocks

let shock_count t = List.length t.shocks

(* ── Labels ──────────────────────────────────────────────────────────────── *)

let to_label t =
  Printf.sprintf "[%s] %s scenario for %s"
    (Persona.to_string t.persona)
    (if is_stress_scenario t then "stress" else "baseline")
    (Stage.to_string t.stage)

let shock_to_label s =
  Printf.sprintf "%s %+.4f" s.metric.id s.delta

(* ── Application ─────────────────────────────────────────────────────────── *)

type shock_result = {
  metric    : Metric.t;
  baseline  : float;
  shocked   : float;
  delta_abs : float;
  delta_pct : float;  (** percentage-point change; nan if baseline = 0 *)
}

let apply_one baseline_map (sh : shock) =
  let b = match List.assoc_opt sh.metric.id baseline_map with
          | Some v -> v | None -> 0.0 in
  let s = b +. sh.delta in
  { metric    = sh.metric;
    baseline  = b;
    shocked   = s;
    delta_abs = sh.delta;
    delta_pct = if b = 0.0 then Float.nan
                else sh.delta /. (abs_float b) *. 100.0 }

(** Apply all shocks to [baseline_map] (a list of [(metric_id, value)] pairs).
    Metrics absent from the map are treated as having baseline 0.0. *)
let apply t ~baseline_map =
  List.map (apply_one baseline_map) t.shocks

(** Aggregate magnitude of all shocks: sum of |delta| across metrics. *)
let total_shock_magnitude t =
  List.fold_left (fun acc s -> acc +. abs_float s.delta) 0.0 t.shocks

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let shock_to_yojson (s : shock) : Yojson.Safe.t =
  `Assoc [
    "metric_id", `String s.metric.id;
    "delta",     `Float  s.delta;
  ]

let shock_of_yojson (j : Yojson.Safe.t) : (shock, string) result =
  let open Yojson.Safe.Util in
  try
    let id    = j |> member "metric_id" |> to_string in
    let delta = j |> member "delta"     |> to_float in
    match Metric.find_opt id with
    | None   -> Error ("shock_of_yojson: unknown metric_id \"" ^ id ^ "\"")
    | Some m -> Ok { metric = m; delta }
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("shock_of_yojson: " ^ msg)
  | Failure msg                          -> Error ("shock_of_yojson: " ^ msg)

let to_yojson (t : t) : Yojson.Safe.t =
  `Assoc [
    "id",      `String t.id;
    "persona", Persona.to_yojson t.persona;
    "stage",   Stage.to_yojson t.stage;
    "shocks",  `List (List.map shock_to_yojson t.shocks);
  ]

let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  let open Yojson.Safe.Util in
  try
    let id      = j |> member "id"      |> to_string in
    let persona = match Persona.of_yojson (j |> member "persona") with
                  | Ok p -> p | Error e -> failwith e in
    let stage   = match Stage.of_yojson (j |> member "stage") with
                  | Ok s -> s | Error e -> failwith e in
    let shocks  = j |> member "shocks" |> to_list
                  |> List.map (fun sj ->
                       match shock_of_yojson sj with
                       | Ok s -> s | Error e -> failwith e) in
    Ok (make ~id ~persona ~stage ~shocks ())
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("Scenario.of_yojson: " ^ msg)
  | Failure msg                          -> Error ("Scenario.of_yojson: " ^ msg)

let shock_result_to_yojson (r : shock_result) : Yojson.Safe.t =
  `Assoc [
    "metric_id",  `String r.metric.id;
    "baseline",   `Float  r.baseline;
    "shocked",    `Float  r.shocked;
    "delta_abs",  `Float  r.delta_abs;
    "delta_pct",  (if Float.is_nan r.delta_pct then `Null else `Float r.delta_pct);
  ]
