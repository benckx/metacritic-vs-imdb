const categoryHoverMarkers = new WeakSet();

/**
 * @typedef {Object} CategoryMeanPoint
 * @property {number} x Metacritic minus IMDb percentage at the arrow tip.
 * @property {number} y Category row index at the arrow height.
 * @property {{g: string, average: number, count: number}} meta Category mean summary.
 */

/**
 * @typedef {Object} ChartContext
 * @property {HTMLElement} el Chart container element.
 * @property {Object} w ApexCharts context.
 */

/**
 * @param {ChartContext} context
 * @param {string} svgNS SVG namespace.
 * @returns {SVGSVGElement}
 */
function initSvg(context, svgNS) {
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
    return svg;
}

/**
 * Draw one category mean arrow.
 *
 * @param {ChartContext} context
 * @param {string} svgNS SVG namespace.
 * @param {CategoryMeanPoint} point Category mean; x is the arrow-tip score difference,
 * y is the category row index.
 * @param {function(number): number} scoreDifferenceToPixelX Maps an x-axis score difference to a pixel.
 * @param {function(number): number} categoryIndexToPixelY Maps a category row index to a pixel.
 * @returns {SVGLineElement}
 */
function drawArrow(context, svgNS, point, scoreDifferenceToPixelX, categoryIndexToPixelY) {
    const markerId = `${context.el.id}-mean-head`;
    const line = document.createElementNS(svgNS, "line");
    const direction = point.x > 0 ? "positive" : point.x < 0 ? "negative" : "zero";
    const color = point.x > 0 ? RED : point.x < 0 ? BLUE : GREY;
    const lineAttributes = {
        x1: scoreDifferenceToPixelX(0),
        x2: scoreDifferenceToPixelX(point.x),
        y1: categoryIndexToPixelY(point.y),
        y2: categoryIndexToPixelY(point.y),
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
    return line;
}

/**
 * Draw arrows from the zero point to each category mean.
 *
 * @param {ChartContext} context
 * @returns {void}
 */
function drawMeanArrows(context) {
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = initSvg(context, svgNS);
    const {translateX, translateY, gridWidth, gridHeight} = context.w.globals;
    const xAxis = context.w.config.xaxis;
    const yAxis = context.w.config.yaxis[0];
    const scoreDifferenceToPixelX = scoreDifference =>
        translateX + gridWidth * (scoreDifference - xAxis.min) / (xAxis.max - xAxis.min);
    const categoryIndexToPixelY = categoryIndex =>
        translateY + gridHeight * (yAxis.max - categoryIndex) / (yAxis.max - yAxis.min);
    const meanArrowPoints = context.w.config.series[2].data;
    meanArrowPoints.forEach(point => {
        svg.appendChild(drawArrow(context, svgNS, point, scoreDifferenceToPixelX, categoryIndexToPixelY));
    });
    context.el.appendChild(svg);
}

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
        series: [data.series[1], data.series[0], data.series[2]],
        colors: [BLUE, RED, GREY],
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
