#!/usr/bin/env python3
"""Export each dashboard visualization, including its title, as a 3x PNG."""
import argparse
import math
import struct
from pathlib import Path

from playwright.sync_api import sync_playwright


def export_visualizations(output):
    root = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(
                viewport={"width": 1200, "height": 1000}, device_scale_factor=3
            )
            page.set_default_timeout(60_000)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto((root / "index.html").as_uri())
            page.add_style_tag(content="""
                [data-export] {
                    background: var(--bg);
                    padding: 24px;
                    margin: 0 auto;
                }
                [data-export] h2 { margin-top: 0; }
                [data-export] .card { margin-bottom: 0; }
                .view-more { display: none; }
            """)
            sections = page.locator("[data-export]")
            if not sections.count():
                raise RuntimeError("No exportable sections found in index.html")
            names = set()
            for section in sections.all():
                name = section.get_attribute("data-export")
                if not name or Path(name).name != name or name in names:
                    raise RuntimeError(f"Invalid or duplicate export name: {name!r}")
                names.add(name)
                if not section.locator("h2").count():
                    raise RuntimeError(f"Missing visualization title: {name}")
                widget = section.locator('div[id^="chart-"], #consensus-gallery')
                if widget.count():
                    widget.scroll_into_view_if_needed()
                    page.wait_for_function(
                        """id => {
                            const element = document.getElementById(id);
                            if (element.querySelector(".load-error")) {
                                throw new Error(element.textContent);
                            }
                            return element.dataset.rendered === "true";
                        }""",
                        arg=widget.get_attribute("id"),
                    )
                section.evaluate("""async element => {
                    const card = element.querySelector(".category-card");
                    if (card) {
                        const padding = parseFloat(getComputedStyle(element).paddingLeft) +
                            parseFloat(getComputedStyle(element).paddingRight);
                        element.style.maxWidth = `${card.offsetWidth + padding}px`;
                    }
                    await document.fonts.ready;
                    await Promise.all([...element.querySelectorAll("img")].map(image => {
                        image.loading = "eager";
                        return image.decode();
                    }));
                    await new Promise(resolve => requestAnimationFrame(() =>
                        requestAnimationFrame(resolve)));
                }""")
                load_errors = section.locator(".load-error").all_text_contents()
                if load_errors:
                    raise RuntimeError("\n".join(load_errors))
                if errors:
                    raise RuntimeError("\n".join(errors))
                path = output / f"{name}.png"
                image = section.screenshot(path=str(path), animations="disabled")
                width, height = struct.unpack(">II", image[16:24])
                bounds = section.bounding_box()
                assert width >= math.floor(bounds["width"] * 3), f"{name}: low-resolution width"
                assert height >= math.floor(bounds["height"] * 3), f"{name}: low-resolution height"
                print(f"{path}: {width} x {height}")
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("exports"),
        help="destination directory (default: exports/ in the current directory)",
    )
    export_visualizations(parser.parse_args().output)
