function showLoadError(element, error) {
    console.error(error);
    const message = document.createElement("p");
    message.className = "load-error";
    message.textContent = "Unable to load this view. Check your connection and reload the page.";
    element.appendChild(message);
}

const views = new Map([
    ["chart-year-by-year", {key: "yearByYear", render: yearByYearChart}],
    ["chart-plotted", {key: "plotted", render: plotted}],
    ["chart-genre", {
        key: "genres", render: data =>
            categoryChart("#chart-genre", data)
    }],
    ["chart-decade", {
        key: "decades", render: data =>
            categoryChart("#chart-decade", data)
    }],
    ["consensus-gallery", {key: "consensus", render: consensusGallery}],
]);

const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        const view = views.get(entry.target.id);
        Promise.resolve().then(() => view.render(dashboardData[view.key]))
            .catch(error => showLoadError(entry.target, error));
    }
}, {rootMargin: "150px"});

document.addEventListener("DOMContentLoaded", () => {
    try {
        if (!window.dashboardData) throw new Error("Unable to load js/data.js");
        buildTable("#table-pos", "Metacritic > IMDb", RED,
            dashboardData.tables.pos.map(index => dashboardData.movies[index]));
        buildTable("#table-neg", "IMDb > Metacritic", BLUE,
            dashboardData.tables.neg.map(index => dashboardData.movies[index]));
        for (const id of views.keys()) {
            observer.observe(document.getElementById(id));
        }
    } catch (error) {
        showLoadError(document.getElementById("table-pos"), error);
    }
});
