(** Financial metric definitions.

    Key invariant: leverage always refers to the thesis-consistent decimal
    ratio (lev1100 = total_borrowings / total_assets), never a percentage. *)

type unit_kind =
  | Ratio           (** dimensionless, e.g. leverage = 0.35 *)
  | Percent         (** 0–100, e.g. interest rate = 8.5 *)
  | CurrencyInrCr   (** INR crore *)
  | Count           (** integer count *)
  | Years           (** duration *)

type statement_type = [ `Pnl | `BalanceSheet | `CashFlow | `Derived ]

type t = {
  id             : string;            (** canonical ID, e.g. "leverage_ratio" *)
  name           : string;            (** display name *)
  statement_type : statement_type;
  unit           : unit_kind;
  is_derived     : bool;
}

(* ── Canonical metric catalogue ─────────────────────────────────────────── *)

let leverage_ratio = {
  id = "leverage_ratio"; name = "Leverage (lev1100)";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let profitability = {
  id = "profitability"; name = "Profitability (EBIT/Assets)";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let tangibility = {
  id = "tangibility"; name = "Tangibility (NFA/Assets)";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let firm_size = {
  id = "firm_size"; name = "Firm Size (log Assets)";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let non_debt_tax_shield = {
  id = "tax_shield"; name = "Non-Debt Tax Shield";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let liquidity = {
  id = "liquidity"; name = "Cash Holdings / Assets";
  statement_type = `Derived; unit = Ratio; is_derived = true;
}

let catalogue = [
  leverage_ratio; profitability; tangibility; firm_size;
  non_debt_tax_shield; liquidity;
]

let find_opt id = List.find_opt (fun m -> m.id = id) catalogue

let unit_to_string = function
  | Ratio         -> "ratio"
  | Percent       -> "%"
  | CurrencyInrCr -> "INR Cr"
  | Count         -> "count"
  | Years         -> "years"

(** Smart constructor — raises [Invalid_argument] on blank id or name. *)
let make ~id ~name ~statement_type ~unit ~is_derived () =
  if String.trim id   = "" then invalid_arg "Metric.make: id must not be empty"
  else if String.trim name = "" then invalid_arg "Metric.make: name must not be empty"
  else { id; name; statement_type; unit; is_derived }

(** Plausible value range for each catalogue metric (ratio scale). *)
let value_range m = match m.id with
  | "leverage_ratio" -> Some (-0.1, 2.0)
  | "profitability"  -> Some (-5.0, 5.0)
  | "tangibility"    -> Some ( 0.0, 1.0)
  | "firm_size"      -> Some ( 0.0, 30.0)
  | "tax_shield"     -> Some ( 0.0, 1.0)
  | "liquidity"      -> Some ( 0.0, 1.0)
  | _                -> None

(** Check whether [v] is within the plausible range for [metric].
    Returns [Ok v] when valid, or [Error] with a description. *)
let validate_value metric v =
  match value_range metric with
  | None -> Ok v
  | Some (lo, hi) ->
      if v < lo then
        Error (Printf.sprintf "%s value %.4f below minimum %.4f" metric.id v lo)
      else if v > hi then
        Error (Printf.sprintf "%s value %.4f above maximum %.4f" metric.id v hi)
      else Ok v

(** Broad group for display grouping. *)
let group m = match m.id with
  | "leverage_ratio"                                        -> "leverage"
  | "profitability"                                         -> "profitability"
  | "tangibility" | "firm_size" | "tax_shield" | "liquidity" -> "asset_structure"
  | _                                                       -> "other"

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let unit_to_yojson u : Yojson.Safe.t = `String (unit_to_string u)

let unit_of_yojson j : (unit_kind, string) result =
  match j with
  | `String "ratio"   -> Ok Ratio
  | `String "%"       -> Ok Percent
  | `String "INR Cr"  -> Ok CurrencyInrCr
  | `String "count"   -> Ok Count
  | `String "years"   -> Ok Years
  | `String s         -> Error ("Metric.unit_of_yojson: unknown unit \"" ^ s ^ "\"")
  | _                 -> Error "Metric.unit_of_yojson: expected JSON string"

let statement_type_to_yojson (st : statement_type) : Yojson.Safe.t =
  match st with
  | `Pnl          -> `String "pnl"
  | `BalanceSheet -> `String "balance_sheet"
  | `CashFlow     -> `String "cash_flow"
  | `Derived      -> `String "derived"

let statement_type_of_yojson j : (statement_type, string) result =
  match j with
  | `String "pnl"           -> Ok `Pnl
  | `String "balance_sheet" -> Ok `BalanceSheet
  | `String "cash_flow"     -> Ok `CashFlow
  | `String "derived"       -> Ok `Derived
  | `String s               -> Error ("unknown statement_type: " ^ s)
  | _                       -> Error "expected JSON string for statement_type"

(** Serialise a metric as a full object (suitable for catalogue export). *)
let to_yojson (m : t) : Yojson.Safe.t =
  `Assoc [
    "id",             `String m.id;
    "name",           `String m.name;
    "statement_type", statement_type_to_yojson m.statement_type;
    "unit",           unit_to_yojson m.unit;
    "is_derived",     `Bool m.is_derived;
  ]

(** Deserialise from a full object, OR fall back to catalogue lookup by [id]
    string (enables compact embedding as just [{"id":"leverage_ratio"}]). *)
let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  let open Yojson.Safe.Util in
  match j with
  | `String _ | `Assoc _ ->
      let id_str = (match j with
        | `String s -> s
        | _ -> j |> member "id" |> to_string) in
      (match find_opt id_str with
       | Some m -> Ok m
       | None   ->
           (* build from full object when not in catalogue *)
           (try
             let name = j |> member "name" |> to_string in
             let st   = match statement_type_of_yojson (j |> member "statement_type") with
                        | Ok s -> s | Error e -> failwith e in
             let u    = match unit_of_yojson (j |> member "unit") with
                        | Ok u -> u | Error e -> failwith e in
             let d    = j |> member "is_derived" |> to_bool in
             Ok { id = id_str; name; statement_type = st; unit = u; is_derived = d }
           with
           | Yojson.Safe.Util.Type_error (msg, _) -> Error ("Metric.of_yojson: " ^ msg)
           | Failure msg                          -> Error ("Metric.of_yojson: " ^ msg)))
  | _ -> Error "Metric.of_yojson: expected JSON string or object"
