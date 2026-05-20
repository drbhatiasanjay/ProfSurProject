(** Company entity. Numeric panel data stays in SQLite; OCaml holds the
    identity and classification attributes used for graph and ontology logic. *)

type t = {
  code      : string;           (** companycode from CMIE *)
  name      : string;
  industry  : string;           (** NIC industry group *)
  listing   : string option;    (** "NSE" | "BSE" | "NSE,BSE" | None *)
  ipo_year  : int option;
}

let make ~code ~name ~industry ?(listing = None) ?(ipo_year = None) () =
  { code; name; industry; listing; ipo_year }

(** Smart constructor — returns [Error] when required fields are blank. *)
let make_validated ~code ~name ~industry ?(listing = None) ?(ipo_year = None) () =
  if String.trim code     = "" then Error "company code must not be empty"
  else if String.trim name     = "" then Error "company name must not be empty"
  else if String.trim industry = "" then Error "industry must not be empty"
  else Ok (make ~code ~name ~industry ~listing ~ipo_year ())

let is_listed t = t.listing <> None

let to_label t =
  Printf.sprintf "%s (%s)" t.name t.industry

let equal a b = String.equal a.code b.code

let compare a b = String.compare a.code b.code

(** Split comma-separated listing string into individual exchange names. *)
let exchange_list t =
  match t.listing with
  | None   -> []
  | Some s ->
      String.split_on_char ',' s
      |> List.map String.trim
      |> List.filter (fun x -> x <> "")

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let to_yojson (t : t) : Yojson.Safe.t =
  `Assoc [
    "code",      `String t.code;
    "name",      `String t.name;
    "industry",  `String t.industry;
    "listing",   (match t.listing  with Some s -> `String s | None -> `Null);
    "ipo_year",  (match t.ipo_year with Some y -> `Int y    | None -> `Null);
  ]

let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  let open Yojson.Safe.Util in
  try
    let code     = j |> member "code"     |> to_string in
    let name     = j |> member "name"     |> to_string in
    let industry = j |> member "industry" |> to_string in
    let listing  = match j |> member "listing" with
                   | `String s -> Some s | `Null -> None
                   | _ -> failwith "listing: expected string or null" in
    let ipo_year = match j |> member "ipo_year" with
                   | `Int y -> Some y | `Null -> None
                   | _ -> failwith "ipo_year: expected int or null" in
    Ok { code; name; industry; listing; ipo_year }
  with
  | Yojson.Safe.Util.Type_error (msg, _) -> Error ("Company.of_yojson: " ^ msg)
  | Failure msg                          -> Error ("Company.of_yojson: " ^ msg)
