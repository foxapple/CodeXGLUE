frontend.page("tutorial",
              expect={ "document_title": testing.expect.document_title(u"Tutorials"),
                       "content_title": testing.expect.paleyellow_title(0, u"Tutorials"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "request" },
              expect={ "document_title": testing.expect.document_title(u"Requesting a Review"),
                       "content_title": testing.expect.paleyellow_title(0, u"Requesting a Review"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "review" },
              expect={ "document_title": testing.expect.document_title(u"Reviewing Changes"),
                       "content_title": testing.expect.paleyellow_title(0, u"Reviewing Changes"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "filters" },
              expect={ "document_title": testing.expect.document_title(u"Filters"),
                       "content_title": testing.expect.paleyellow_title(0, u"Filters"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "archival" },
              expect={ "document_title": testing.expect.document_title(u"Review branch archival"),
                       "content_title": testing.expect.paleyellow_title(0, u"Review branch archival"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "viewer" },
              expect={ "document_title": testing.expect.document_title(u"Repository Viewer"),
                       "content_title": testing.expect.paleyellow_title(0, u"Repository Viewer"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "reconfigure" },
              expect={ "document_title": testing.expect.document_title(u"Reconfiguring Critic"),
                       "content_title": testing.expect.paleyellow_title(0, u"Reconfiguring Critic"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "rebase" },
              expect={ "document_title": testing.expect.document_title(u"Rebasing a Review"),
                       "content_title": testing.expect.paleyellow_title(0, u"Rebasing a Review"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "administration" },
              expect={ "document_title": testing.expect.document_title(u"System Administration"),
                       "content_title": testing.expect.paleyellow_title(0, u"System Administration"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "customization" },
              expect={ "document_title": testing.expect.document_title(u"System Customization"),
                       "content_title": testing.expect.paleyellow_title(0, u"System Customization"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

frontend.page("tutorial",
              params={ "item": "search" },
              expect={ "document_title": testing.expect.document_title(u"Review Quick Search"),
                       "content_title": testing.expect.paleyellow_title(0, u"Review Quick Search"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })

# Unknown items are ignored and the main Tutorials page is returned instead.
frontend.page("tutorial",
              params={ "item": "nonexisting" },
              expect={ "document_title": testing.expect.document_title(u"Tutorials"),
                       "content_title": testing.expect.paleyellow_title(0, u"Tutorials"),
                       "pageheader_links": testing.expect.pageheader_links("anonymous"),
                       "script_user": testing.expect.script_no_user() })
