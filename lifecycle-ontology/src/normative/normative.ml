(** Normative band evaluation — Phase 4.

    Bands are [lower, upper] intervals for a metric × stage × industry triple,
    derived from conformalized quantile regression on the thesis panel.
    This module handles *evaluation* (checking a value against a band);
    band *fitting* lives in the Python analytics layer. *)

open Domain

(* ── Anomaly flag ────────────────────────────────────────────────────────── *)

type flag = Within | OverLevered | UnderLevered

let flag_of_value ~lower ~upper value =
  if value > upper then OverLevered
  else if value < lower then UnderLevered
  else Within

let flag_to_string = function
  | Within       -> "within"
  | OverLevered  -> "over-levered"
  | UnderLevered -> "under-levered"

let flag_of_string_opt = function
  | "within"        -> Some Within
  | "over-levered"  -> Some OverLevered
  | "under-levered" -> Some UnderLevered
  | _               -> None

let check_band (band : Analytics_meta.normative_band) ~value : flag =
  flag_of_value ~lower:band.lower ~upper:band.upper value

(* ── Band geometry ───────────────────────────────────────────────────────── *)

let band_width (band : Analytics_meta.normative_band) =
  band.upper -. band.lower

let band_midpoint (band : Analytics_meta.normative_band) =
  (band.lower +. band.upper) /. 2.0

(** Percentile rank of [value] within [band], clamped to [0, 1].
    0.0 = at lower bound; 1.0 = at upper bound; outside range possible. *)
let percentile_rank (band : Analytics_meta.normative_band) ~value =
  let w = band_width band in
  if w <= 0.0 then 0.5
  else (value -. band.lower) /. w

(* ── Anomaly score ───────────────────────────────────────────────────────── *)

(** Normalised distance outside the band.
    Returns 0.0 when within; positive when outside.
    Normalised by band_width so score 1.0 = one full band-width outside. *)
let anomaly_score (band : Analytics_meta.normative_band) ~value =
  let w = band_width band in
  if w <= 0.0 then 0.0
  else if value > band.upper then (value -. band.upper) /. w
  else if value < band.lower then (band.lower -. value) /. w
  else 0.0

(* ── Human-readable explanation ──────────────────────────────────────────── *)

let explain_flag (band : Analytics_meta.normative_band) flag =
  let mn = band.metric.id in
  let st = Stage.to_string band.stage in
  match flag with
  | Within ->
      Printf.sprintf "%s is within normative band [%.3f, %.3f] for %s stage"
        mn band.lower band.upper st
  | OverLevered ->
      Printf.sprintf
        "%s exceeds upper bound %.3f for %s stage — potential over-leverage"
        mn band.upper st
  | UnderLevered ->
      Printf.sprintf
        "%s is below lower bound %.3f for %s stage — under-levered relative to peers"
        mn band.lower st

(* ── Normative result ────────────────────────────────────────────────────── *)

type normative_result = {
  band          : Analytics_meta.normative_band;
  value         : float;
  flag          : flag;
  anomaly_score : float;
  explanation   : string;
}

let evaluate (band : Analytics_meta.normative_band) ~value : normative_result =
  let flag = check_band band ~value in
  { band;
    value;
    flag;
    anomaly_score = anomaly_score band ~value;
    explanation   = explain_flag band flag }

(** Evaluate a list of (band, value) pairs in one pass. *)
let batch_evaluate pairs =
  List.map (fun (band, value) -> evaluate band ~value) pairs

(** Count results by flag. Returns (n_within, n_over, n_under). *)
let count_flags results =
  List.fold_left (fun (w, o, u) r ->
    match r.flag with
    | Within       -> (w + 1, o,     u    )
    | OverLevered  -> (w,     o + 1, u    )
    | UnderLevered -> (w,     o,     u + 1)
  ) (0, 0, 0) results

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let flag_to_yojson f : Yojson.Safe.t = `String (flag_to_string f)

let flag_of_yojson j : (flag, string) result =
  match j with
  | `String s ->
      (match flag_of_string_opt s with
       | Some f -> Ok f
       | None   -> Error ("flag_of_yojson: unknown flag \"" ^ s ^ "\""))
  | _ -> Error "flag_of_yojson: expected JSON string"

let normative_result_to_yojson (r : normative_result) : Yojson.Safe.t =
  `Assoc [
    "nb_id",         `String r.band.nb_id;
    "stage",         Stage.to_yojson r.band.stage;
    "metric_id",     `String r.band.metric.id;
    "value",         `Float  r.value;
    "flag",          flag_to_yojson r.flag;
    "anomaly_score", `Float  r.anomaly_score;
    "explanation",   `String r.explanation;
  ]
