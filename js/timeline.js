// ---------- year-by-year chart ----------
function alignTimelineTitles(context) {
    let titles = context.el.querySelector(".timeline-titles");
    if (!titles) {
        titles = document.createElement("div");
        titles.className = "timeline-titles";
        context.el.appendChild(titles);
    }
    if (titles.querySelector('[aria-describedby="score-tooltip"]')) scoreTooltip.hidden = true;
    titles.replaceChildren();
    const {translateX, translateY, gridWidth, gridHeight} = context.w.globals;
    const axis = context.w.config.yaxis[0];
    const right = translateX + gridWidth + 12;
    const width = context.el.clientWidth;
    context.w.config.series.slice(0, 2).forEach(series => {
        series.data.forEach(point => {
            const movie = pointMeta(point);
            const label = document.createElement("a");
            const left = movie.d < 0;
            label.className = "timeline-title " + (left ? "left" : "right");
            label.href = imdb(movie);
            label.target = "_blank";
            label.rel = "noopener noreferrer";
            label.textContent = movie.t;
            label.style.left = (left ? 0 : right) + "px";
            label.style.width = Math.max(0, left ? translateX - 36 : width - right) + "px";
            label.style.top = (translateY + gridHeight * (axis.max - movie.y) / (axis.max - axis.min) - 7) + "px";
            bindMovieHover(label, movie, true);
            titles.appendChild(label);
        });
    });
}

function yearByYearChart(data) {
    const dAbs = data.limit;
    const series = [
        ["Critics like it more", data.pos],
        ["Users like it more", data.neg],
        ["Popular movies", data.ctx],
    ].map(([name, indexes]) => ({
        name, data: indexes.map(movie => {
            const m = dashboardData.movies[movie];
            return {x: m.d, y: m.y, movie};
        }),
    }));
    return new ApexCharts(document.querySelector("#chart-year-by-year"), {
        chart: {
            ...baseChart, type: "scatter", height: 780,
            events: {
                ...baseChart.events,
                mounted: alignTimelineTitles,
                updated: alignTimelineTitles,
            },
        },
        theme: darkTheme,
        series,
        colors: [RED, BLUE, GREY],
        markers: {size: [6, 6, 3], strokeWidth: 0, hover: {sizeOffset: 2}},
        dataLabels: {enabled: false},
        xaxis: {
            min: -dAbs, max: dAbs, tickAmount: 10, crosshairs: {show: false},
            title: {text: "Metascore − IMDb (%)"},
            labels: {formatter: v => (v > 0 ? "+" : "") + Math.round(v)}
        },
        yaxis: {
            min: 1978, max: 2028, crosshairs: {show: false},
            labels: {formatter: v => Math.round(v)}
        },
        grid: {borderColor: "#232a36", padding: {left: 180, right: 180}},
        legend: {position: "top"},
        tooltip: {custom: customTip, intersect: true, shared: false},
        annotations: {
            xaxis: [{x: 0, strokeDashArray: 0, borderColor: "#49536400"},
                {x: 0, borderColor: "#6b7689"}]
        },
    }).render();
}
