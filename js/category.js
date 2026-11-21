function drawMeanArrows(context) {
    const svgNS = "http://www.w3.org/2000/svg";
    context.el.querySelector(".mean-arrows")?.remove();
    const svg = document.createElementNS(svgNS, "svg");
    svg.classList.add("mean-arrows");
    svg.setAttribute("width", context.el.clientWidth);
    svg.setAttribute("height", context.el.clientHeight);
    const defs = document.createElementNS(svgNS, "defs");
    const markerId = `${context.el.id}-mean-head`;
    for (const [direction, color] of [["positive", RED], ["negative", BLUE], ["zero", GREY]]) {
        const head = document.createElementNS(svgNS, "marker");
        const headAttributes = {
            id: `${markerId}-${direction}`, viewBox: "0 0 10 10", refX: 9, refY: 5,
            markerWidth: 5, markerHeight: 5, orient: "auto",
        };
        for (const [key, value] of Object.entries(headAttributes)) {
            head.setAttribute(key, value.toString());
        }
        const triangle = document.createElementNS(svgNS, "path");
        triangle.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
        triangle.setAttribute("fill", color);
        head.appendChild(triangle);
        defs.appendChild(head);
    }
    svg.appendChild(defs);
    const {translateX, translateY, gridWidth, gridHeight} = context.w.globals;
    const xaxis = context.w.config.xaxis;
    const yaxis = context.w.config.yaxis[0];
    const x = value => translateX + gridWidth * (value - xaxis.min) / (xaxis.max - xaxis.min);
    const y = value => translateY + gridHeight * (yaxis.max - value) / (yaxis.max - yaxis.min);
    context.w.config.series[2].data.forEach(point => {
        const line = document.createElementNS(svgNS, "line");
        const direction = point.x > 0 ? "positive" : point.x < 0 ? "negative" : "zero";
        const color = point.x > 0 ? RED : point.x < 0 ? BLUE : GREY;
        const lineAttributes = {
            x1: x(0), x2: x(point.x), y1: y(point.y), y2: y(point.y),
            stroke: color, "stroke-width": 2, "marker-end": `url(#${markerId}-${direction})`,
        };
        for (const [key, value] of Object.entries(lineAttributes)) {
            line.setAttribute(key, value);
        }
        line.classList.add("mean-arrow");
        line.addEventListener("pointerenter", event => {
            showFloatingInfo(customTip({
                seriesIndex: 2,
                dataPointIndex: point.y,
                w: context.w,
            }), event.clientX, event.clientY);
        });
        line.addEventListener("pointermove", event => positionScores(event.clientX, event.clientY));
        line.addEventListener("pointerleave", () => {
            scoreTooltip.hidden = true;
        });
        svg.appendChild(line);
    });
    context.el.appendChild(svg);
}

const categoryHoverMarkers = new WeakSet();

function bindCategoryHover(context) {
    drawMeanArrows(context);
    context.el.querySelectorAll(".apexcharts-series").forEach((series, i) => {
        if (i >= 2) return;
        const markers = series.querySelectorAll(".apexcharts-marker");
        context.w.config.series[i].data.forEach((point, j) => {
            const marker = markers[j];
            if (categoryHoverMarkers.has(marker)) return;
            const movie = pointMeta(point);
            bindMovieHover(marker, movie, true);
            marker.setAttribute("tabindex", "0");
            marker.setAttribute("role", "link");
            marker.setAttribute("aria-label", `${movie.t} (${movie.y}) on IMDb`);
            marker.addEventListener("keydown", event => {
                if (event.key === "Enter") window.open(imdb(movie), "_blank", "noopener,noreferrer");
            });
            categoryHoverMarkers.add(marker);
        });
    });
}

function categoryChart(sel, data) {
    const labels = data.labels;
    const lim = data.limit;
    return new ApexCharts(document.querySelector(sel), {
        chart: {
            ...baseChart, type: "scatter", height: data.height,
            events: {...baseChart.events, mounted: bindCategoryHover, updated: bindCategoryHover}
        },
        theme: darkTheme,
        series: data.series,
        colors: [RED, BLUE, GREY],
        markers: {size: [6, 6, 0], strokeWidth: 0, hover: {sizeOffset: 0}},
        xaxis: {
            min: -lim, max: lim, tickAmount: 10, crosshairs: {show: false},
            title: {text: "Metascore − IMDb (%)"},
            labels: {formatter: v => (v > 0 ? "+" : "") + Math.round(v)}
        },
        yaxis: {
            min: -1, max: labels.length, crosshairs: {show: false},
            tickAmount: labels.length + 1,
            labels: {formatter: v => labels[Math.round(v)] ?? ""}
        },
        grid: {borderColor: "#232a36"},
        legend: {position: "top"},
        tooltip: {enabled: false},
        annotations: {xaxis: [{x: 0, borderColor: "#6b7689", strokeDashArray: 0}]},
    }).render();
}
