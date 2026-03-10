+++
title = "Team"
+++


[//]: # (+++)
[//]: # (title = "Person A")
[//]: # (role = "PhD Student"        # PhD (now at...)
[//]: # (role_group = "PhD"          # used for filtering: PhD, Postdoc, MSc, BSc, Staff, Visiting, Collaborator)
[//]: # (status = "active"           # "active" or "alumni")
[//]: # (image = "/images/team/personA.jpg")
[//]: # (+++)


# Our Team

## Principal Investigator
{{ with .Site.GetPage "team/haddadin" }}
<div class="team-section">
  <div class="team-grid team-grid-pi">
    <div class="team-card">
      {{ with .Params.image }}
        <img src="{{ . }}" alt="{{ $.Title }}" class="team-photo">
      {{ end }}
      <div class="team-card-body">
        <h3 class="team-name"><a href="{{ .RelPermalink }}">{{ .Title }}</a></h3>
        {{ with .Params.role }}<p class="team-role">{{ . }}</p>{{ end }}
      </div>
    </div>
  </div>
</div>
{{ end }}

---

## Members

<div class="team-controls">
  <label for="roleFilter" class="team-filter-label">Filter by role:</label>
  <select id="roleFilter" class="team-filter">
    <option value="all">All</option>
  </select>
  <noscript>
    <span class="team-noscript">JavaScript is disabled — members are shown in a fixed (alphabetical) order and filtering/shuffling is unavailable.</span>
  </noscript>
</div>

<div id="team-members" class="team-grid">
  {{ with .Site.GetPage "section" "team/members" }}
    {{ range .Pages.ByTitle }}
      {{ $status := .Params.status | default "active" }}
      {{ $roleGroup := .Params.role_group | default "Other" }}
      <div class="team-card member-card"
           data-status="{{ $status }}"
           data-role="{{ $roleGroup }}">
        {{ with .Params.image }}
          <img src="{{ . }}" alt="{{ $.Title }}" class="team-photo">
        {{ end }}
        <div class="team-card-body">
          <h3 class="team-name"><a href="{{ .RelPermalink }}">{{ .Title }}</a></h3>
          {{ with .Params.role }}<p class="team-role">{{ . }}</p>{{ end }}
          <p class="team-meta">{{ $roleGroup }}</p>
        </div>
      </div>
    {{ end }}
  {{ end }}
</div>

<h2 id="alumni-heading" class="team-alumni-title">Alumni</h2>
<div id="team-alumni" class="team-grid"></div>

<script>
(function () {
  function shuffleInPlace(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr;
  }

  function uniqueSorted(values) {
    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
  }

  function buildRoleFilter(selectEl, roleGroups) {
    roleGroups.forEach(r => {
      const opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      selectEl.appendChild(opt);
    });
  }

  function applyFilter(cards, roleValue) {
    cards.forEach(card => {
      const role = card.getAttribute("data-role") || "Other";
      const show = (roleValue === "all") || (role === roleValue);
      card.style.display = show ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const membersContainer = document.getElementById("team-members");
    const alumniContainer = document.getElementById("team-alumni");
    const alumniHeading = document.getElementById("alumni-heading");
    const filterSelect = document.getElementById("roleFilter");

    if (!membersContainer || !alumniContainer || !filterSelect) return;

    const allCards = Array.from(membersContainer.getElementsByClassName("member-card"));

    // Split active vs alumni
    const active = [];
    const alumni = [];

    allCards.forEach(card => {
      const status = (card.getAttribute("data-status") || "active").toLowerCase();
      if (status === "alumni") alumni.push(card);
      else active.push(card);
    });

    // Move alumni cards into alumni container
    alumni.forEach(card => alumniContainer.appendChild(card));

    // Hide alumni section if empty
    if (alumni.length === 0) {
      alumniHeading.style.display = "none";
      alumniContainer.style.display = "none";
    }

    // Randomize order on each refresh (active + alumni independently)
    shuffleInPlace(active).forEach(card => membersContainer.appendChild(card));
    shuffleInPlace(alumni).forEach(card => alumniContainer.appendChild(card));

    // Build role filter options from ALL cards (active + alumni)
    const roles = uniqueSorted(allCards.map(c => c.getAttribute("data-role") || "Other"));
    buildRoleFilter(filterSelect, roles);

    // Filter applies to both sections
    filterSelect.addEventListener("change", function () {
      const v = filterSelect.value;
      applyFilter(active, v);
      applyFilter(alumni, v);

      // If filtering hides all alumni, hide heading to avoid empty block
      const anyAlumniVisible = alumni.some(c => c.style.display !== "none");
      if (alumni.length > 0) alumniHeading.style.display = anyAlumniVisible ? "" : "none";
    });
  });
})();
</script>

<style>
/* Controls */
.team-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin: 1rem 0 1.25rem 0;
}
.team-filter-label { font-weight: 600; }
.team-filter {
  padding: 0.35rem 0.6rem;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.15);
}
.team-noscript {
  margin-left: 0.5rem;
  font-size: 0.95rem;
  opacity: 0.8;
}

/* Grid */
.team-grid {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
@media (min-width: 640px) {
  .team-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 1024px) {
  .team-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

/* PI grid can be one/two columns depending on theme width */
.team-grid-pi {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}
@media (min-width: 900px) {
  .team-grid-pi { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* Card */
.team-card {
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255,255,255,0.75);
  box-shadow: 0 4px 14px rgba(0,0,0,0.06);
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}
.team-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(0,0,0,0.12);
  border-color: rgba(0,0,0,0.18);
}

/* Image */
.team-photo {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  display: block;
}

/* Text */
.team-card-body { padding: 0.9rem 1rem 1.05rem 1rem; }
.team-name { margin: 0; font-size: 1.1rem; }
.team-name a { text-decoration: none; }
.team-name a:hover { text-decoration: underline; }
.team-role { margin: 0.35rem 0 0 0; opacity: 0.9; }
.team-meta { margin: 0.4rem 0 0 0; font-size: 0.95rem; opacity: 0.7; }

.team-alumni-title { margin-top: 2.5rem; }
</style>