package policy.oras_index

# Input structure example:
# {
#   "artifacts": [ {"file": "provenance-foo.json", "mediaType": "application/vnd.slsa.provenance+json", "sha256": "..."}, ...],
#   "meta": {"generatedAt": "...", "schemaVersion": 1},
#   "policy": {"requireSbomMediaTypes": true}
# }
# The workflow may augment the index with meta/policy fields in the future. We allow absence of optional sections.

default allow := true

# Basic shape checks
deny[msg] {
  not input.artifacts
  msg := "oras-index: missing artifacts array"
}

deny[msg] {
  input.artifacts
  not is_array(input.artifacts)
  msg := "oras-index: artifacts is not an array"
}

# Every artifact must have required keys and non-empty strings
deny[msg] {
  some i
  art := input.artifacts[i]
  not art.file
  msg := sprintf("oras-index: artifact %v missing file", [i])
}

deny[msg] {
  some i
  art := input.artifacts[i]
  not art.mediaType
  msg := sprintf("oras-index: artifact %v missing mediaType", [i])
}

deny[msg] {
  some i
  art := input.artifacts[i]
  not art.sha256
  msg := sprintf("oras-index: artifact %v missing sha256", [i])
}

# sha256 must match hex pattern
deny[msg] {
  some i
  art := input.artifacts[i]
  art.sha256
  not re_match("^[0-9a-f]{64}$", art.sha256)
  msg := sprintf("oras-index: artifact %v sha256 invalid format", [i])
}

sbom_requirement_enabled {
  # Optionally the workflow can pass a flag by injecting requireSbomMediaTypes into an outer object; tolerate both top-level and policy subobject
  input.policy.requireSbomMediaTypes == true
} else {
  input.requireSbomMediaTypes == true
}

sbom_cdx_present {
  some i
  input.artifacts[i].mediaType == "application/vnd.cyclonedx+json"
}

sbom_spdx_present {
  some i
  input.artifacts[i].mediaType == "application/spdx+json"
}

# Deny if policy (flag) requires both SBOM types but any missing
deny[msg] {
  sbom_requirement_enabled
  not sbom_cdx_present
  msg := "oras-index: CycloneDX SBOM mediaType missing"
}

deny[msg] {
  sbom_requirement_enabled
  not sbom_spdx_present
  msg := "oras-index: SPDX SBOM mediaType missing"
}

# Optional: ensure at least provenance + attestation present (defense in depth although already enforced elsewhere)
deny[msg] {
  not some i
  input.artifacts[i].mediaType == "application/vnd.slsa.provenance+json"
  msg := "oras-index: provenance mediaType missing"
}

deny[msg] {
  not some i
  input.artifacts[i].mediaType == "application/vnd.in-toto+json"
  msg := "oras-index: in-toto attestation mediaType missing"
}

# No duplicate mediaType+file pairs (likely erroneous duplicates)
deny[msg] {
  some i, j
  i < j
  ai := input.artifacts[i]
  aj := input.artifacts[j]
  ai.file == aj.file
  ai.mediaType == aj.mediaType
  msg := sprintf("oras-index: duplicate artifact file/mediaType combination: %s (%s)", [ai.file, ai.mediaType])
}

# Provide an informational helper rule (not used directly by deny) to list required core media types.
core_media_types := {"application/vnd.slsa.provenance+json", "application/vnd.in-toto+json"}
