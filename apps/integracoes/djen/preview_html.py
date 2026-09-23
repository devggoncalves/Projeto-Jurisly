from __future__ import annotations

import html
import re


_TAG_HTML = re.compile(
    r"<\s*(html|body|div|p|table|span|br|font|strong|em|b|i|u|a|ul|ol|li|h[1-6]|style|center)\b",
    re.IGNORECASE,
)


def preparar_preview_html_comunicacao(texto: str) -> str:
    """
    Monta um documento HTML para preview em iframe (estilo cliente de e-mail).
    Se o conteúdo for texto puro, escapa e envolve em <pre>.
    """
    bruto = (texto or "").strip()
    if not bruto:
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
            "<body style='margin:0;padding:16px;font-family:system-ui,sans-serif;"
            "color:#666;background:#fff'>Sem texto nesta comunicação.</body></html>"
        )

    estilo = (
        "html,body{margin:0;padding:0;background:#ffffff;color:#111111;}"
        "body{padding:20px;font-family:Georgia,'Times New Roman',serif;"
        "font-size:15px;line-height:1.55;}"
        "img,table{max-width:100%;}"
        "img{height:auto;}"
        "a{color:#1a56db;}"
    )

    if re.search(r"<\s*html\b", bruto, re.IGNORECASE):
        # Documento completo: injeta base de estilo claro se possível
        if re.search(r"<\s*head\b", bruto, re.IGNORECASE):
            return re.sub(
                r"(<\s*head[^>]*>)",
                rf"\1<meta charset='utf-8'><style>{estilo}</style>",
                bruto,
                count=1,
                flags=re.IGNORECASE,
            )
        return bruto

    if _TAG_HTML.search(bruto):
        corpo = bruto
    else:
        corpo = (
            "<pre style='margin:0;white-space:pre-wrap;word-wrap:break-word;"
            "font-family:Georgia,serif;font-size:15px;line-height:1.55'>"
            f"{html.escape(bruto)}"
            "</pre>"
        )

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{estilo}</style></head><body>{corpo}</body></html>"
    )
