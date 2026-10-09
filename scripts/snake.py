"""Contribution snake: dense recent weeks first, upcoming weeks after.

Usage: python3 scripts/snake.py contrib.json out_dir
contrib.json = GraphQL user.contributionsCollection.contributionCalendar
"""
import datetime as dt
import json
import sys

LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
THEMES = {
    "dark": {"cells": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"], "future": "#30363d",
             "text": "#8b949e", "now": "#d97757", "snake": "#d97757"},
    "light": {"cells": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"], "future": "#d1d9e0",
              "text": "#59636e", "now": "#d97757", "snake": "#d97757"},
}
TOTAL_WEEKS = 53
S, PAD, TOP = 12, 4, 18
DURATION = 16.0


def dense_start(weeks):
    """First week from which at least 60% of the remaining weeks are active."""
    active = [any(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    for i, a in enumerate(active):
        rest = active[i:]
        if a and sum(rest) / len(rest) >= 0.6:
            return i
    return 0


def build(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"][dense_start(cal["weeks"]):]
    future = TOTAL_WEEKS - len(weeks)
    width = PAD * 2 + TOTAL_WEEKS * S
    height = TOP + PAD + 7 * S + 12
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="-apple-system, Segoe UI, sans-serif" font-size="9">']

    # month labels across past and future
    first = dt.date.fromisoformat(weeks[0]["contributionDays"][0]["date"])
    last_month = None
    for i in range(TOTAL_WEEKS):
        day = first + dt.timedelta(weeks=i)
        if day.month != last_month and i < TOTAL_WEEKS - 2:
            out.append(f'<text x="{PAD + i * S}" y="11" fill="{t["text"]}">{day.strftime("%b")}</text>')
            last_month = day.month

    # past cells in serpentine order (the snake's path)
    order = []
    for i, w in enumerate(weeks):
        days = sorted(w["contributionDays"], key=lambda d: d["weekday"])
        if i % 2:
            days.reverse()
        order += [(i, d["weekday"], LEVEL[d["contributionLevel"]]) for d in days]
    n = len(order)
    for k, (i, wd, lv) in enumerate(order):
        x, y = PAD + i * S, TOP + wd * S
        color = t["cells"][lv]
        if lv == 0:
            out.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{color}"/>')
            continue
        p = k / n * 0.9
        q = p + 0.003
        empty = t["cells"][0]
        out.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{color}">'
                   f'<animate attributeName="fill" values="{color};{color};{empty};{empty};{color}" '
                   f'keyTimes="0;{p:.4f};{q:.4f};0.97;1" dur="{DURATION}s" repeatCount="indefinite"/></rect>')

    # future cells: outlined, waiting to be filled
    for i in range(len(weeks), TOTAL_WEEKS):
        for wd in range(7):
            out.append(f'<rect x="{PAD + i * S + 0.5}" y="{TOP + wd * S + 0.5}" width="9" height="9" rx="2" '
                       f'fill="none" stroke="{t["future"]}" stroke-dasharray="2 2"/>')

    # "now" divider
    nx = PAD + len(weeks) * S - 1
    out.append(f'<line x1="{nx}" y1="{TOP - 3}" x2="{nx}" y2="{TOP + 7 * S + 2}" stroke="{t["now"]}" stroke-width="1.5"/>')
    out.append(f'<text x="{nx - 3}" y="{TOP + 7 * S + 11}" fill="{t["text"]}" text-anchor="end">past</text>')
    out.append(f'<text x="{nx + 3}" y="{TOP + 7 * S + 11}" fill="{t["now"]}" font-weight="700">NOW → future</text>')

    # snake: eats the past within 90% of the loop, then rests at NOW
    path = "M" + " L".join(f"{PAD + i * S},{TOP + wd * S}" for i, wd, _ in order)
    step = DURATION * 0.9 / n
    for seg in range(5):
        size = 10 - seg * 1.2
        off = (10 - size) / 2
        out.append(f'<rect x="{off}" y="{off}" width="{size}" height="{size}" rx="3" fill="{t["snake"]}" '
                   f'opacity="{1 - seg * 0.12:.2f}"><animateMotion path="{path}" dur="{DURATION}s" '
                   f'begin="{-DURATION + seg * step:.3f}s" repeatCount="indefinite" '
                   f'keyPoints="0;1;1" keyTimes="0;0.9;1" calcMode="linear"/></rect>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    cal = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    for theme in THEMES:
        with open(f"{out_dir}/snake-{theme}.svg", "w") as f:
            f.write(build(cal, theme))
