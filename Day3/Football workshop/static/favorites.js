const favoriteStorageKey = "touchline-favourite-team";
const selectedLeagueKey = "touchline-selected-league";
const knownLeagues = ["premier_league", "scottish_premiership", "bundesliga", "ligue_1"];

/** Persist an explicit league choice and apply the saved choice on navigation. */
function syncSelectedLeague() {
  const currentUrl = new URL(window.location.href);
  const queryLeague = currentUrl.searchParams.get("league");
  let selectedLeague = null;
  try {
    selectedLeague = localStorage.getItem(selectedLeagueKey);
    if (queryLeague && knownLeagues.includes(queryLeague)) {
      localStorage.setItem(selectedLeagueKey, queryLeague);
      selectedLeague = queryLeague;
    } else if (!selectedLeague) {
      selectedLeague = document.body.dataset.currentLeague;
      if (knownLeagues.includes(selectedLeague)) {
        localStorage.setItem(selectedLeagueKey, selectedLeague);
      }
    }

    if (!queryLeague && knownLeagues.includes(selectedLeague)) {
      currentUrl.searchParams.set("league", selectedLeague);
      window.location.replace(currentUrl.toString());
    }
  } catch {
    return;
  }
}

/** Read and validate the user's browser-stored favourite club. */
function readFavorite() {
  try {
    const saved = JSON.parse(localStorage.getItem(favoriteStorageKey) || "null");
    if (saved && typeof saved.team === "string" && typeof saved.league === "string") {
      return saved;
    }
  } catch {
    return null;
  }
  return null;
}

/** Refresh favourite labels, row highlights, and selectors across the page. */
function updateFavoriteDisplay(favorite) {
  document.querySelectorAll("[data-favorite-display]").forEach((element) => {
    element.textContent = favorite ? favorite.team : "No team selected";
  });
  document.querySelectorAll("[data-favorite-league]").forEach((element) => {
    element.textContent = favorite ? favorite.league.replaceAll("_", " ") : "Choose from a league table";
  });
  document.querySelectorAll(".standing-row").forEach((row) => {
    const isFavorite = Boolean(
      favorite &&
      favorite.league === row.dataset.league &&
      favorite.team.toLocaleLowerCase() === row.dataset.team.toLocaleLowerCase(),
    );
    row.classList.toggle("standing-row--favorite", isFavorite);
    const tag = row.querySelector(".favourite-tag");
    if (tag) tag.hidden = !isFavorite;
  });
  document.querySelectorAll(".match-row, .result-row").forEach((row) => {
    const teams = (row.dataset.teams || "").split("|");
    const isFavorite = Boolean(
      favorite &&
      favorite.league === row.dataset.league &&
      teams.includes(favorite.team.toLocaleLowerCase()),
    );
    row.classList.toggle("match-row--favorite", isFavorite);
    row.classList.toggle("result-row--favorite", isFavorite);
    const tag = row.querySelector(".favourite-match-tag");
    if (tag) tag.hidden = !isFavorite;
  });
  const picker = document.querySelector("#favorite-team");
  if (picker && favorite && picker.form.dataset.league === favorite.league) {
    picker.value = favorite.team;
  }
}

syncSelectedLeague();
const favorite = readFavorite();
updateFavoriteDisplay(favorite);

document.querySelectorAll("[data-team-form]").forEach((form) => {
  const picker = form.querySelector('select[name="team"]');
  if (
    picker &&
    !picker.value &&
    favorite &&
    favorite.league === form.dataset.league &&
    Array.from(picker.options).some((option) => option.value === favorite.team)
  ) {
    picker.value = favorite.team;
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-favorite-picker]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const team = form.querySelector("#favorite-team").value;
    if (!team) return;
    const selected = { team, league: form.dataset.league };
    try {
      localStorage.setItem(favoriteStorageKey, JSON.stringify(selected));
      updateFavoriteDisplay(selected);
      form.querySelector("button").textContent = "Favourite saved";
    } catch {
      form.querySelector("button").textContent = "Could not save";
    }
  });
});

document.querySelectorAll("[data-favorite-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const selectedFavorite = readFavorite();
    if (!selectedFavorite || selectedFavorite.league !== button.dataset.league) {
      button.textContent = "Choose a favourite in the league table";
      return;
    }

    const enabled = button.getAttribute("aria-pressed") !== "true";
    button.setAttribute("aria-pressed", String(enabled));
    button.textContent = enabled ? "★ Showing my team" : "★ My team";
    applyMatchFilters();
  });
});

let activeStatusFilter = "all";

/** Apply selected status and favourite filters without another API request. */
function applyMatchFilters() {
  const favoriteOnly = Array.from(document.querySelectorAll("[data-favorite-filter]"))
    .some((button) => button.getAttribute("aria-pressed") === "true");
  const selectedFavorite = favoriteOnly ? readFavorite() : null;
  let visibleMatches = 0;

  document.querySelectorAll(".match-row, .result-row").forEach((row) => {
    const statusMatches = activeStatusFilter === "all" || row.dataset.status === activeStatusFilter;
    const teams = (row.dataset.teams || "").split("|");
    const favoriteMatches = !selectedFavorite || (
      row.dataset.league === selectedFavorite.league &&
      teams.includes(selectedFavorite.team.toLocaleLowerCase())
    );
    const show = statusMatches && favoriteMatches;
    row.hidden = !show;
    if (show) visibleMatches += 1;
  });

  document.querySelectorAll(".standing-row").forEach((row) => {
    const show = !selectedFavorite || (
      row.dataset.league === selectedFavorite.league &&
      row.dataset.team.toLocaleLowerCase() === selectedFavorite.team.toLocaleLowerCase()
    );
    row.hidden = !show;
  });

  const empty = document.querySelector("#filtered-empty");
  if (empty) {
    const hasRows = document.querySelectorAll(".match-row, .result-row").length > 0;
    empty.hidden = !hasRows || visibleMatches > 0;
  }
}

document.querySelectorAll("[data-status-filter]").forEach((tab) => {
  tab.setAttribute("aria-pressed", String(tab.dataset.statusFilter === "all"));
  tab.addEventListener("click", () => {
    activeStatusFilter = tab.dataset.statusFilter;
    document.querySelectorAll("[data-status-filter]").forEach((item) => {
      item.classList.toggle("match-tab--active", item === tab);
      item.setAttribute("aria-pressed", String(item === tab));
    });
    applyMatchFilters();
  });
});
