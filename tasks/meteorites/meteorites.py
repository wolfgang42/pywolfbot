# TODO use standard library
from sys import path as libpath
libpath.append('./lib/wikitools') # Location of library
libpath.append('./lib/mwparserfromhell')
libpath.append('.')
from wikitools import wiki, category, api
from conf import username, password
wikipedia = wiki.Wiki("http://en.wikipedia.org/w/api.php") 
wikipedia.login(username, password, True)

from wikitools.page import Page
from wikitools.page import namespaceDetect
from sys import stdout
import re
import codecs
import mwparserfromhell
import pickle
import time
astrolist=codecs.open('tasks/meteorites/astrolist.txt','a','utf-8')
imagelist=codecs.open('tasks/meteorites/imagelist.txt','a','utf-8')
def checkCategory(cat):
    if (cat in checkCategory.checkedCats):
        return
    checkCategory.checkedCats.append(cat)
    for article in category.Category(wikipedia, cat).getAllMembersGen(namespaces=[0]):
        print article.title
        stdout.write(article.title+": ")
        talk=article.toggleTalk()
        editSummary=[]
        if talk.exists:
            talkText=talk.getWikiText().decode('utf-8')
        else:
            talkText=u""
        if article.namespace == 14: # Category
            if not (talk.exists and "Template:WikiProject Geology" in talk.getTemplates()):
                talkText="{{WikiProject Geology|class=Cat}}\n\n"+talkText
                editSummary.append("Added {{WikiProject Geology}}")
                print "Adding {{WikiProject Geology}}"
            checkCategory(article.unprefixedtitle)
        elif article.namespace == 0: # Article
            if (article.unprefixedtitle in checkCategory.checkedArts): # Already checked
                continue
            checkCategory.checkedArts.append(article.unprefixedtitle)
            articleText=article.getWikiText().decode('utf-8')
            articleEditSummary=[]
            articleTemplates=article.getTemplates()
            stub=[s for s in articleTemplates if s.find('-stub') != -1]==[] # look for {{Foo-stub}}
            if checkCategory.classStubRE.search(talkText):
            	stub=True
            if "Template:Stub" in articleTemplates:
                stub=True
                articleText=checkCategory.stubRE.sub('{{Meteorite-stub}}',articleText)
                articleEditSummary.append("Replaced {{Stub}} with {{Meteorite-stub}}")
            elif stub:
                articleText+="\n\n{{Meteorite-stub}}"
                articleEditSummary.append("Added {{Meteorite-stub}}")
            addedWPGeoTpl=False
            if not (talk.exists and "Template:WikiProject Geology" in talk.getTemplates()):
                addedWPGeoTpl=True
                talkText="{{WikiProject Geology|class=|importance=|attention=|needs-infobox=}}\n\n"+talkText
                editSummary.append("Added {{WikiProject Geology}}")
                print "Adding {{WikiProject Geology}}"
            country="" # No country
            for c in article.getCategories():
                if c[:29] == "Category:Meteorites found in ":
                    country=c[29:]
                    if (re.search('\{\{[Ww]ikiProject '+country,talkText) == None and
                            Page(wikipedia,'Wikipedia:WikiProject '+country).exists): # No template but WikiProject exists
                        talkText="{{WikiProject "+country+("|class=Stub|auto=Yes" if stub else "")+"}}\n\n"+talkText
                        editSummary.append("Added {{WikiProject "+country+"}}")
                    break
            # Note: {{WikiProject Geology}} will always be in talkText, since we put it in above
            parsedTalk=mwparserfromhell.parse(talkText)
            # Put the {{WikiProject Geology}} template into the variable 'tpl' (yes this looks wierd)
            tpl=[tpl for tpl in parsedTalk.filter_templates() if tpl.name.strip().lower()=='wikiproject geology'][0]
            if stub and (not tpl.has_param('class') or tpl.get('class') != ""):
                tplset(tpl,'class','Stub')
                tplset(tpl,'auto','Yes')
            if checkCategory.infoboxRE.search(article.getWikiText()):
                try:
                    tpl.remove('needs-infobox')
                except ValueError:
                    False # There wasn't a needs-infobox param, which is fine
            else:
                tplset(tpl,'needs-infobox',"No")
            tplset(tpl,'meteorite',"Yes")
            if not tpl.has_param('meteorite-importance'):
                tpl.add('meteorite-importance','')
            if parsedTalk != talkText:
                talkText=str(parsedTalk).decode('utf-8')
                if not addedWPGeoTpl: # Only put in an edit summary for these changes if the template wasn't just added
                    editSummary.append("Changed {{WikiProject Geology}} parameters")
            if checkCategory.astronomyRE.search(talkText) != None: # Article is part of WikiProject Astronomy
                astrolist.write('* [['+article.title+"]]\n")
            resp = api.APIRequest(wikipedia,{'action': 'query','prop': 'images','titles':article.title}).query()
            for item in resp['query']['pages'][resp['query']['pages'].keys()[0]]['images']:
            	link=Page(wikipedia,item['title'])
            	if not (link.exists): continue # TODO what about images on Commons?
                if (link.unprefixedtitle in checkCategory.checkedImgs): # Already checked
                    continue
                checkCategory.checkedImgs.append(link.unprefixedtitle)
                if link.namespace==6: # Image
                	imagelist.write('* [[:File:'+link.unprefixedtitle+"]]\n")
            if articleEditSummary != []: # Article was edited
                # TODO actually edit
                fakedit.write(article.title+" ("+"; ".join(articleEditSummary)+")\n"+articleText+"\n###########################\n\n")
        if editSummary != []: # Talk page was edited
            # TODO actually edit
            fakedit.write(talk.title+" ("+"; ".join(editSummary)+")\n"+talkText+"\n###########################\n\n")
    # Save data for the next run
    pickle.dump([checkCategory.checkedCats,checkCategory.checkedArts,checkCategory.checkedImgs],open('tasks/meteorites/jar.pickle','wb'))
def tplset(tpl,name,value):
    if tpl.has_param(name):
        tpl.get(name).value=value
    else:
        tpl.add(name,value)
fakedit=codecs.open('fakedit.txt','w','utf-8')
# Load previous run data
[checkCategory.checkedCats,checkCategory.checkedArts,checkCategory.checkedImgs] = pickle.load(open('tasks/meteorites/jar.pickle','rb'))
checkCategory.stubRE=re.compile('\{\{[Ss]tub\}\}')
checkCategory.infoboxRE=re.compile('{\{([Ii]nfobox|[Mm]arsGeo|[[Cc]hembox])')
checkCategory.astronomyRE=re.compile('\{\{[Ww]ikiProject Astronomy')
checkCategory.coordsRE=re.compile('\{\{[Cc]oord')
checkCategory.classStubRE=re.compile('class\=Stub')
checkCategory("Meteorites")
astrolist.close()
imagelist.close()
fakedit.close()
