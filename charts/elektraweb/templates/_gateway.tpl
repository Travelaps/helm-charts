{{- define "elektraweb.gatewayServices" -}}
{{- $services := list -}}
{{- $services = append $services (dict "name" "worker" "config" .Values.worker "backend" "nodejs-http" "port" 8080 "secret" "nodejs4001-cert" "timeout" "600s") -}}
{{- range $service := list
  (dict "name" "angus" "config" .Values.angus "backend" "angus" "port" 80 "secret" "elektraweb-cert")
  (dict "name" "pos" "config" .Values.pos "backend" "pos-ng11" "port" 80 "secret" "elektrawebpos-cert")
  (dict "name" "reporting" "config" .Values.reporting "backend" "reportingcore" "port" 5000 "secret" "elektrawebreport-cert")
  (dict "name" "online-booking" "config" .Values.onlineBooking "backend" "online-booking" "port" 8080 "secret" "onlinebooking-cert")
  (dict "name" "callcenter" "config" .Values.callcenterintegration "backend" "call-center-integration" "port" 8000 "secret" "callcenterintegration-cert" "timeout" "3600s")
}}
{{- if $service.config.install -}}
{{- $services = append $services $service -}}
{{- end -}}
{{- end -}}
{{- if .Values.dashboardAccess.gateway.enabled -}}
{{- $services = append $services (dict "name" "dashboard" "config" .Values.dashboardAccess.gateway "backend" "kubernetes-dashboard" "namespace" .Values.dashboard.namespace "port" 443 "secret" "kubernetes-dashboard-cert") -}}
{{- end -}}
{{- $hosts := dict -}}
{{- range $service := $services -}}
{{- $host := required (printf "%s.host is required for gateway routing" $service.name) $service.config.host -}}
{{- if hasKey $hosts $host -}}
{{- fail (printf "Gateway host %s is configured more than once" $host) -}}
{{- end -}}
{{- $_ := set $hosts $host true -}}
{{- end -}}
{{- toYaml $services -}}
{{- end -}}
