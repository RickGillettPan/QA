# ShowFinder

ShowFinder is a small, standalone web page for searching and browsing a TV-show collection.

## Run it

Open `index.html` in a modern web browser. No installation, server, or internet connection is required.

## Features

- Search show titles and descriptions; matching is case-insensitive.
- Filter by genre and sort titles A–Z or Z–A.
- Save shows to a watchlist, stored in the browser's local storage.
- Show search results and an empty state when nothing matches.
- Use the Clear button to reset the search and filters.

## Update the collection

Edit the `shows` array in the `<script>` section of `index.html`. Each show has a title, genre, and description:

```js
{ title: "Example Show", genre: "Drama", description: "A short description." }
```

The genre filter is populated automatically from the genres in this array.
