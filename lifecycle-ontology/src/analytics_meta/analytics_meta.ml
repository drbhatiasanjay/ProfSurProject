(** Analytics ontology — Phase 1 stub.

    Full implementations added in Phase 3 once domain types are complete.
    Type signatures here reflect the v4 spec; bodies are minimal stubs. *)

(* ── Model kinds ─────────────────────────────────────────────────────────── *)

type model_kind = Fe | Re | Ols | Gmm | Rf | Xgboost | Lstm | Gru

let model_kind_to_string = function
  | Fe -> "FE" | Re -> "RE" | Ols -> "OLS" | Gmm -> "GMM"
  | Rf -> "RF" | Xgboost -> "XGBoost" | Lstm -> "LSTM" | Gru -> "GRU"

open Domain

(* ── Hypothesis ──────────────────────────────────────────────────────────── *)

type hypothesis =
  | PeckingOrderUniversal
  | TradeOffStageConditional
  | CrisisEffect of Period.event

(* ── Model ───────────────────────────────────────────────────────────────── *)

type model = {
  id               : string;
  kind             : model_kind;
  dependent        : Metric.t;
  determinants     : Metric.t list;
  stage_scope      : Stage.t list;
  events_controlled: Period.event list;
  backend          : [ `Stata | `Python ];
}

(* ── Model run ───────────────────────────────────────────────────────────── *)

type model_run = {
  model         : model;
  run_id        : string;
  input_vintage : string;   (** "thesis" | "run3" | "cmie_2025" | "us_av_2024" *)
  filters       : (string * string) list;
  timestamp     : float;
}

(* ── Statistic ───────────────────────────────────────────────────────────── *)

type statistic_kind =
  | Coefficient     of { determinant : Metric.t }
  | TStat           of { determinant : Metric.t }
  | PValue          of { determinant : Metric.t }
  | RSquared
  | SoaCoefficient
  | TransitionProb  of { from_stage : Stage.t; to_stage : Stage.t }
  | DurationYears   of { stage : Stage.t }

type statistic = {
  id          : string;
  kind        : statistic_kind;
  value       : float;
  sign        : int;        (** -1 | 0 | 1 *)
  significant : bool;
  ci95        : (float * float) option;
  model_run   : model_run;
}

(* ── Normative band ─────────────────────────────────────────────────────── *)

type normative_band = {
  nb_id          : string;
  stage          : Stage.t;
  industry       : string;
  metric         : Metric.t;
  lower          : float;
  upper          : float;
  source_vintage : string;
}

(* ── Scenario ────────────────────────────────────────────────────────────── *)

type scenario = {
  scenario_id      : string;
  persona          : Persona.t;
  baseline_stage   : Stage.t;
  baseline_metrics : (Metric.t * float) list;
  shocks           : (Metric.t * float) list;
  model            : model;
}

(* ── Explanation ─────────────────────────────────────────────────────────── *)

type explanation = {
  expl_id  : string;
  personas : Persona.t list;
  template : string;
}

(* ── Visualization ───────────────────────────────────────────────────────── *)

type visualization = {
  viz_id : string;
}

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let model_kind_to_yojson k : Yojson.Safe.t = `String (model_kind_to_string k)

let model_kind_of_yojson j : (model_kind, string) result =
  match j with
  | `String "FE"      -> Ok Fe
  | `String "RE"      -> Ok Re
  | `String "OLS"     -> Ok Ols
  | `String "GMM"     -> Ok Gmm
  | `String "RF"      -> Ok Rf
  | `String "XGBoost" -> Ok Xgboost
  | `String "LSTM"    -> Ok Lstm
  | `String "GRU"     -> Ok Gru
  | `String s         -> Error ("model_kind_of_yojson: unknown kind \"" ^ s ^ "\"")
  | _                 -> Error "model_kind_of_yojson: expected JSON string"

let normative_band_to_yojson (nb : normative_band) : Yojson.Safe.t =
  `Assoc [
    "nb_id",          `String nb.nb_id;
    "stage",          Stage.to_yojson nb.stage;
    "industry",       `String nb.industry;
    "metric_id",      `String nb.metric.id;
    "lower",          `Float nb.lower;
    "upper",          `Float nb.upper;
    "source_vintage", `String nb.source_vintage;
  ]

let normative_band_of_yojson (j : Yojson.Safe.t) : (normative_band, string) result =
  let open Yojson.Safe.Util in
  try
    let nb_id          = j |> member "nb_id"          |> to_string in
    let industry       = j |> member "industry"       |> to_string in
    let source_vintage = j |> member "source_vintage" |> to_string in
    let lower          = j |> member "lower"          |> to_float in
    let upper          = j |> member "upper"          |> to_float in
    let stage = match Stage.of_yojson (j |> member "stage") with
                | Ok s -> s | Error e -> failwith e in
    let metric_id = j |> member "metric_id" |> to_string in
    let metric = match Metric.find_opt metric_id with
                 | Some m -> m
                 | None   -> failwith ("unknown metric_id: " ^ metric_id) in
    Ok { nb_id; stage; industry; metric; lower; upper; source_vintage }
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("normative_band_of_yojson: " ^ msg)
  | Failure msg                          -> Error ("normative_band_of_yojson: " ^ msg)

let explanation_to_yojson (e : explanation) : Yojson.Safe.t =
  `Assoc [
    "expl_id",  `String e.expl_id;
    "personas", `List (List.map Persona.to_yojson e.personas);
    "template", `String e.template;
  ]

let explanation_of_yojson (j : Yojson.Safe.t) : (explanation, string) result =
  let open Yojson.Safe.Util in
  try
    let expl_id  = j |> member "expl_id"  |> to_string in
    let template = j |> member "template" |> to_string in
    let personas = j |> member "personas" |> to_list
                   |> List.map (fun pj ->
                        match Persona.of_yojson pj with
                        | Ok p -> p | Error e -> failwith e) in
    Ok { expl_id; personas; template }
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("explanation_of_yojson: " ^ msg)
  | Failure msg                          -> Error ("explanation_of_yojson: " ^ msg)
