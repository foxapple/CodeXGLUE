import unittest
import zen

class FlowTestCase(unittest.TestCase):
	
	def test_min_cut(self):
		#sample graph
		G = zen.DiGraph()
		G.add_node('a')
		G.add_node('b')
		G.add_node('c')
		G.add_node('d')
		G.add_node('e')
		G.add_node('f')
		G.add_node('g')
		G.add_node('h')
		G.add_edge('a','b',weight=10)
		G.add_edge('a','c',weight=5)
		G.add_edge('a','d',weight=15)
		G.add_edge('b','e',weight=9)
		G.add_edge('b','f',weight=15)
		G.add_edge('b','c',weight=4)
		G.add_edge('c','f',weight=8)
		G.add_edge('c','d',weight=4)
		G.add_edge('d','g',weight=30)
		G.add_edge('g','c',weight=6)
		G.add_edge('e','f',weight=15)
		G.add_edge('e','h',weight=10)
		G.add_edge('f','g',weight=15)
		G.add_edge('f','h',weight=10)
		G.add_edge('g','h',weight=10)

		self.assertEquals(28, zen.min_cut(G,'a','h','weight'))
		self.assertEquals(3, zen.min_cut(G,'a','h','unit'))

		G.set_weight('d','g', float('inf'))
		
		self.assertEquals(28, zen.min_cut_(G,0,7,'weight'))
		self.assertEquals(3, zen.min_cut_(G,0,7,'unit'))
		
		G.set_weight('a','c', float('inf'))
		G.set_weight('c','f', float('inf'))
		G.set_weight('f','h', float('inf'))
		self.assertEquals(float('inf'), zen.min_cut(G,'a','h','weight'))
		self.assertEquals(3, zen.min_cut(G,'a','h','unit'))	

	def test_min_cut_(self):
		#sample graph
		G = zen.DiGraph()
		G.add_node('a')
		G.add_node('b')
		G.add_node('c')
		G.add_node('d')
		G.add_node('e')
		G.add_node('f')
		G.add_node('g')
		G.add_node('h')
		G.add_edge('a','b',weight=10)
		G.add_edge('a','c',weight=5)
		G.add_edge('a','d',weight=15)
		G.add_edge('b','e',weight=9)
		G.add_edge('b','f',weight=15)
		G.add_edge('b','c',weight=4)
		G.add_edge('c','f',weight=8)
		G.add_edge('c','d',weight=4)
		G.add_edge('d','g',weight=30)
		G.add_edge('g','c',weight=6)
		G.add_edge('e','f',weight=15)
		G.add_edge('e','h',weight=10)
		G.add_edge('f','g',weight=15)
		G.add_edge('f','h',weight=10)
		G.add_edge('g','h',weight=10)

		self.assertEquals(28, zen.min_cut_(G,0,7,'weight'))
		self.assertEquals(3, zen.min_cut_(G,0,7,'unit'))
		
		G.set_weight('d','g', float('inf'))
		
		self.assertEquals(28, zen.min_cut_(G,0,7,'weight'))
		self.assertEquals(3, zen.min_cut_(G,0,7,'unit'))
	
		G.set_weight('a','c', float('inf'))
		G.set_weight('c','f', float('inf'))
		G.set_weight('f','h', float('inf'))
		self.assertEquals(float('inf'), zen.min_cut(G,'a','h','weight'))
		self.assertEquals(3, zen.min_cut(G,'a','h','unit'))	

	def test_min_cut_set(self):
		#sample graph
		G = zen.DiGraph()
		G.add_node('a')
		G.add_node('b')
		G.add_node('c')
		G.add_node('d')
		G.add_node('e')
		G.add_node('f')
		G.add_node('g')
		G.add_node('h')
		G.add_edge('a','b',weight=10)
		G.add_edge('a','c',weight=5)
		G.add_edge('a','d',weight=15)
		G.add_edge('b','e',weight=9)
		G.add_edge('b','f',weight=15)
		G.add_edge('b','c',weight=4)
		G.add_edge('c','f',weight=8)
		G.add_edge('c','d',weight=4)
		G.add_edge('d','g',weight=30)
		G.add_edge('g','c',weight=6)
		G.add_edge('e','f',weight=15)
		G.add_edge('e','h',weight=10)
		G.add_edge('f','g',weight=15)
		G.add_edge('f','h',weight=10)
		G.add_edge('g','h',weight=10)

		cut_set = zen.min_cut_set(G,'a','h','weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('c','f') in cut_set)
		self.assertTrue(('g','h') in cut_set)

		cut_set = zen.min_cut_set(G,'a','h','unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('a','c') in cut_set)
		self.assertTrue(('a','d') in cut_set)

		G.set_weight('d','g', float('inf'))

		cut_set = zen.min_cut_set(G,'a','h','weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('c','f') in cut_set)
		self.assertTrue(('g','h') in cut_set)

		cut_set = zen.min_cut_set(G,'a','h','unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('a','c') in cut_set)
		self.assertTrue(('a','d') in cut_set)
	
		G.set_weight('a','c', float('inf'))
		G.set_weight('c','f', float('inf'))
		G.set_weight('f','h', float('inf'))

		cut_set = zen.min_cut_set(G,'a','h','weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('a','c') in cut_set)
		self.assertTrue(('a','d') in cut_set)

		cut_set = zen.min_cut_set(G,'a','h','unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(('a','b') in cut_set)
		self.assertTrue(('a','c') in cut_set)
		self.assertTrue(('a','d') in cut_set)


	def test_min_cut_set_(self):
		#sample graph
		G = zen.DiGraph()
		G.add_node('a')		#node 0
		G.add_node('b')
		G.add_node('c')
		G.add_node('d')		
		G.add_node('e')		#node 4
		G.add_node('f')
		G.add_node('g')
		G.add_node('h')		#node 7
		G.add_edge('a','b',weight=10)	#edge 0
		G.add_edge('a','c',weight=5)
		G.add_edge('a','d',weight=15)
		G.add_edge('b','e',weight=9)
		G.add_edge('b','f',weight=15)
		G.add_edge('b','c',weight=4)	#edge 5
		G.add_edge('c','f',weight=8)
		G.add_edge('c','d',weight=4)
		G.add_edge('d','g',weight=30)
		G.add_edge('g','c',weight=6)
		G.add_edge('e','f',weight=15)	#edge 10
		G.add_edge('e','h',weight=10)
		G.add_edge('f','g',weight=15)
		G.add_edge('f','h',weight=10)
		G.add_edge('g','h',weight=10)	#edge 14

		cut_set = zen.min_cut_set_(G,0,7,'weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(6 in cut_set)
		self.assertTrue(14 in cut_set)

		cut_set = zen.min_cut_set_(G,0,7,'unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(1 in cut_set)
		self.assertTrue(2 in cut_set)

		G.set_weight('d','g', float('inf'))

		cut_set = zen.min_cut_set_(G,0,7,'weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(6 in cut_set)
		self.assertTrue(14 in cut_set)

		cut_set = zen.min_cut_set_(G,0,7,'unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(1 in cut_set)
		self.assertTrue(2 in cut_set)
	
		G.set_weight('a','c', float('inf'))
		G.set_weight('c','f', float('inf'))
		G.set_weight('f','h', float('inf'))

		cut_set = zen.min_cut_set_(G,0,7,'weight')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(1 in cut_set)
		self.assertTrue(2 in cut_set)

		cut_set = zen.min_cut_set_(G,0,7,'unit')
		self.assertEquals(3, len(cut_set))
		self.assertTrue(0 in cut_set)
		self.assertTrue(1 in cut_set)
		self.assertTrue(2 in cut_set)


if __name__ == '__main__':
	unittest.main()
