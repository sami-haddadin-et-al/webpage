## Principal Investigator

{{ with site.GetPage "team/SamiHaddadin" }}
<div class="pi-home">
  {{ with .Params.image }}
    <img src="{{ . }}" alt="{{ $.Title }}" class="pi-avatar">
  {{ end }}

  <div class="pi-text">
    <strong><a href="{{ .RelPermalink }}">{{ .Title }}</a></strong><br/>

    {{ with .Params.role_first_line }}
      <span class="pi-role">{{ . }}</span><br/>
    {{ end }}

    {{ with .Params.role_second_line }}
      <span class="pi-role-second">{{ . }}</span>
    {{ end }}
  </div>
</div>
{{ end }}

## Intelligent Machines: New Frontiers for our Society

Our goal is to advance the scientific foundations of intelligent machines capable of autonomous interaction and learning in the world of their human creators. 
In the future, these machines will be part of global and heterogeneous cyber-physical societies that exploit the sheer unlimited possibilities arising from the massive increase in computing power and high-speed communications. 
With my team, we bridge the disciplines of distributed control, robotics, collective machine learning, and human motor intelligence. 
Our exploratory urge at the frontiers of the known allows us to design the fundamental principles to engineer artificial intelligence and intelligent robots.





---
