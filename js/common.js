const RED = "#e05c55", BLUE = "#4e8de8", GREY = "#555e6e";
const poster = m => m.img;
const imdb = m => `https://www.imdb.com/title/${m.id}/`;
const pct = v => Math.round(v) + "%";
const sdiff = v => (v > 0 ? "+" : "") + Math.round(v) + "%";
const pointMeta = point => point.movie === undefined ? point.meta : dashboardData.movies[point.movie];

/**
 * Shared chart tooltip for plotted and timeline visualizations
 *
 * @param {string} title
 * @param {number} year
 * @param {number} metacriticScore
 * @param {number} imdbScore
 * @param {number} difference
 * @param {number} voteCount
 * @param {string} [posterPath]
 */
function tipHTML(title, year, metacriticScore, imdbScore, difference, voteCount, posterPath) {
    const posterHTML = posterPath ? `<img src="${posterPath}" loading="lazy">` : "";
    return `<div class="apex-tip">${posterHTML}<div>
    <div class="tt">${title} (${year})</div>
    <div class="ts">Metascore ${pct(metacriticScore)} &middot; IMDb ${pct(imdbScore)}<br>
    diff ${sdiff(difference)}<br>${voteCount.toLocaleString()} votes</div></div></div>`;
}

const customTip = ({seriesIndex, dataPointIndex, w}) => {
    const meta = pointMeta(w.config.series[seriesIndex].data[dataPointIndex]);
    if (meta.average !== undefined) {
        return `<div class="apex-tip"><div><div class="tt">${meta.g} mean</div>
      <div class="ts">Signed difference: ${meta.average.toFixed(1)} percentage points<br>
      ${meta.count.toLocaleString()} movies · equal weight per movie</div></div></div>`;
    }
    return tipHTML(meta.t, meta.y, meta.mc, meta.im, meta.d, meta.v, meta.img);
};

// noinspection JSUnusedGlobalSymbols
const baseChart = {
    background: "transparent",
    fontFamily: "system-ui, sans-serif",
    toolbar: {show: false},
    zoom: {enabled: false},
    animations: {enabled: false},
    events: {
        dataPointSelection: (_, __, {seriesIndex, dataPointIndex, w}) => {
            const movie = pointMeta(w.config.series[seriesIndex].data[dataPointIndex]);
            if (movie.id) window.open(imdb(movie), "_blank", "noopener,noreferrer");
        },
    },
};

const darkTheme = {mode: "dark"};
