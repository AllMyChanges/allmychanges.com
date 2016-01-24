import CommonMark


def render_markdown(text):
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(text)
    rendered = renderer.render(ast)
    # print 'In:', text
    # print ''
    # print 'Out:', rendered
    return rendered
