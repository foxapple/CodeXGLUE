__author__ = 'bernardo'

def __addMeta(meta, text):
    text = text.replace("\n","<br />")
    return "<" + meta + ">" + text + "</" + meta + ">"



def bold(txt):
	txt = txt.replace("\n","<br />")
	return "<strong>"+txt+"</strong>"
def emphasized(txt):
	txt = txt.replace("\n","<br />")
	return "<em>"+txt+"</em>"

def p(txt):
    return __addMeta("p", txt)
def span(txt):
    return __addMeta("span", txt)

def b(txt):
    return __addMeta("b", txt)
def i(txt):
    return __addMeta("i", txt)

def small(text):
    return __addMeta("small", text)

#The HTML <mark> element defines marked or highlighted text:
def mark(text):
    return __addMeta("mark", text)

#The HTML <del> element defines deleted (removed) of text.
def deleted(txt):
    return __addMeta("del", txt)

#The HTML <ins> element defines inserted (added) text.
def ins(txt):
    return __addMeta("ins", txt)

#The HTML <sub> element defines subscripted text.
def sub(txt):
    return __addMeta("sub", txt)

#The HTML <sup> element defines superscripted text.
def sup(txt):
    return __addMeta("sup", txt)

def underline(txt):
	txt = txt.replace("\n","<br />")
	return "<u>"+txt+"</u>"
def link(txt,to,idd="",cssclass=""):
	txt = txt.replace("\n","<br />")
	return "<a href='"+to+"' id='"+idd+"' class='"+cssclass+"'>"+txt+"</a>"

def li(txt):
	txt = txt.replace("\n","<br />")
	return "<li>"+txt+"</li>"

def ol(txt):
    return __addMeta("ol", txt)

def ul(txt):
    return __addMeta("ul", txt)

def h(txt, level):
    return __addMeta("h" + str(level), txt)
def h1(txt):
    return __addMeta("h1", txt)
def h2(txt):
    return __addMeta("h2", txt)
def h3(txt):
    return __addMeta("h3", txt)