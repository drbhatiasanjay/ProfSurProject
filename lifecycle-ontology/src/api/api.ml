(** HTTP API layer — Phase 6.

    Pure handler functions (JSON string → JSON string) that Dream wires up in
    cli/main.ml.  Keeping handlers pure lets test_api.ml call them directly
    without starting a server. *)

open Domain

let version = "0.2.0-phase6-http"

(* ── Request parsing helpers ─────────────────────────────────────────────── *)

let member_str j key =
  match Yojson.Safe.Util.(j |> member key) with
  | `String s -> Ok s
  | `Null     -> Error (key ^ " is null")
  | _         -> Error (key ^ ": expected string")

let member_float_opt j key =
  match Yojson.Safe.Util.(j |> member key) with
  | `Float f  -> Some f
  | `Int i    -> Some (float_of_int i)
  | _         -> None

let member_list j key =
  match Yojson.Safe.Util.(j |> member key) with
  | `List l -> l
  | _       -> []

let ok_response body = body
let err_response msg =
  Yojson.Safe.to_string (`Assoc ["error", `String msg])

(* ── /lifecycle_query ────────────────────────────────────────────────────── *)

(** Parse a stage string with a clear error. *)
let parse_stage s =
  match Stage.of_string_opt s with
  | Some st -> Ok st
  | None    -> Error ("unknown stage: " ^ s)

let parse_event s =
  match Period.event_of_string_opt s with
  | Some ev -> Ok ev
  | None    -> Error ("unknown event: " ^ s)

let parse_company_tuple j =
  (* ["code", "name", "stage", "industry", leverage] *)
  match j with
  | `List [`String code; `String name; `String stage_s; `String ind; lev_j] ->
      let lev = match lev_j with
                | `Float f -> f | `Int i -> float_of_int i | _ -> 0.0 in
      (match parse_stage stage_s with
       | Ok st -> Ok (code, name, st, ind, lev)
       | Error e -> Error e)
  | _ -> Error "company tuple must be [code, name, stage, industry, leverage]"

let parse_peer_tuple j =
  (* ["code", "name", "stage", leverage, similarity] *)
  match j with
  | `List [`String code; `String name; `String stage_s; lev_j; sim_j] ->
      let lev = match lev_j with `Float f -> f | `Int i -> float_of_int i | _ -> 0.0 in
      let sim = match sim_j with `Float f -> f | `Int i -> float_of_int i | _ -> 0.0 in
      (match parse_stage stage_s with
       | Ok st -> Ok (code, name, st, lev, sim)
       | Error e -> Error e)
  | _ -> Error "peer tuple must be [code, name, stage, leverage, similarity]"

let parse_si_count j =
  (* ["stage", "industry", count] *)
  match j with
  | `List [`String st_s; `String ind; cnt_j] ->
      let cnt = match cnt_j with `Int n -> n | `Float f -> int_of_float f | _ -> 0 in
      (match parse_stage st_s with
       | Ok st -> Ok (st, ind, cnt)
       | Error e -> Error e)
  | _ -> Error "si_count must be [stage, industry, count]"

let parse_transition j =
  (* ["from_stage", "to_stage", prob] *)
  match j with
  | `List [`String fs; `String ts; prob_j] ->
      let prob = match prob_j with `Float f -> f | `Int i -> float_of_int i | _ -> 0.0 in
      (match parse_stage fs, parse_stage ts with
       | Ok f, Ok t -> Ok (f, t, prob)
       | Error e, _ | _, Error e -> Error e)
  | _ -> Error "transition must be [from_stage, to_stage, prob]"

let parse_crisis j =
  (* ["event", ["stage1", ...]] *)
  match j with
  | `List [`String ev_s; `List stages_j] ->
      (match parse_event ev_s with
       | Error e -> Error e
       | Ok ev ->
           let stages_r = List.map (function
             | `String s -> parse_stage s
             | _         -> Error "stage must be a string") stages_j in
           let errs = List.filter_map (function Error e -> Some e | Ok _ -> None) stages_r in
           if errs <> [] then Error (List.hd errs)
           else Ok (ev, List.filter_map (function Ok s -> Some s | _ -> None) stages_r))
  | _ -> Error "crisis must be [event, [stage_list]]"

let handle_lifecycle_query (body : string) : string =
  match (try Ok (Yojson.Safe.from_string body)
         with Yojson.Json_error msg -> Error msg) with
  | Error msg -> err_response ("JSON parse error: " ^ msg)
  | Ok j ->
      let level_s   = Result.value (member_str j "level") ~default:"macro" in
      let persona   = match member_str j "persona" with
                      | Ok s -> (match Persona.of_string_opt s with
                                 | Some p -> p | None -> Persona.CorporateCFO)
                      | Error _ -> Persona.CorporateCFO in
      let panel     = Result.value (member_str j "panel_mode") ~default:"latest" in
      let graph = match level_s with
        | "macro" ->
            let si = List.filter_map (fun x ->
              match parse_si_count x with Ok v -> Some v | _ -> None)
              (member_list j "stage_industry_counts") in
            let tr = List.filter_map (fun x ->
              match parse_transition x with Ok v -> Some v | _ -> None)
              (member_list j "stage_transitions") in
            let cr = List.filter_map (fun x ->
              match parse_crisis x with Ok v -> Some v | _ -> None)
              (member_list j "crisis_stages") in
            Graph_export.build_macro
              ~stage_industry_counts:si
              ~stage_transitions:tr
              ~crisis_stages:cr ()
        | "meso" ->
            let companies = List.filter_map (fun x ->
              match parse_company_tuple x with Ok v -> Some v | _ -> None)
              (member_list j "companies") in
            Graph_export.build_meso ~companies ()
        | "micro" ->
            let fc   = Result.value (member_str j "focal_code") ~default:"UNKNOWN" in
            let fn   = Result.value (member_str j "focal_name") ~default:"Unknown" in
            let fs   = (match member_str j "focal_stage" with
                        | Ok s -> (match parse_stage s with Ok st -> st | _ -> Stage.Maturity)
                        | _ -> Stage.Maturity) in
            let flev = Option.value (member_float_opt j "focal_leverage") ~default:0.0 in
            let peers = List.filter_map (fun x ->
              match parse_peer_tuple x with Ok v -> Some v | _ -> None)
              (member_list j "peers") in
            let evts = List.filter_map (function
              | `String s -> (match parse_event s with Ok ev -> Some ev | _ -> None)
              | _ -> None)
              (member_list j "crisis_events") in
            Graph_export.build_micro
              ~focal_code:fc ~focal_name:fn
              ~focal_stage:fs ~focal_leverage:flev
              ~peers ~crisis_events:evts ()
        | other ->
            (* fallback — return empty macro *)
            let _ = other in
            Graph_export.build_macro
              ~stage_industry_counts:[] ~stage_transitions:[] ~crisis_stages:[] ()
      in
      ok_response
        (Yojson.Safe.to_string
          (Graph_export.graph_to_yojson ~persona ~panel_mode:panel graph))

(* ── /explain_stat ───────────────────────────────────────────────────────── *)

let handle_explain_stat (body : string) : string =
  match (try Ok (Yojson.Safe.from_string body)
         with Yojson.Json_error msg -> Error msg) with
  | Error msg -> err_response ("JSON parse error: " ^ msg)
  | Ok j ->
      let stat_id   = Result.value (member_str j "stat_id")  ~default:"leverage_ratio" in
      let persona   = match member_str j "persona" with
                      | Ok s -> Option.value (Persona.of_string_opt s) ~default:Persona.CorporateCFO
                      | _    -> Persona.CorporateCFO in
      let stage     = match member_str j "stage" with
                      | Ok s -> (match Stage.of_string_opt s with Some st -> st | None -> Stage.Maturity)
                      | _    -> Stage.Maturity in
      let value     = Option.value (member_float_opt j "value") ~default:0.0 in
      let industry  = Result.value (member_str j "industry") ~default:"All" in
      let metric    = Option.value (Metric.find_opt stat_id) ~default:Metric.leverage_ratio in
      let band : Analytics_meta.normative_band = {
        nb_id = "explain_" ^ stat_id; stage; industry;
        metric; lower = 0.0; upper = 1.0; source_vintage = "dynamic";
      } in
      let result = Normative.evaluate band ~value in
      let tone   = Persona.explanation_tone persona in
      let resp = `Assoc [
        "stat_id",     `String stat_id;
        "persona",     `String (Persona.to_string persona);
        "tone",        `String tone;
        "explanation", `String result.explanation;
        "flag",        `String (Normative.flag_to_string result.flag);
        "anomaly_score", `Float result.anomaly_score;
      ] in
      ok_response (Yojson.Safe.to_string resp)

(* ── /scenario_runner ────────────────────────────────────────────────────── *)

let handle_scenario_runner (body : string) : string =
  match (try Ok (Yojson.Safe.from_string body)
         with Yojson.Json_error msg -> Error msg) with
  | Error msg -> err_response ("JSON parse error: " ^ msg)
  | Ok j ->
      match Scenario.of_yojson j with
      | Error msg -> err_response ("scenario parse error: " ^ msg)
      | Ok sc ->
          let baseline =
            match Yojson.Safe.Util.(j |> member "baseline") with
            | `Assoc pairs ->
                List.filter_map (fun (k, v) ->
                  match v with
                  | `Float f -> Some (k, f)
                  | `Int i   -> Some (k, float_of_int i)
                  | _        -> None) pairs
            | _ -> [] in
          let results    = Scenario.apply sc ~baseline_map:baseline in
          let is_stress  = Scenario.is_stress_scenario sc in
          let magnitude  = Scenario.total_shock_magnitude sc in
          let resp = `Assoc [
            "scenario_id",     `String sc.id;
            "persona",         Persona.to_yojson sc.persona;
            "stage",           Stage.to_yojson sc.stage;
            "is_stress",       `Bool is_stress;
            "total_magnitude", `Float magnitude;
            "shock_results",   `List (List.map Scenario.shock_result_to_yojson results);
          ] in
          ok_response (Yojson.Safe.to_string resp)

(* ── Health check ────────────────────────────────────────────────────────── *)

let handle_health () : string =
  Yojson.Safe.to_string
    (`Assoc ["status", `String "ok"; "version", `String version])
