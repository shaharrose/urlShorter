import urllib
from random import randint

from HTTPServer import HTTPServer, Handler
from sqlMaster import sqlMaster

generateLinkChars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
server_location = 'http://localhost:8080'
error_page = open('error.html').read().replace('HOSTLOC', server_location)
landing_page = open('landing.html').read().replace('HOSTLOC', server_location)


def generateLink(length):
    res = ''
    for i in range(length):
        res += generateLinkChars[randint(0, len(generateLinkChars) - 1)]
    return res


def getRedirectHTML(url):
    return '''<html><head><script>function redirect(){    window.location = '%s';}
    window.onload = redirect;</script></head><body>redirecting</body></html>''' % url


class MyHandler(Handler):
    def DO_GET(self, path, variables={}):
        if path == '/sfFont.otf':
            self.SendFile('sfFont.otf')
            return
        elif path == '/generate':
            self.send(generateLink(6))

        # source-'aOGg4t' target-'google.com'
        elif 'source' in variables and 'target' in variables and 'get' not in variables:
            if not linksDB.hasLocalPath(variables['source']):
                if len(variables['source']) > 1:
                    if all(l in generateLinkChars for l in variables['source']):
                        linksDB.insert(variables['source'], variables['target'])
                        newLink = server_location + '/' + variables['source']
                        self.send('Your shortened link is ready!<br><a href=' + newLink + '>%s</a>' % newLink)
                    else:
                        self.send(error_page % 'shortened link chosen has illegal characters')
                else:
                    self.send(error_page % 'shortened link chosen is too short')
            else:
                self.send(error_page % ('"' + variables['source'] + '" is taken!'))
        elif linksDB.hasLocalPath(path[1:]):
            target = str(urllib.unquote(linksDB.getAllDict()[path[1:]]).decode('utf8'))
            if '://' not in target:
                target = 'http://' + target
            self.send(getRedirectHTML(target))

        else:
            self.send(landing_page)
        self.SetContentType("html")
        return

    def DO_POST(self, path, variables={}):
        return


linksDB = sqlMaster()
server = HTTPServer('localhost', 8080, MyHandler)
server.run()
