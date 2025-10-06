package policy.provenance

# Minimal structural checks for provenance JSON (pre-SLSA custom format)
# Adjust these rules if provenance schema evolves.

deny[msg] {
  not input.image_slug
  msg := "Provenance missing image_slug"
}

deny[msg] {
  not input.commit
  msg := "Provenance missing commit field"
}

deny[msg] {
  not input.build_command
  msg := "Provenance missing build_command"
}

# Require at least one SBOM reference

deny[msg] {
  not input.sbom.cyclonedx
  msg := "Provenance missing CycloneDX SBOM reference"
}

deny[msg] {
  not input.sbom.spdx
  msg := "Provenance missing SPDX SBOM reference"
}

# If diff present ensure meta counts exist

deny[msg] {
  input.sbom_diff
  not input.sbom_diff.meta
  msg := "SBOM diff metadata missing"
}
