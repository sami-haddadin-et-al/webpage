+++
title = "Team"
+++

# Team

## Principal Investigator

{{ with .Site.GetPage "team/haddadin" }}
{{ with .Params.image }}
<img src="{{ . }}" alt="{{ $.Title }}" style="max-width:220px; border-radius:12px; margin:0.5rem 0 1rem 0;">
{{ end }}

### [{{ .Title }}]({{ .RelPermalink }})

{{ with .Params.role }}{{ . }}{{ end }}
{{ end }}

---

## Members

{{ with .Site.GetPage "section" "team/members" }}
<ul>
  {{ range .Pages.ByTitle }}
    <li>
      {{ with .Params.image }}
        <img src="{{ . }}" alt="{{ $.Title }}" style="width:64px; height:64px; object-fit:cover; border-radius:50%; vertical-align:middle; margin-right:10px;">
      {{ end }}
      <a href="{{ .RelPermalink }}">{{ .Title }}</a>
      {{ with .Params.role }} — {{ . }}{{ end }}
    </li>
  {{ end }}
</ul>
{{ end }}