frontend.page("services", expect={ "document_title": testing.expect.document_title(u"Services"),
                                   "content_title": testing.expect.paleyellow_title(0, u"Services"),
                                   "pageheader_links": testing.expect.pageheader_links("anonymous"),
                                   "script_user": testing.expect.script_anonymous_user() })
