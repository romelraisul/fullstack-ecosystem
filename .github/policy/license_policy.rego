package policy

# License blocklist policy. Expects input JSON structured as:
# { "licenses": ["MIT", "GPL-3.0-only", ...] }
# Blocklist passed via env var LICENSE_BLOCKLIST (comma separated), or defaults empty.

licenses := input.licenses
blocklist_raw := lower(env.LICENSE_BLOCKLIST)
blocklist := {trim(x) | x := split(blocklist_raw, ",")[_]; trim(x) != ""}

violation[msg] {
  some i
  lic := lower(licenses[i])
  lic != ""
  lic_blocked := blocklist[_]
  lic == lic_blocked
  msg := sprintf("blocked license detected: %s", [lic])
}

deny[msg] { violation[msg] }
