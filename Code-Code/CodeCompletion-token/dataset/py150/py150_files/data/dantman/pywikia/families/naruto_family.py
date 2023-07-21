# -*- coding: utf-8  -*-
import family, wikia_basefamily

# The Narutopedia. (naruto.wikia.com)

class Family(wikia_basefamily.Family):

	def __init__(self):
		
		wikia_basefamily.Family.__init__(self)
		
		self.name               = 'naruto'
		self.langs              = { 'en': u'naruto.wikia.com', }
		self.wikia['projectns'] = 'Narutopedia'
		self.wikia['smw']       = True
		
		wikia_basefamily.Family.initNamespaces(self)
		