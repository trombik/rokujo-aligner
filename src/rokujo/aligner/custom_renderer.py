from marko.renderer import Renderer


class CustomRenderer(Renderer):
    def render_raw_text(self, element):
        return element.children

    def render_line_break(self, element):
        return ""

    def render_code_span(self, element):
        return element.children

    def render_fenced_code(self, element):
        return " "

    def render_code_block(self, element):
        return " "

    def render_children(self, element):
        if isinstance(element.children, str):
            return element.children
        return "".join(self.render(child) for child in element.children)
