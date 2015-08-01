import CommonMark


def render_markdown(text):
    parser = CommonMark.DocParser()
    renderer = CommonMark.HTMLRenderer()
    ast = parser.parse(text)
    rendered = renderer.render(ast)
    # print 'In:', text
    # print ''
    # print 'Out:', rendered
    return rendered
