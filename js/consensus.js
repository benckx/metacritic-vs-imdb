function consensusGallery(data) {
    document.getElementById("consensus-gallery").innerHTML = data.map(index => dashboardData.movies[index]).map(m => `
  <a class="consensus-card" href="${imdb(m)}" target="_blank" rel="noopener noreferrer" title="${m.t} (${m.y}) — Metascore ${pct(m.mc)}, IMDb ${pct(m.im)}">
    ${poster(m) ? `<img src="${poster(m)}" loading="lazy">` : ""}
    <div class="consensus-title">${m.t}</div>
    <div class="consensus-scores">${pct(m.mc)} · ${pct(m.im)}</div>
  </a>`).join("");
}
