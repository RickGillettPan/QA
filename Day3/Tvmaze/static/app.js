const grid = document.querySelector("#show-grid");

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    const form = document.querySelector(".search-form");
    form.querySelector("#query").value = button.dataset.query;
    form.requestSubmit();
  });
});

document.querySelector(".search-form").addEventListener("submit", (event) => {
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true;
  button.querySelector("span").textContent = "Searching…";
});

if (grid) {
  const cards = Array.from(grid.querySelectorAll(".show-card"));
  const genreFilter = document.querySelector("#genre-filter");
  const sortOrder = document.querySelector("#sort-order");
  const favoritesFilter = document.querySelector("#favorites-filter");
  const visibleCount = document.querySelector("#visible-count");
  const favoritesCount = document.querySelector("#favorites-count");
  const noFilterResults = document.querySelector("#no-filter-results");
  const filterStatus = document.querySelector("#filter-status");
  const favoriteKey = "screenly-favorites";
  let favorites = new Set();
  let favoritesOnly = false;

  try {
    const savedFavorites = JSON.parse(localStorage.getItem(favoriteKey) || "[]");
    if (Array.isArray(savedFavorites)) {
      favorites = new Set(savedFavorites.filter((name) => typeof name === "string"));
    }
  } catch {
    filterStatus.textContent = "Favorites cannot be restored in this browser session.";
  }

  const genres = new Set();
  for (const card of cards) {
    const showGenres = JSON.parse(card.dataset.genres || "[]");
    for (const genre of showGenres) {
      genres.add(genre);
    }
  }
  for (const genre of Array.from(genres).sort((a, b) => a.localeCompare(b))) {
    const option = document.createElement("option");
    option.value = genre;
    option.textContent = genre;
    genreFilter.append(option);
  }

  function updateFavorites() {
    for (const card of cards) {
      const button = card.querySelector(".favorite-button");
      const isFavorite = favorites.has(card.dataset.name);
      button.setAttribute("aria-pressed", String(isFavorite));
      button.setAttribute(
        "aria-label",
        `${isFavorite ? "Remove" : "Add"} ${card.querySelector("h3").textContent} ${isFavorite ? "from" : "to"} favorites`,
      );
      button.querySelector("span").textContent = isFavorite ? "♥" : "♡";
    }
    favoritesCount.textContent = String(favorites.size);
  }

  function renderCards() {
    const selectedGenre = genreFilter.value;
    const sort = sortOrder.value;
    const visibleCards = cards.filter((card) => {
      const matchesGenre = !selectedGenre || JSON.parse(card.dataset.genres || "[]").includes(selectedGenre);
      const matchesFavorites = !favoritesOnly || favorites.has(card.dataset.name);
      return matchesGenre && matchesFavorites;
    });

    visibleCards.sort((first, second) => {
      if (sort === "rating") {
        return Number(second.dataset.rating) - Number(first.dataset.rating);
      }
      if (sort === "name") {
        return first.dataset.name.localeCompare(second.dataset.name);
      }
      return cards.indexOf(first) - cards.indexOf(second);
    });

    for (const card of cards) {
      card.hidden = true;
    }
    for (const card of visibleCards) {
      card.hidden = false;
      grid.append(card);
    }

    visibleCount.textContent = String(visibleCards.length);
    noFilterResults.hidden = visibleCards.length > 0;
    filterStatus.textContent = selectedGenre || favoritesOnly
      ? `${visibleCards.length} of ${cards.length} titles shown`
      : "";
  }

  grid.addEventListener("click", (event) => {
    const button = event.target.closest(".favorite-button");
    if (!button) return;

    const name = button.closest(".show-card").dataset.name;
    if (favorites.has(name)) {
      favorites.delete(name);
    } else {
      favorites.add(name);
    }
    try {
      localStorage.setItem(favoriteKey, JSON.stringify(Array.from(favorites)));
    } catch {
      filterStatus.textContent = "Favorites are available until you close this tab.";
    }
    updateFavorites();
    renderCards();
  });

  genreFilter.addEventListener("change", renderCards);
  sortOrder.addEventListener("change", renderCards);
  favoritesFilter.addEventListener("click", () => {
    favoritesOnly = !favoritesOnly;
    favoritesFilter.setAttribute("aria-pressed", String(favoritesOnly));
    renderCards();
  });

  updateFavorites();
  renderCards();
}
