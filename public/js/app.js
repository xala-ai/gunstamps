(function () {
  const rowsEl = document.getElementById("rows");
  const table = document.getElementById("table");
  const status = document.getElementById("status");
  const empty = document.getElementById("empty");
  const q = document.getElementById("q");
  let movies = [];

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function barHtml(safety) {
    const parts = (safety && safety.bar) || [];
    if (!parts.length) return '<div class="safety-bar"><span class="safety-seg other" style="width:100%"></span></div>';
    return (
      '<div class="safety-bar">' +
      parts
        .map((p) => {
          const tip = esc(p.tooltip || p.label || p.id);
          return (
            '<span class="safety-seg ' +
            esc(p.id) +
            '" style="width:' +
            Number(p.share_pct || 0).toFixed(2) +
            '%" title="' +
            tip +
            '"></span>'
          );
        })
        .join("") +
      "</div>"
    );
  }

  function render(list) {
    rowsEl.innerHTML = list
      .map((m) => {
        const s = m.safety || {};
        const title = esc(m.title) + (m.year ? " (" + esc(m.year) + ")" : "");
        return (
          "<tr data-title=\"" +
          esc((m.title || "").toLowerCase() + " " + (m.year || "")) +
          "\">" +
          "<td><a href=\"/movie.html?id=" +
          encodeURIComponent(m.id) +
          "\">" +
          title +
          "</a></td>" +
          "<td>" +
          (m.poster
            ? '<img class="poster-thumb" src="' + esc(m.poster) + '" alt="" loading="lazy" />'
            : "—") +
          "</td>" +
          "<td>" +
          barHtml(s) +
          '<div class="meta"><span class="rag ' +
          esc(s.rag || "") +
          '">' +
          esc(s.rag_label || "") +
          "</span><span>" +
          esc(s.pct_label || "") +
          " unsafe min</span></div>" +
          (m.summary ? '<div class="summary">' + esc(m.summary) + "</div>" : "") +
          "</td>" +
          "<td>" +
          esc(m.segment_count ?? "—") +
          "</td></tr>"
        );
      })
      .join("");
    table.hidden = list.length === 0;
    empty.hidden = list.length !== 0;
  }

  function filter() {
    const needle = (q.value || "").trim().toLowerCase();
    const list = !needle
      ? movies
      : movies.filter((m) =>
          ((m.title || "") + " " + (m.year || "")).toLowerCase().includes(needle)
        );
    render(list);
  }

  fetch("/api/v1/movies.json")
    .then((r) => {
      if (!r.ok) throw new Error("API " + r.status);
      return r.json();
    })
    .then((data) => {
      movies = data.movies || [];
      status.hidden = true;
      filter();
    })
    .catch((err) => {
      status.textContent = "Could not load catalog: " + err.message;
    });

  q.addEventListener("input", filter);
  q.addEventListener("search", filter);
})();
