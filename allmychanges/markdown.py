import CommonMark


def render_markdown(text):
    parser = CommonMark.DocParser()
    renderer = CommonMark.HTMLRenderer()
    ast = parser.parse(text)
    return renderer.render(ast)
