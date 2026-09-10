# Reviewer hook policy

If Gemini CLI hooks are enabled, they may perform read-only checks only:

- confirm repository root and expected branch;
- confirm the requested candidate SHA exists;
- reject writes outside a designated temporary evidence directory;
- scan proposed evidence for credentials;
- report the final command and exit status.

Hooks must not delete files, alter credentials, stage changes, commit, push,
deploy, or silently broaden the reviewer scope. The API adapter performs its own
equivalent checks and does not rely on these hooks.
