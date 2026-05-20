(** Financial period representation.

    Each period has explicit basis (Standalone/Consolidated), kind
    (Annual/Quarterly/TTM), fiscal year, optional quarter, and flags
    for overlapping crisis events (GFC/IBC/COVID). *)

type basis = Standalone | Consolidated

type kind = Annual | Quarterly | Ttm

type event = GFC | IBC | COVID

type t = {
  id          : string;         (** e.g. "FY2024-SA" *)
  kind        : kind;
  fiscal_year : int;
  quarter     : int option;     (** None for annual/TTM *)
  basis       : basis;
  events      : event list;     (** crisis events overlapping this period *)
}

let basis_to_string = function
  | Standalone   -> "Standalone"
  | Consolidated -> "Consolidated"

let basis_of_string_opt = function
  | "Standalone" | "SA"  -> Some Standalone
  | "Consolidated" | "CS" -> Some Consolidated
  | _ -> None

let kind_to_string = function
  | Annual    -> "Annual"
  | Quarterly -> "Quarterly"
  | Ttm       -> "TTM"

let event_to_string = function
  | GFC   -> "GFC"
  | IBC   -> "IBC"
  | COVID -> "COVID"

let event_of_string_opt = function
  | "GFC"   -> Some GFC
  | "IBC"   -> Some IBC
  | "COVID" -> Some COVID
  | _       -> None

let make ~fiscal_year ?(quarter = None) ?(basis = Standalone)
    ?(kind = Annual) ?(events = []) () =
  let q_part = match quarter with Some q -> Printf.sprintf "Q%d-" q | None -> "" in
  let basis_abbr = match basis with Standalone -> "SA" | Consolidated -> "CS" in
  let id = Printf.sprintf "FY%d-%s%s-%s"
    fiscal_year q_part (kind_to_string kind) basis_abbr in
  { id; kind; fiscal_year; quarter; basis; events }

let is_crisis_period t = t.events <> []

let has_event t ev = List.mem ev t.events

let contains_gfc   t = has_event t GFC
let contains_ibc   t = has_event t IBC
let contains_covid t = has_event t COVID

let to_label t =
  Printf.sprintf "FY%d%s (%s)" t.fiscal_year
    (match t.quarter with Some q -> Printf.sprintf " Q%d" q | None -> "")
    (basis_to_string t.basis)

(** Validate a period, returning Error with a description on failure. *)
let validate t =
  if t.fiscal_year < 1980 || t.fiscal_year > 2030 then
    Error (Printf.sprintf "fiscal_year %d out of range [1980, 2030]" t.fiscal_year)
  else
    match t.quarter with
    | Some q when q < 1 || q > 4 ->
        Error (Printf.sprintf "quarter %d out of range [1, 4]" q)
    | _ ->
        let uniq = List.sort_uniq compare t.events in
        if List.length uniq <> List.length t.events then
          Error "duplicate events in period"
        else Ok t

(** Like [make] but validates the result; returns [Error] on invalid inputs. *)
let make_validated ~fiscal_year ?(quarter = None) ?(basis = Standalone)
    ?(kind = Annual) ?(events = []) () =
  let t = make ~fiscal_year ~quarter ~basis ~kind ~events () in
  validate t

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let event_to_yojson ev : Yojson.Safe.t = `String (event_to_string ev)

let event_of_yojson j : (event, string) result =
  match j with
  | `String s ->
      (match event_of_string_opt s with
       | Some ev -> Ok ev
       | None    -> Error ("Period.event_of_yojson: unknown event \"" ^ s ^ "\""))
  | _ -> Error "Period.event_of_yojson: expected JSON string"

let basis_to_yojson b : Yojson.Safe.t = `String (basis_to_string b)

let basis_of_yojson j : (basis, string) result =
  match j with
  | `String s ->
      (match basis_of_string_opt s with
       | Some b -> Ok b
       | None   -> Error ("Period.basis_of_yojson: unknown basis \"" ^ s ^ "\""))
  | _ -> Error "Period.basis_of_yojson: expected JSON string"

let kind_to_yojson k : Yojson.Safe.t = `String (kind_to_string k)

let kind_of_yojson j : (kind, string) result =
  match j with
  | `String "Annual"    -> Ok Annual
  | `String "Quarterly" -> Ok Quarterly
  | `String "TTM"       -> Ok Ttm
  | `String s           -> Error ("Period.kind_of_yojson: unknown kind \"" ^ s ^ "\"")
  | _                   -> Error "Period.kind_of_yojson: expected JSON string"

let to_yojson (t : t) : Yojson.Safe.t =
  `Assoc [
    "id",          `String t.id;
    "kind",        kind_to_yojson t.kind;
    "fiscal_year", `Int t.fiscal_year;
    "quarter",     (match t.quarter with Some q -> `Int q | None -> `Null);
    "basis",       basis_to_yojson t.basis;
    "events",      `List (List.map event_to_yojson t.events);
  ]

let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  let open Yojson.Safe.Util in
  try
    let fiscal_year = j |> member "fiscal_year" |> to_int in
    let kind        = match kind_of_yojson (j |> member "kind") with
                      | Ok k -> k | Error e -> failwith e in
    let basis       = match basis_of_yojson (j |> member "basis") with
                      | Ok b -> b | Error e -> failwith e in
    let quarter     = match j |> member "quarter" with
                      | `Int q -> Some q | `Null -> None
                      | _ -> failwith "quarter: expected int or null" in
    let events_j    = j |> member "events" |> to_list in
    let events      = List.map (fun ej ->
      match event_of_yojson ej with
      | Ok ev -> ev | Error e -> failwith e) events_j in
    Ok (make ~fiscal_year ~quarter ~basis ~kind ~events ())
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("Period.of_yojson: " ^ msg)
  | Failure msg                          -> Error ("Period.of_yojson: " ^ msg)
