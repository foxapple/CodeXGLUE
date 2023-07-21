import aspen_jinja2_renderer as base

from markupsafe import escape as htmlescape


class HTMLRenderer(base.Renderer):
    def render_content(self, context):

        # Extend to inject an HTML-escaping function. Since autoescape is on,
        # template authors shouldn't normally need to use this function, but
        # having it in the simplate context makes it easier to implement i18n.

        context['state']['escape'] = context['escape'] = htmlescape

        return base.Renderer.render_content(self, context)


class Factory(base.Factory):

    Renderer = HTMLRenderer

    def compile_meta(self, configuration):
        # Override to turn on autoescaping.
        loader = base.FileSystemLoader(configuration.project_root)
        return base.Environment( loader=loader
                               , autoescape=True
                               , extensions=['jinja2.ext.autoescape']
                                )
