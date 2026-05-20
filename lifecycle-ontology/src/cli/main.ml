(** lifecycle-ontology CLI — Phase 6.
    Commands: serve, query, version. *)

open Cmdliner

(* ── version ─────────────────────────────────────────────────────────────── *)

let version_cmd =
  let run () = print_endline Api.version in
  Cmd.v (Cmd.info "version" ~doc:"Print version string")
    Term.(const run $ const ())

(* ── serve ───────────────────────────────────────────────────────────────── *)

let serve_cmd =
  let port =
    let doc = "TCP port to listen on." in
    Arg.(value & opt int 8080 & info ["port"; "p"] ~doc)
  in
  let run port =
    Printf.printf "lifecycle-ontology %s starting on port %d\n%!" Api.version port;
    Dream.run ~port ~interface:"127.0.0.1"
    @@ Dream.logger
    @@ Dream.router [
         Dream.get  "/health"
           (fun _req -> Dream.json (Api.handle_health ()));

         Dream.post "/lifecycle_query"
           (fun req ->
             let%lwt body = Dream.body req in
             Dream.json (Api.handle_lifecycle_query body));

         Dream.post "/explain_stat"
           (fun req ->
             let%lwt body = Dream.body req in
             Dream.json (Api.handle_explain_stat body));

         Dream.post "/scenario_runner"
           (fun req ->
             let%lwt body = Dream.body req in
             Dream.json (Api.handle_scenario_runner body));
       ]
  in
  Cmd.v (Cmd.info "serve" ~doc:"Start the HTTP API server")
    Term.(const run $ port)

(* ── query ───────────────────────────────────────────────────────────────── *)

let query_cmd =
  let level =
    let doc = "Graph level: macro, meso, or micro." in
    Arg.(value & opt string "macro" & info ["level"; "l"] ~doc)
  in
  let persona =
    let doc = "Persona (e.g. CorporateCFO, RatingAnalyst)." in
    Arg.(value & opt string "CorporateCFO" & info ["persona"] ~doc)
  in
  let run level persona =
    let body = Yojson.Safe.to_string (`Assoc [
      "level",      `String level;
      "persona",    `String persona;
      "panel_mode", `String "latest";
    ]) in
    print_endline (Api.handle_lifecycle_query body)
  in
  Cmd.v (Cmd.info "query" ~doc:"Print graph JSON for a given level")
    Term.(const run $ level $ persona)

(* ── main ────────────────────────────────────────────────────────────────── *)

let () =
  let info = Cmd.info "lifecycle-ontology"
    ~version:Api.version
    ~doc:"OCaml semantic + analytics meta-layer for LifeCycle Leverage" in
  exit (Cmd.eval (Cmd.group info [ version_cmd; serve_cmd; query_cmd ]))
