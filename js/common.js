const RED = "#e05c55", BLUE = "#4e8de8", GREY = "#555e6e";
const poster = m => m.img;
const imdb = m => `https://www.imdb.com/title/${m.id}/`;
const pct = v => Math.round(v) + "%";
const sdiff = v => (v > 0 ? "+" : "") + Math.round(v) + "%";
const pointMeta = point => point.movie === undefined ? point.meta : dashboardData.movies[point.movie];

// ---------- shared tooltip ----------
function tipHTML(m) {
    const img = poster(m) ? `<img src="${poster(m)}" loading="lazy">` : "";
    return `<div class="apex-tip">${img}<div>
    <div class="tt">${m.t} (${m.y})</div>
    <div class="ts">Metascore ${pct(m.mc)} &middot; IMDb ${pct(m.im)}<br>
    diff ${sdiff(m.d)}<br>${m.v.toLocaleString()} votes</div></div></div>`;
}

const customTip = ({seriesIndex, dataPointIndex, w}) => {
    const meta = pointMeta(w.config.series[seriesIndex].data[dataPointIndex]);
    if (meta.average !== undefined) {
        return `<div class="apex-tip"><div><div class="tt">${meta.g} mean</div>
      <div class="ts">Signed difference: ${meta.average.toFixed(1)} percentage points<br>
      ${meta.count.toLocaleString()} movies · equal weight per movie</div></div></div>`;
    }
    return tipHTML(meta);
};

const baseChart = {
    background: "transparent",
    fontFamily: "system-ui, sans-serif",
    toolbar: {show: false},
    zoom: {enabled: false},
    animations: {enabled: false},
    events: {
        _: (_, __, {seriesIndex, dataPointIndex, w}) => {
            const movie = pointMeta(w.config.series[seriesIndex].data[dataPointIndex]);
            if (movie.id) window.open(imdb(movie), "_blank", "noopener,noreferrer");
        },
    },
};
const darkTheme = {mode: "dark"};
