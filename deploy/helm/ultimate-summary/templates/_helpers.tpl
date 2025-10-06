{{- define "ultimate-summary.name" -}}
{{ include "ultimate-summary.chart" . }}
{{- end -}}

{{- define "ultimate-summary.fullname" -}}
{{ .Release.Name | default "ultimate-summary" }}
{{- end -}}

{{- define "ultimate-summary.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}
