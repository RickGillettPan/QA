const dateLabel = document.querySelector("#today-label");
// Present dates in the visitor's locale instead of showing the server's UTC text.
if (dateLabel) {
  dateLabel.textContent = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date());
}

// Convert ESPN timestamps to readable local date and time labels.
document.querySelectorAll(".local-time").forEach((time) => {
  const parsed = new Date(time.dateTime);
  if (!Number.isNaN(parsed.getTime())) {
    time.textContent = new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(parsed);
  }
});
