package policy.attestation

deny[msg] {
  input._type != "https://in-toto.io/Statement/v0.1"
  msg := "Attestation _type invalid"
}

deny[msg] {
  input.predicateType != "https://slsa.dev/provenance/v1"
  msg := "Attestation predicateType must be SLSA v1"
}

deny[msg] {
  count(input.subject) == 0
  msg := "Attestation must contain at least one subject"
}

deny[msg] {
  some s
  subject := input.subject[s]
  not subject.digest.sha256
  msg := sprintf("Subject %v missing sha256 digest", [subject.name])
}

deny[msg] {
  not input.predicate.buildDefinition
  msg := "Missing buildDefinition in predicate"
}

deny[msg] {
  not input.predicate.runDetails
  msg := "Missing runDetails in predicate"
}

deny[msg] {
  not input.predicate.runDetails.metadata.startedOn
  msg := "Missing runDetails.metadata.startedOn"
}

deny[msg] {
  not input.predicate.runDetails.metadata.finishedOn
  msg := "Missing runDetails.metadata.finishedOn"
}

# Ensure required byproducts exist for reproducibility context
required_byproducts := {"trivy_version", "grype_version", "buildx_version", "docker_version"}

deny[msg] {
  some rb
  rb_name := required_byproducts[rb]
  not some i
  input.predicate.runDetails.byproducts[i].name == rb_name
  msg := sprintf("Missing required byproduct %v", [rb_name])
}

# Example warning (not enforced as deny) for empty resolvedDependencies
warn[msg] {
  count(input.predicate.buildDefinition.resolvedDependencies) == 0
  msg := "No resolvedDependencies listed (consider capturing inputs explicitly)"
}

deny[msg] {
  count(input.predicate.buildDefinition.resolvedDependencies) == 0
  msg := "Must include at least one resolvedDependency (dockerfile/base image/lockfile)"
}

# Enforce materials pattern: at least 1 dockerfile material and >=1 base-image material
deny[msg] {
  not input.predicate.materials
  msg := "Missing materials array"
}

deny[msg] {
  input.predicate.materials
  count([m | m := input.predicate.materials[_]; m.name == "dockerfile"]) == 0
  msg := "Materials must include dockerfile entry"
}

deny[msg] {
  input.predicate.materials
  count([m | m := input.predicate.materials[_]; m.name == "base-image"]) == 0
  msg := "Materials must include at least one base-image entry"
}

# Reproducibility mismatch enforcement: if a byproduct reproducibility_match is present and explicitly 'false'
# deny. Upstream workflow already optionally enforces; this gives policy visibility.
deny[msg] {
  some i
  bp := input.predicate.runDetails.byproducts[i]
  bp.name == "reproducibility_match"
  bp.value == "false"
  msg := "Reproducibility mismatch: reproducibility_match=false"
}
