(** Dickinson (2011) eight-stage corporate lifecycle classification.

    Stages are an algebraic data type — invalid stage strings are impossible
    at the OCaml boundary, unlike Python dicts or unchecked string columns. *)

type t =
  | Startup
  | Growth
  | Maturity
  | Shakeout1
  | Shakeout2
  | Shakeout3
  | Decline
  | Decay

let all = [ Startup; Growth; Maturity; Shakeout1; Shakeout2; Shakeout3; Decline; Decay ]

let count = List.length all

let to_string = function
  | Startup   -> "Startup"
  | Growth    -> "Growth"
  | Maturity  -> "Maturity"
  | Shakeout1 -> "Shakeout1"
  | Shakeout2 -> "Shakeout2"
  | Shakeout3 -> "Shakeout3"
  | Decline   -> "Decline"
  | Decay     -> "Decay"

let of_string_opt = function
  | "Startup"   -> Some Startup
  | "Growth"    -> Some Growth
  | "Maturity"  -> Some Maturity
  | "Shakeout1" -> Some Shakeout1
  | "Shakeout2" -> Some Shakeout2
  | "Shakeout3" -> Some Shakeout3
  | "Decline"   -> Some Decline
  | "Decay"     -> Some Decay
  | _           -> None

let of_string s =
  match of_string_opt s with
  | Some stage -> stage
  | None       -> invalid_arg ("Stage.of_string: unknown stage " ^ s)

(** Ordinal index 0–7 for matrix operations. *)
let to_index = function
  | Startup -> 0 | Growth -> 1 | Maturity -> 2
  | Shakeout1 -> 3 | Shakeout2 -> 4 | Shakeout3 -> 5
  | Decline -> 6 | Decay -> 7

let of_index = function
  | 0 -> Startup | 1 -> Growth | 2 -> Maturity
  | 3 -> Shakeout1 | 4 -> Shakeout2 | 5 -> Shakeout3
  | 6 -> Decline | 7 -> Decay
  | n -> invalid_arg (Printf.sprintf "Stage.of_index: out of range %d" n)

(** True if stage represents distress (Shakeout2/3, Decline, Decay). *)
let is_distress = function
  | Shakeout2 | Shakeout3 | Decline | Decay -> true
  | _ -> false

(** True if stage represents early-growth (Startup, Growth). *)
let is_early = function
  | Startup | Growth -> true
  | _ -> false

let equal (a : t) (b : t) = a = b

let compare (a : t) (b : t) = compare (to_index a) (to_index b)

let is_mature = function Maturity -> true | _ -> false

let is_shakeout = function
  | Shakeout1 | Shakeout2 | Shakeout3 -> true
  | _ -> false

(** Broad lifecycle group for display and filtering. *)
let group = function
  | Startup | Growth             -> "early"
  | Maturity                     -> "peak"
  | Shakeout1                    -> "transitional"
  | Shakeout2 | Shakeout3        -> "distress"
  | Decline | Decay              -> "terminal"

(** Next stage in the canonical Dickinson sequence, or None at terminal. *)
let next_opt = function
  | Startup   -> Some Growth
  | Growth    -> Some Maturity
  | Maturity  -> Some Shakeout1
  | Shakeout1 -> Some Shakeout2
  | Shakeout2 -> Some Shakeout3
  | Shakeout3 -> Some Decline
  | Decline   -> Some Decay
  | Decay     -> None

(** Previous stage in the sequence, or None at origin. *)
let prev_opt = function
  | Startup   -> None
  | Growth    -> Some Startup
  | Maturity  -> Some Growth
  | Shakeout1 -> Some Maturity
  | Shakeout2 -> Some Shakeout1
  | Shakeout3 -> Some Shakeout2
  | Decline   -> Some Shakeout3
  | Decay     -> Some Decline

(* ── JSON serialization ──────────────────────────────────────────────────── *)

let to_yojson (s : t) : Yojson.Safe.t = `String (to_string s)

let of_yojson (j : Yojson.Safe.t) : (t, string) result =
  match j with
  | `String s ->
      (match of_string_opt s with
       | Some st -> Ok st
       | None    -> Error ("Stage.of_yojson: unknown stage \"" ^ s ^ "\""))
  | _ -> Error "Stage.of_yojson: expected JSON string"
