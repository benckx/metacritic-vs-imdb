function diffColor(d) {
    const a = Math.min(Math.abs(d) / 50, 1) * 0.75 + 0.1;
    return d >= 0 ? `rgba(224,92,85,${a})` : `rgba(78,141,232,${a})`;
}

const scoreTooltip = document.getElementById("score-tooltip");
let scoreWidth = 0, scoreHeight = 0;

function positionScores(x, y) {
    const gap = 14;
    const left = Math.max(8, Math.min(x + gap, innerWidth - scoreWidth - 8));
    const top = Math.max(8, Math.min(y + gap, innerHeight - scoreHeight - 8));
    scoreTooltip.style.transform = `translate3d(${left}px, ${top}px, 0)`;
}

function showFloatingInfo(html, x, y) {
    scoreTooltip.innerHTML = html;
    scoreTooltip.hidden = false;
    const box = scoreTooltip.getBoundingClientRect();
    scoreWidth = box.width;
    scoreHeight = box.height;
    positionScores(x, y);
}

function scoreHTML(movie) {
    return `<div class="score-line"><span>IMDb</span><strong>${pct(movie.im)}</strong></div>
    <div class="score-line"><span>Metacritic</span><strong>${pct(movie.mc)}</strong></div>
    <div class="score-line"><span>Discrepancy</span><strong style="color:${movie.d >= 0 ? RED : BLUE}">${sdiff(movie.d)}</strong></div>`;
}

function bindMovieHover(element, movie, withPoster = false) {
    const show = (x, y) => {
        element.setAttribute("aria-describedby", "score-tooltip");
        const scores = scoreHTML(movie);
        const html = withPoster ? `<div class="movie-hover">
      ${poster(movie) ? `<img src="${poster(movie)}" width="72" height="106" decoding="async" alt="">` : ""}
      <div class="movie-hover-details"><div class="movie-hover-title">${movie.t} (${movie.y})</div>${scores}
        <div class="score-line"><span>IMDb votes</span><strong>${movie.v.toLocaleString()}</strong></div></div>
      </div>` : scores;
        showFloatingInfo(html, x, y);
    };
    const hide = () => {
        scoreTooltip.hidden = true;
        element.removeAttribute("aria-describedby");
    };
    element.addEventListener("pointerenter", event => show(event.clientX, event.clientY));
    element.addEventListener("pointermove", event => positionScores(event.clientX, event.clientY));
    element.addEventListener("pointerleave", hide);
    element.addEventListener("focusin", () => {
        const box = (element.querySelector(".diff-track") || element).getBoundingClientRect();
        show(box.left, box.top);
    });
    element.addEventListener("focusout", event => {
        if (!element.contains(event.relatedTarget)) hide();
    });
}

const movieRowHTML = (m, rank) => `<tr class="movie-row" tabindex="0">
    <td class="num muted">${rank}</td>
    <td class="poster-cell"><a href="${imdb(m)}" target="_blank" rel="noopener noreferrer" aria-label="Open ${m.t} on IMDb">${poster(m) ? `<img src="${poster(m)}" loading="lazy" decoding="async" alt="">` : ""}</a></td>
    <td class="movie-details">
      <a class="movie-link" href="${imdb(m)}" target="_blank" rel="noopener noreferrer">${m.t} <span class="muted">(${m.y})</span></a>
      <div class="diff-track">
        <span class="diff-fill" style="width:${Math.min(Math.abs(m.d), 100)}%;background:${diffColor(m.d)}"></span>
        <span class="diff-value">${sdiff(m.d)}</span>
      </div>
    </td>
  </tr>`;

function showMore(table, button, title, items, visible) {
    const start = visible;
    visible = Math.min(visible + 10, items.length);
    const rowsHTML = items.slice(start, visible).map((m, i) => movieRowHTML(m, start + i + 1)).join("");
    table.tBodies[0].insertAdjacentHTML("beforeend", rowsHTML);
    const added = Array.from(table.querySelectorAll(".movie-row")).slice(start);
    added.forEach((row, i) => {
        const movie = items[start + i];
        bindMovieHover(row, movie);
        row.addEventListener("click", event => {
            if (!event.target.closest("a, .diff-track")) {
                window.open(imdb(movie), "_blank", "noopener,noreferrer");
            }
        });
        row.addEventListener("keydown", event => {
            if (event.key === "Enter" && event.target === row) {
                window.open(imdb(movie), "_blank", "noopener,noreferrer");
            }
        });
    });
    table.caption.textContent = `${title} — top ${visible}`;
    if (visible === items.length) {
        if (document.activeElement === button && added.length) added[0].focus();
        button.hidden = true;
    }
    return visible;
}

function buildTable(sel, title, color, items) {
    const table = document.querySelector(sel);
    table.innerHTML =
        `<caption style="color:${color}"></caption>
     <colgroup><col class="rank-column"><col class="poster-column"><col></colgroup>
     <tbody></tbody>`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "view-more";
    button.textContent = "View more";
    button.setAttribute("aria-label", `View more: ${title}`);
    table.after(button);
    let visible = 0;

    button.addEventListener("click", () => {
        visible = showMore(table, button, title, items, visible);
    });
    visible = showMore(table, button, title, items, visible);
}
