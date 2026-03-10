+++
title = "Team"
layout = "team"
+++

# Team

## Principal Investigator

{{ with .Site.GetPage "team/SamiHaddadin" }}
- [{{ .Title }}]({{ .RelPermalink }}){{ with .Params.role }} — {{ . }}{{ end }}
{{ end }}

---

## Members

{{ with .Site.GetPage "section" "team/members" }}
{{ range .Pages.ByTitle }}
- [{{ .Title }}]({{ .RelPermalink }}){{ with .Params.role }} — {{ . }}{{ end }}
{{ end }}
{{ end }}