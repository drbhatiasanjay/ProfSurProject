(** Stakeholder personas driving UX, explanation tone, and default KPIs. *)

type t =
  | RatingAnalyst
  | CorporateCFO
  | VentureDebtInvestor
  | PEVCInvestor
  | FacultyPhDSupervisor
  | RegulatorPolicyAnalyst

let all = [
  RatingAnalyst; CorporateCFO; VentureDebtInvestor;
  PEVCInvestor; FacultyPhDSupervisor; RegulatorPolicyAnalyst;
]

let to_string = function
  | RatingAnalyst         -> "RatingAnalyst"
  | CorporateCFO          -> "CorporateCFO"
  | VentureDebtInvestor   -> "VentureDebtInvestor"
  | PEVCInvestor          -> "PEVCInvestor"
  | FacultyPhDSupervisor  -> "FacultyPhDSupervisor"
  | RegulatorPolicyAnalyst -> "RegulatorPolicyAnalyst"

let of_string_opt = function
  | "RatingAnalyst"          -> Some RatingAnalyst
  | "CorporateCFO"           -> Some CorporateCFO
  | "VentureDebtInvestor"    -> Some VentureDebtInvestor
  | "PEVCInvestor"           -> Some PEVCInvestor
  | "FacultyPhDSupervisor"   -> Some FacultyPhDSupervisor
  | "RegulatorPolicyAnalyst" -> Some RegulatorPolicyAnalyst
  | _ -> None

let of_string s =
  match of_string_opt s with
  | Some p -> p
  | None   -> invalid_arg ("Persona.of_string: unknown persona " ^ s)

let equal (a : t) (b : t) = a = b

(** Horizon in years for this persona's default view. *)
let default_horizon = function
  | RatingAnalyst          -> 1
  | CorporateCFO           -> 3
  | VentureDebtInvestor    -> 2
  | PEVCInvestor           -> 5
  | FacultyPhDSupervisor   -> 10
  | RegulatorPolicyAnalyst -> 5

(** Human-readable display label. *)
let display_name = function
  | RatingAnalyst          -> "Rating Analyst"
  | CorporateCFO           -> "Corporate CFO"
  | VentureDebtInvestor    -> "Venture Debt Investor"
  | PEVCInvestor           -> "PE/VC Investor"
  | FacultyPhDSupervisor   -> "Faculty / PhD Supervisor"
  | RegulatorPolicyAnalyst -> "Regulator / Policy Analyst"

(** Canonical metric IDs this persona prioritises (order matters for display). *)
let key_metric_ids = function
  | RatingAnalyst          -> ["leverage_ratio"; "liquidity"; "profitability"]
  | CorporateCFO           -> ["leverage_ratio"; "profitability"; "firm_size"]
  | VentureDebtInvestor    -> ["leverage_ratio"; "profitability"; "tangibility"]
  | PEVCInvestor           -> ["profitability"; "firm_size"; "tangibility"]
  | FacultyPhDSupervisor   -> ["leverage_ratio"; "profitability"; "tangibility";
                               "firm_size"; "tax_shield"; "liquidity"]
  | RegulatorPolicyAnalyst -> ["leverage_ratio"; "profitability"; "liquidity"]

(** Explanation tone tag used by the DSPy explanation layer. *)
let explanation_tone = function
  | RatingAnalyst          -> "credit-focused"
  | CorporateCFO           -> "strategic"
  | VentureDebtInvestor    -> "risk-return"
  | PEVCInvestor           -> "growth-oriented"
  | FacultyPhDSupervisor   -> "academic"
  | RegulatorPolicyAnalyst -> "systemic-risk"

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let to_yojson (p : t) : Yojson.Safe.t = `String (to_string p)

let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  match j with
  | `String s ->
      (match of_string_opt s with
       | Some p -> Ok p
       | None   -> Error ("Persona.of_yojson: unknown persona \"" ^ s ^ "\""))
  | _ -> Error "Persona.of_yojson: expected JSON string"
