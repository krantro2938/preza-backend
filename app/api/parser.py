import zipfile
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath
import json

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
EMU_PER_INCH = 914400
DPI = 96

MAIN_PH_TYPES = {
    "title", "ctrTitle", "subTitle",
    "body", "obj", "pic", "tbl", "chart", "clipArt", "dgm", "media"
}


def _q(name: str) -> str:
    pfx, local = name.split(":")
    return f"{{{NS[pfx]}}}{local}"


def _read_xml(zf: zipfile.ZipFile, path: str) -> ET.Element | None:
    try:
        with zf.open(path) as f:
            return ET.fromstring(f.read())
    except KeyError:
        return None


def _resolve_rel_target(base_path: str, target: str) -> str:
    base = PurePosixPath(base_path)
    if not base.name.endswith(".rels"):
        base = base.parent / "_rels" / (base.name + ".rels")
    base_dir = base.parent
    full = (base_dir / target).resolve()
    parts = []
    for p in full.parts:
        if p == "..":
            if parts:
                parts.pop()
        elif p != ".":
            parts.append(p)
    norm = PurePosixPath(*parts)
    if "ppt" in norm.parts:
        idx = norm.parts.index("ppt")
        norm = PurePosixPath(*norm.parts[idx:])
    return str(norm)


def _parse_presentation_size(zf: zipfile.ZipFile) -> dict:
    pres = _read_xml(zf, "ppt/presentation.xml")
    if pres is None:
        return {}
    sldSz = pres.find(_q("p:sldSz"))
    if sldSz is None:
        return {}
    cx = int(sldSz.get("cx"))
    cy = int(sldSz.get("cy"))

    def emu_to_px(v):
        return round((v / EMU_PER_INCH) * DPI)

    return {
        "widthEMU": cx, "heightEMU": cy,
        "widthPx96": emu_to_px(cx), "heightPx96": emu_to_px(cy)
    }


def _parse_theme_palette(zf: zipfile.ZipFile) -> dict | None:
    theme_paths = sorted([p for p in zf.namelist() if p.startswith("ppt/theme/") and p.endswith(".xml")])
    if not theme_paths:
        return None
    root = _read_xml(zf, theme_paths[0])
    if root is None:
        return None
    cs = root.find(".//" + _q("a:clrScheme"))
    if cs is None:
        return None
    palette = {"name": cs.get("name")}
    for node in list(cs):
        key = node.tag.split('}')[-1]
        rgb = node.find(_q("a:srgbClr"))
        if rgb is not None:
            palette[key] = "#" + rgb.get("val", "").upper()
        else:
            sc = node.find(_q("a:schemeClr"))
            pr = node.find(_q("a:prstClr"))
            if sc is not None:
                palette[key] = {"scheme": sc.get("val")}
            elif pr is not None:
                palette[key] = {"preset": pr.get("val")}
            else:
                palette[key] = None
    return palette


def _parse_font_scheme(zf: zipfile.ZipFile) -> dict | None:
    theme_paths = sorted([p for p in zf.namelist() if p.startswith("ppt/theme/") and p.endswith(".xml")])
    if not theme_paths:
        return None
    root = _read_xml(zf, theme_paths[0])
    if root is None:
        return None
    fs = root.find(".//" + _q("a:fontScheme"))
    if fs is None:
        return None

    def branch(tag):
        b = fs.find(_q(tag))
        if b is None:
            return None
        out = {
            "latin": (b.find(_q("a:latin")) or {}).get("typeface") if b.find(_q("a:latin")) is not None else None,
            "eastAsian": (b.find(_q("a:ea")) or {}).get("typeface") if b.find(_q("a:ea")) is not None else None,
            "complexScript": (b.find(_q("a:cs")) or {}).get("typeface") if b.find(_q("a:cs")) is not None else None,
            "supplemental": []
        }
        for f in b.findall(_q("a:font")):
            out["supplemental"].append({"script": f.get("script"), "typeface": f.get("typeface")})
        return out

    return {
        "name": fs.get("name"),
        "major": branch("a:majorFont"),
        "minor": branch("a:minorFont"),
    }


def _read_rels(zf: zipfile.ZipFile, xml_path: str) -> dict[str, str]:
    rels_path = str(PurePosixPath(xml_path).parent / "_rels" / (PurePosixPath(xml_path).name + ".rels"))
    rels_xml = _read_xml(zf, rels_path)
    mapping = {}
    if rels_xml is None:
        return mapping
    for rel in rels_xml.findall(_q("r:Relationship")):
        rid, tgt = rel.get("Id"), rel.get("Target")
        if rid and tgt:
            mapping[rid] = _resolve_rel_target(rels_path, tgt)
    return mapping


def _xfrm(el: ET.Element | None) -> dict | None:
    if el is None:
        return None
    x = el.find(_q("a:xfrm"))
    if x is None:
        return None
    off, ext = x.find(_q("a:off")), x.find(_q("a:ext"))
    return {
        "xEMU": int(off.get("x")) if off is not None and off.get("x") else None,
        "yEMU": int(off.get("y")) if off is not None and off.get("y") else None,
        "cxEMU": int(ext.get("cx")) if ext is not None and ext.get("cx") else None,
        "cyEMU": int(ext.get("cy")) if ext is not None and ext.get("cy") else None,
    }


def _parse_layout_placeholders(zf: zipfile.ZipFile, layout_path: str, slide_w: int, slide_h: int) -> dict:
    root = _read_xml(zf, layout_path)
    if root is None:
        return {"path": layout_path, "error": "missing"}
    cSld = root.find(_q("p:cSld"))
    spTree = cSld.find(_q("p:spTree")) if cSld is not None else None
    items = []
    if spTree is not None:
        for sp in spTree.findall(_q("p:sp")):
            nvSpPr = sp.find(_q("p:nvSpPr"))
            if nvSpPr is None:
                continue
            ph = nvSpPr.find(_q("p:nvPr")).find(_q("p:ph")) if nvSpPr.find(_q("p:nvPr")) is not None else None
            if ph is None:
                continue
            ph_type = ph.get("type")
            if ph_type is None and nvSpPr.find(_q("p:cNvPr")) is not None:
                ph_type = "body"
            if ph_type not in MAIN_PH_TYPES:
                continue
            name = nvSpPr.find(_q("p:cNvPr")).get("name") if nvSpPr.find(_q("p:cNvPr")) is not None else None
            xf = _xfrm(sp.find(_q("p:spPr")))
            if xf is None:
                continue

            def emu_to_px(v):
                return round((v / EMU_PER_INCH) * DPI) if v is not None else None

            def pct(val, total):
                return round((val / total) * 100, 2) if val is not None and total else None

            items.append({
                "name": name,
                "type": ph_type,
                "idx": int(ph.get("idx")) if ph.get("idx") else None,
                "position": {
                    "xEMU": xf["xEMU"], "yEMU": xf["yEMU"], "wEMU": xf["cxEMU"], "hEMU": xf["cyEMU"],
                    "xPx96": emu_to_px(xf["xEMU"]), "yPx96": emu_to_px(xf["yEMU"]),
                    "wPx96": emu_to_px(xf["cxEMU"]), "hPx96": emu_to_px(xf["cyEMU"]),
                    "xPct": pct(xf["xEMU"], slide_w), "yPct": pct(xf["yEMU"], slide_h),
                    "wPct": pct(xf["cxEMU"], slide_w), "hPct": pct(xf["cyEMU"], slide_h),
                }
            })
    return {
        "path": layout_path,
        "type": root.get("type"),
        "matchingName": root.get("matchingName"),
        "placeholders": items
    }


def parse_pptx_style_core(pptx_path: str) -> dict:
    with zipfile.ZipFile(pptx_path, "r") as zf:
        slide_size = _parse_presentation_size(zf)
        palette = _parse_theme_palette(zf)
        fonts = _parse_font_scheme(zf)

        master_paths = sorted([p for p in zf.namelist() if p.startswith("ppt/slideMasters/") and p.endswith(".xml")])
        layouts = []
        for mp in master_paths:
            rels = _read_rels(zf, mp)
            master = _read_xml(zf, mp)
            if master is None:
                continue
            idlst = master.find(_q("p:sldLayoutIdLst"))
            ordered = []
            if idlst is not None:
                for it in idlst.findall(_q("p:sldLayoutId")):
                    rid = it.get(_q("r:id"))
                    if rid and rid in rels:
                        ordered.append(rels[rid])
            else:
                ordered = [t for t in rels.values() if t.startswith("ppt/slideLayouts/")]
            for lp in ordered:
                layouts.append(_parse_layout_placeholders(
                    zf, lp,
                    slide_size.get("widthEMU"), slide_size.get("heightEXLMU"))
                )

        return {
            "palette": palette,
            "fonts": fonts,
            "slideSize": slide_size,
            "layouts": layouts,
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <file.pptx>")
        raise SystemExit(1)
    data = parse_pptx_style_core(sys.argv[1])
    print(json.dumps(data, ensure_ascii=False, indent=2))
