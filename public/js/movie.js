(function () {
  const id = new URLSearchParams(location.search).get("id");
  const titleEl = document.getElementById("title");
  const blurbEl = document.getElementById("blurb");
  const posterEl = document.getElementById("poster");
  const safetyEl = document.getElementById("safety");
  const timelineEl = document.getElementById("timeline");
  const legendEl = document.getElementById("legend");
  const scenesEl = document.getElementById("scenes");
  const tip = document.getElementById("seg-tooltip");
  const tipImg = document.getElementById("seg-tooltip-img");
  const tipCat = document.getElementById("seg-tooltip-cat");
  const tipTime = document.getElementById("seg-tooltip-time");
  const tipText = document.getElementById("seg-tooltip-text");

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function clock(t) {
    t = Math.max(0, Math.floor(Number(t) || 0));
    const m = Math.floor(t / 60);
    const s = t % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  function showTip(seg, x, y) {
    if (!seg) return;
    tip.hidden = false;
    tip.classList.add("fixed");
    tip.style.left = Math.min(window.innerWidth - 320, Math.max(8, x + 12)) + "px";
    tip.style.top = Math.min(window.innerHeight - 360, Math.max(8, y + 12)) + "px";
    tipCat.className = "pill " + (seg.category || "");
    tipCat.textContent = seg.label || seg.category || "";
    tipTime.textContent = clock(seg.t_start) + "–" + clock(seg.t_end);
    tipText.textContent = seg.summary || "";
    if (seg.thumb) {
      tipImg.hidden = false;
      tipImg.src = seg.thumb;
    } else {
      tipImg.hidden = true;
      tipImg.removeAttribute("src");
    }
  }

  function hideTip() {
    tip.hidden = true;
  }

  if (!id) {
    titleEl.textContent = "Missing movie id";
    return;
  }

  fetch("/api/v1/movies/" + encodeURIComponent(id) + ".json")
    .then((r) => {
      if (!r.ok) throw new Error(String(r.status));
      return r.json();
    })
    .then((m) => {
      document.title = m.title + " — GunStamps";
      titleEl.textContent = m.title + (m.year ? " (" + m.year + ")" : "");
      blurbEl.textContent = m.summary || "";
      if (m.poster) {
        posterEl.hidden = false;
        posterEl.src = m.poster;
        posterEl.alt = m.title + " poster";
      }

      const s = m.safety || {};
      const bar = (s.bar || [])
        .map(
          (p) =>
            '<span class="safety-seg ' +
            esc(p.id) +
            '" style="width:' +
            Number(p.share_pct || 0).toFixed(2) +
            '%" title="' +
            esc(p.tooltip || p.label || "") +
            '"></span>'
        )
        .join("");
      const legendPills = (s.bar || [])
        .filter((p) => p.id !== "other")
        .map(
          (p) =>
            '<span class="pill ' +
            esc(p.id) +
            '" title="' +
            esc(p.tooltip || "") +
            '">' +
            esc(p.label) +
            " · " +
            Number(p.film_pct || 0).toFixed(0) +
            "%</span>"
        )
        .join("");
      safetyEl.hidden = false;
      safetyEl.innerHTML =
        '<div class="safety-bar" style="height:16px">' +
        bar +
        "</div>" +
        '<div class="safety-bar-legend">' +
        legendPills +
        "</div>" +
        '<p class="safety-headline"><span class="rag ' +
        esc(s.rag || "") +
        '">' +
        esc(s.rag_label || "") +
        "</span> " +
        esc(s.headline || "") +
        "</p>" +
        '<p class="muted safety-detail">' +
        esc(s.pct_label || "") +
        " of minutes flagged · " +
        esc(m.segment_count || 0) +
        " scenes</p>";

      legendEl.innerHTML = legendPills;

      const duration = Math.max(1, Number(m.duration_s) || 1);
      const segs = m.segments || [];
      timelineEl.hidden = segs.length === 0;
      segs.forEach((seg) => {
        const el = document.createElement("div");
        el.className = "seg " + (seg.category || "");
        const left = (Number(seg.t_start) / duration) * 100;
        const width = Math.max(
          0.35,
          ((Number(seg.t_end) - Number(seg.t_start)) / duration) * 100
        );
        el.style.left = left + "%";
        el.style.width = width + "%";
        el.title = (seg.label || seg.category || "") + "";
        el.addEventListener("mousemove", (ev) => showTip(seg, ev.clientX, ev.clientY));
        el.addEventListener("mouseleave", hideTip);
        timelineEl.appendChild(el);
      });

      if (!segs.length) {
        scenesEl.innerHTML = '<p class="empty">No flagged scenes.</p>';
        return;
      }
      scenesEl.innerHTML =
        '<table class="results scenes-table"><thead><tr>' +
        "<th></th><th>Type</th><th>Start</th><th>End</th><th>Description</th>" +
        "</tr></thead><tbody>" +
        segs
          .map((seg) => {
            return (
              "<tr>" +
              '<td class="thumb-cell">' +
              (seg.thumb
                ? '<img class="seg-thumb" src="' +
                  esc(seg.thumb) +
                  '" alt="" width="72" height="72" loading="lazy" />'
                : "") +
              "</td>" +
              "<td><span class=\"pill " +
              esc(seg.category) +
              '">' +
              esc(seg.label || seg.category) +
              "</span></td>" +
              '<td class="mono">' +
              clock(seg.t_start) +
              "</td>" +
              '<td class="mono">' +
              clock(seg.t_end) +
              "</td>" +
              "<td>" +
              esc(seg.summary || "") +
              "</td></tr>"
            );
          })
          .join("") +
        "</tbody></table>";
    })
    .catch(() => {
      titleEl.textContent = "Not found";
    });
})();
