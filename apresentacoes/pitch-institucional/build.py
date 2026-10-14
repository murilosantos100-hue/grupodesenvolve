"""Gera o pitch institucional autocontido (assets embutidos em base64).

Uso:  python3 build.py [saida_fragmento]

- index.html: arquivo standalone (abre direto no navegador, também offline,
  exceto as fontes do Google, que caem para fontes do sistema).
- saida_fragmento (opcional): mesmo conteúdo sem <!doctype>/<head>/<body>,
  formato exigido para publicar como Artifact no claude.ai.
"""
import base64
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src" / "pitch.src.html"
ASSETS = ROOT / "assets"
MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".svg": "image/svg+xml"}


def logo_slot(m):
    """{{LOGO:arquivo|Nome}}: usa assets/logo-arquivo.(png|svg) se existir; senão, o nome em texto."""
    name, label = m.group(1), m.group(2)
    for ext in (".png", ".svg", ".webp"):
        if (ASSETS / f"logo-{name}{ext}").exists():
            return f'<img src="{{{{logo-{name}{ext}}}}}" alt="{label}">'
    return f'<span class="word">{label}</span>'


def embed(html: str) -> str:
    html = re.sub(r"\{\{LOGO:([\w-]+)\|([^}]+)\}\}", logo_slot, html)

    def repl(m):
        f = ASSETS / m.group(1)
        data = base64.b64encode(f.read_bytes()).decode()
        return f"data:{MIME[f.suffix]};base64,{data}"
    return re.sub(r"\{\{([\w.-]+)\}\}", repl, html)


def main():
    frag = embed(SRC.read_text(encoding="utf-8"))
    title, rest = frag.split("\n", 1)
    # fontes e estilo vão para o <head>; o restante (svg, slides, script) para o <body>
    head_part, body_part = rest.split("</style>", 1)
    page = (
        "<!doctype html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
        f"{title}\n{head_part}</style>\n</head>\n<body>{body_part}</body>\n</html>\n"
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html: {len(page) / 1024:.0f} KB")
    if len(sys.argv) > 1:
        out = pathlib.Path(sys.argv[1])
        out.write_text(frag, encoding="utf-8")
        print(f"{out}: {len(frag) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
