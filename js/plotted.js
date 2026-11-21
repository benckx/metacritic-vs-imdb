// ---------- plotted chart ----------
function drawEqualityLine(context) {
    context.el.querySelector(".equality-line")?.remove();
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("equality-line");
    svg.setAttribute("width", context.el.clientWidth);
    svg.setAttribute("height", context.el.clientHeight);
    svg.setAttribute("aria-hidden", "true");
    const {translateX, translateY, gridWidth, gridHeight} = context.w.globals;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    const lineAttributes = {
        x1: translateX, y1: translateY + gridHeight,
        x2: translateX + gridWidth, y2: translateY,
        stroke: "#8b94a5", "stroke-width": 1.5, "stroke-dasharray": "2 4",
    };
    for (const [key, value] of Object.entries(lineAttributes)) {
        line.setAttribute(key, value);
    }
    svg.appendChild(line);
    context.el.prepend(svg);
}

function plotted(data) {
    const maxVotes = Math.max(...[...data.pos, ...data.neg, ...data.ctx]
        .map(index => dashboardData.movies[index].v));
    const differences = data.ctx.map(index => dashboardData.movies[index].d);
    const minDiff = Math.min(...differences), maxDiff = Math.max(...differences);
    const series = [
        ["Metacritic > IMDb", data.pos],
        ["IMDb > Metacritic", data.neg],
        ["Popular movies", data.ctx],
    ].map(([name, indexes], seriesIndex) => ({
        name, data: indexes.map(movie => {
            const m = dashboardData.movies[movie];
            const point = {x: m.mc, y: m.im, z: 2 + 10 * Math.sqrt(m.v / maxVotes), movie};
            if (seriesIndex === 2) {
                const t = m.d < 0 ? (1 - m.d / minDiff) / 2 :
                    m.d > 0 ? (1 + m.d / maxDiff) / 2 : 0.5;
                point.fillColor = `rgba(${Math.round(78 + 146 * t)},${Math.round(141 - 49 * t)},${Math.round(232 - 147 * t)},0.35)`;
            }
            return point;
        }),
    }));
    return new ApexCharts(document.querySelector("#chart-plotted"), {
        chart: {
            ...baseChart, type: "bubble", height: "100%", parentHeightOffset: 0,
            events: {...baseChart.events, mounted: drawEqualityLine, updated: drawEqualityLine}
        },
        theme: darkTheme,
        series,
        colors: [RED, BLUE, GREY],
        fill: {type: "solid", opacity: [0.9, 0.9, 0.35]},
        plotOptions: {bubble: {zScaling: false}},
        dataLabels: {enabled: false},
        markers: {strokeWidth: 0},
        stroke: {show: false, width: 0},
        xaxis: {
            min: 0, max: 100, tickAmount: 10, title: {text: "Metascore (%)"},
            labels: {formatter: v => Math.round(v)}
        },
        yaxis: {
            min: 0, max: 100, tickAmount: 10,
            title: {text: "IMDb score (%)"}
        },
        grid: {borderColor: "#232a36"},
        legend: {position: "top"},
        tooltip: {custom: customTip, intersect: true, shared: false},
    }).render();
}
