#!/usr/bin/env python3
"""Branded preview cards for projects that have no screenshot in the README.

Writes assets/cards/*.svg (520x300). These are illustrations, labelled as such in the README.
"""
from html import escape as esc
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "cards"
FONT = "font-family=\"'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif\""


def frame(title, sub, accent, chips, art):
    chip_svg, x = [], 28
    for c in chips:
        w = 20 + len(c) * 7.0
        chip_svg.append(f'<rect x="{x}" y="250" width="{w:.0f}" height="24" rx="12" fill="{accent}" fill-opacity=".16" stroke="{accent}" stroke-opacity=".5"/>'
                        f'<text x="{x + w / 2:.0f}" y="266" fill="#e2e8f0" font-size="11.5" font-weight="600" text-anchor="middle">{esc(c)}</text>')
        x += w + 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="300" viewBox="0 0 520 300" {FONT} role="img"><title>{esc(title)}</title>'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/><stop offset="1" stop-color="#131d33"/></linearGradient>'
            f'<radialGradient id="r" cx=".85" cy=".2" r=".7"><stop offset="0" stop-color="{accent}" stop-opacity=".28"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="520" height="300" rx="18" fill="url(#g)"/><rect width="520" height="300" rx="18" fill="url(#r)"/>'
            f'<rect x=".5" y=".5" width="519" height="299" rx="17.5" fill="none" stroke="#22304a"/>'
            f'<rect x="28" y="30" width="34" height="4" rx="2" fill="{accent}"/>'
            f'<text x="28" y="62" fill="#f8fafc" font-size="22" font-weight="800">{esc(title)}</text>'
            f'<text x="28" y="84" fill="#a7b4c8" font-size="13">{esc(sub)}</text>'
            f'{art}{"".join(chip_svg)}</svg>')


def drain():
    a = "#22d3ee"
    pipes = "".join(f'<path d="{d}" stroke="{a}" stroke-width="3" fill="none" stroke-linecap="round" opacity="{o}"/>' for d, o in [
        ("M300 120 L360 150 L420 140 L480 175", 1), ("M360 150 L370 205 L440 225", .8), ("M300 120 L320 190 L370 205", .6), ("M420 140 L455 110", .6)])
    nodes = "".join(f'<circle cx="{x}" cy="{y}" r="6" fill="#0b1220" stroke="{a}" stroke-width="2.5"/>' for x, y in [(300, 120), (360, 150), (420, 140), (480, 175), (370, 205), (440, 225), (320, 190), (455, 110)])
    alert = '<circle cx="370" cy="205" r="14" fill="#ef4444" fill-opacity=".25"/><circle cx="370" cy="205" r="6" fill="#ef4444"/>'
    water = '<path d="M28 205 q20 -12 40 0 t40 0 t40 0 t40 0" stroke="#3987e5" stroke-width="2.5" fill="none" opacity=".7"/><path d="M28 222 q20 -12 40 0 t40 0 t40 0 t40 0" stroke="#3987e5" stroke-width="2.5" fill="none" opacity=".45"/>'
    stat = '<text x="28" y="130" fill="#e2e8f0" font-size="30" font-weight="800">Drain</text><text x="28" y="162" fill="#22d3ee" font-size="30" font-weight="800">FloodOps</text>'
    return frame("GeoSentinel Drain FloodOps", "Drainage network · flood operations workspace", a, ["Web GIS", "Flood intelligence", "Work orders"], pipes + alert + nodes + water + stat)


def flood():
    a = "#3987e5"
    # stylised district markers on an abstract country outline
    outline = '<path d="M318 228 L300 196 L316 170 L340 160 L352 128 L384 112 L410 120 L428 98 L462 104 L470 132 L448 158 L452 186 L420 206 L392 214 L360 232 Z" fill="#3987e5" fill-opacity=".10" stroke="#3987e5" stroke-opacity=".6" stroke-width="2"/>'
    river = '<path d="M440 108 C420 140 400 150 390 175 S360 210 330 222" stroke="#22d3ee" stroke-width="2.5" fill="none"/>'
    pts = [(372, 150, "#ef4444"), (398, 170, "#f59e0b"), (352, 190, "#ef4444"), (420, 150, "#22c55e"), (380, 200, "#f59e0b"), (430, 182, "#22c55e"), (338, 214, "#f59e0b")]
    marks = "".join(f'<circle cx="{x}" cy="{y}" r="6.5" fill="{c}" stroke="#0b1220" stroke-width="2"/>' for x, y, c in pts)
    stats = ('<text x="28" y="132" fill="#f8fafc" font-size="34" font-weight="800">35</text><text x="80" y="132" fill="#a7b4c8" font-size="13">priority districts</text>'
             '<text x="28" y="174" fill="#f8fafc" font-size="34" font-weight="800">5</text><text x="56" y="174" fill="#a7b4c8" font-size="13">scenarios</text>'
             '<text x="28" y="216" fill="#f8fafc" font-size="34" font-weight="800">4</text><text x="56" y="216" fill="#a7b4c8" font-size="13">response phases</text>')
    return frame("Pakistan National Flood Intelligence", "District screening · scenario views · response phases", a, ["React", "TypeScript", "GeoJSON"], outline + river + marks + stats)


def bill():
    a = "#d55181"
    rec = ('<g transform="translate(320 104)"><path d="M0 0 H150 V140 l-12.5 8 -12.5 -8 -12.5 8 -12.5 -8 -12.5 8 -12.5 -8 -12.5 8 -12.5 -8 -12.5 8 -12.5 -8 -12.5 8 -12.5 -8 Z" fill="#f8fafc" fill-opacity=".95"/>'
           '<rect x="14" y="14" width="70" height="8" rx="4" fill="#334155"/><rect x="14" y="30" width="44" height="6" rx="3" fill="#94a3b8"/>'
           + "".join(f'<rect x="14" y="{52 + i * 16}" width="{80 - i * 8}" height="6" rx="3" fill="#94a3b8"/><rect x="112" y="{52 + i * 16}" width="24" height="6" rx="3" fill="#64748b"/>' for i in range(4))
           + '<rect x="14" y="120" width="40" height="8" rx="4" fill="#334155"/><rect x="100" y="120" width="36" height="8" rx="4" fill="#d55181"/></g>'
           '<rect x="306" y="150" width="178" height="3" fill="#d55181"><animate attributeName="y" values="112;236;112" dur="3.2s" repeatCount="indefinite"/></rect>')
    fields = "".join(f'<text x="28" y="{122 + i * 26}" fill="#a7b4c8" font-size="13.5">› <tspan fill="#f1f5f9" font-weight="700">{k}</tspan> {v}</text>' for i, (k, v) in enumerate(
        [("Vendor", "&amp; invoice no."), ("Currency", "PKR · SAR · AED · USD"), ("Totals", "subtotal · tax · total"), ("Line items", "→ CSV export")]))
    return frame("Zarwa / HIS Bill Scanner", "Browser OCR · review · structured CSV", a, ["Tesseract.js", "PDF.js", "Privacy-first"], rec + fields)


def mep():
    a = "#9085e9"
    duct = ('<g stroke="#9085e9" stroke-width="2" fill="#9085e9" fill-opacity=".10">'
            '<rect x="300" y="120" width="180" height="26" rx="3"/><rect x="380" y="146" width="26" height="80" rx="3"/><rect x="300" y="196" width="80" height="22" rx="3"/></g>'
            + "".join(f'<path d="M{x} 112 l6 -8 l6 8" stroke="#22d3ee" stroke-width="2" fill="none"/>' for x in (318, 358, 438))
            + '<rect x="412" y="160" width="84" height="20" rx="4" fill="#0b1220" stroke="#f59e0b"/><text x="454" y="174" fill="#f59e0b" font-size="10.5" font-weight="700" text-anchor="middle">SAD 600×300</text>'
            '<rect x="300" y="226" width="76" height="18" rx="4" fill="#0b1220" stroke="#22c55e"/><text x="338" y="239" fill="#22c55e" font-size="10.5" font-weight="700" text-anchor="middle">conf 94%</text>')
    schema = "".join(f'<text x="28" y="{120 + i * 22}" fill="#a7b4c8" font-size="13" font-family="Consolas,monospace" xml:space="preserve">{t}</text>' for i, t in enumerate(
        ["ScanRecord {", "  component · tag", "  duct_size_mm", "  airflow · unit", "  confidence_pct }"]))
    return frame("MEP Scanner System", "Drawing OCR → components, ducts & airflow", a, ["EasyOCR", "OpenCV", "Python"], duct + schema)


def mentor():
    a = "#c98500"
    bubbles = ('<rect x="292" y="104" width="200" height="40" rx="14" fill="#3987e5" fill-opacity=".22" stroke="#3987e5" stroke-opacity=".6"/>'
               '<text x="306" y="129" fill="#e2e8f0" font-size="12">Explain RAG vs fine-tuning…</text>'
               '<rect x="330" y="154" width="160" height="40" rx="14" fill="#c98500" fill-opacity=".22" stroke="#c98500" stroke-opacity=".6"/>'
               '<text x="344" y="179" fill="#e2e8f0" font-size="12">Good — add a trade-off.</text>'
               '<rect x="300" y="204" width="120" height="30" rx="12" fill="#22c55e" fill-opacity=".18" stroke="#22c55e" stroke-opacity=".6"/>'
               '<text x="314" y="224" fill="#e2e8f0" font-size="12">Score 8.5 / 10</text>')
    agents = "".join(f'<circle cx="{40 + i * 30}" cy="128" r="11.5" fill="{c}" fill-opacity=".85"/>' for i, c in enumerate(["#3987e5", "#199e70", "#c98500", "#d55181", "#9085e9", "#e66767", "#f59e0b"]))
    txt = '<text x="28" y="172" fill="#f8fafc" font-size="15" font-weight="700">6 agents + confidence coach</text><text x="28" y="194" fill="#a7b4c8" font-size="12.5">Chat · voice · video calls · 3D interviewer</text><text x="28" y="212" fill="#a7b4c8" font-size="12.5">10-category scorecard · 90-day roadmap</text>'
    return frame("AI Career Mentor", "AI interviewer, English & confidence coach", a, ["Multi-agent", "Claude / OpenAI", "65 tests"], bubbles + agents + txt)


def langchain():
    a = "#199e70"
    docs = "".join(f'<g transform="translate({300 + i * 18} {104 + i * 12})"><rect width="70" height="88" rx="6" fill="#f8fafc" fill-opacity="{.95 - i * .2}"/>'
                   + "".join(f'<rect x="10" y="{14 + j * 12}" width="{50 - (j % 2) * 14}" height="5" rx="2.5" fill="#94a3b8"/>' for j in range(5)) + '</g>' for i in range(3))
    flow = ('<path d="M410 150 h22" stroke="#199e70" stroke-width="2.5" marker-end="url(#ah)"/>'
            '<g transform="translate(436 118)"><rect width="56" height="64" rx="8" fill="#199e70" fill-opacity=".18" stroke="#199e70"/>'
            + "".join(f'<rect x="10" y="{12 + j * 13}" width="36" height="7" rx="3.5" fill="#199e70" fill-opacity="{.9 - j * .2}"/>' for j in range(4))
            + '<text x="28" y="80" fill="#a7b4c8" font-size="10" text-anchor="middle">vectors</text></g>'
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="#199e70"/></marker></defs>')
    steps = "".join(f'<text x="28" y="{122 + i * 24}" fill="#a7b4c8" font-size="13.5"><tspan fill="{a}" font-weight="800">{i + 1}</tspan>  {t}</text>' for i, t in enumerate(
        ["Load &amp; chunk documents", "Embed with OpenAI", "Store in SingleStore", "Retrieve + cite sources"]))
    return frame("LangChain RAG Assistant", "Document Q&A with vector retrieval", a, ["LangChain", "OpenAI", "SingleStore"], docs + flow + steps)


def healthassist_v1():
    a = "#14b8a6"
    heart = ('<g transform="translate(330 96) scale(2.4)"><rect width="64" height="64" rx="19" fill="#087f83"/>'
             '<path d="M32 49C10 36 14 17 25 19c4 0 7 4 7 4s3-4 7-4c11-2 15 17-7 30Z" fill="#e4faf3"/>'
             '<path d="M15 32h11l3-7 6 15 4-8h10" fill="none" stroke="#087f83" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></g>')
    items = "".join(f'<text x="28" y="{124 + i * 24}" fill="#a7b4c8" font-size="13.5">› <tspan fill="#f1f5f9" font-weight="700">{k}</tspan> {v}</text>' for i, (k, v) in enumerate(
        [("Intake", "guided symptom form"), ("Vitals", "recorded readings"), ("Health GIS", "facility map prototype"), ("v2", "→ HealthAssist agentic platform")]))
    return frame("AI HealthAssist · v1", "Educational health intake prototype", a, ["TypeScript", "Health GIS", "Predecessor of v2"], heart + items)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("drain-floodops", drain), ("pakistan-flood", flood), ("bill-scanner", bill), ("mep-scanner", mep), ("career-mentor", mentor), ("langchain-rag", langchain), ("healthassist-v1", healthassist_v1)]:
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
