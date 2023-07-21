from shakespeare.lib.base import *

class TemplateController(BaseController):
    def view(self, url):
        """By default, the final controller tried to fulfill the request
        when no other routes match. It may be used to display a template
        when all else fails, e.g.::

            def view(self, url):
                return render('/%s' % url)

        Or if you're using Mako and want to explicitly send a 404 (Not
        Found) response code when the requested template doesn't exist::

            import mako.exceptions

            def view(self, url):
                try:
                    return render('/%s' % url)
                except mako.exceptions.TopLevelLookupException:
                    abort(404)

        By default this controller aborts the request with a 404 (Not
        Found)
        """
        # abort(404)
        return self._proxy()

    def _proxy(self):
        if g.deliverance_enabled:
            # wordpress requires trailing '/' (o/w get redirect)
            if not request.environ['PATH_INFO'].endswith('/'):
                request.environ['PATH_INFO'] = request.environ['PATH_INFO'] + '/'
            return self.deliverance(request.environ, self.start_response)
        else:
            return 'hello world'
            abort(404)

    deliverance_rules = \
'''<ruleset>
  <theme href="%s" />
  <!-- These are the default rules for anything with class="default" or no class: -->
  <!-- suppress standard behaviour of copying over head stuff links, html, css
  etc
  <rule suppress-standard="1"> 
  -->
  <rule>
      <replace content="children:/html/head/title" theme="children:/html/head/title" nocontent="ignore" />

    <replace content="children:#content" theme="children:#content" />
    <append content="children:#primary .xoxo" theme="children:#primary .xoxo" />
  </rule>
</ruleset>
'''
    
    @property
    def deliverance(self):
        from datautil.deliveranceproxy import create_deliverance_proxy
        # where we are proxying from
        proxy_base_url = config['deliverance.dest']
        theme_html = render('index.html')
        if not hasattr(self, '_deliverance'):
            self._deliverance = create_deliverance_proxy(proxy_base_url,
                    theme_html, rules_xml=self.deliverance_rules)
            # self._deliverance = create_deliverance_proxy()
        return self._deliverance

