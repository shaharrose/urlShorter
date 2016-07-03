import Queue
import os
import re
import socket
import traceback
from threading import *
from datetime import datetime
import sys

_favicon = ""

_MIME_types = {
    "image": ("bmp", "gif", "jpeg", "jpg", "png", "svg", "tiff"),
    "text": ("html", "css", "csv", "html", "calender", "plain")
}

_ErrorCodes = {
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',  # RFC '251'8 (WebDAV)
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi-Status',  # RFC '251'8 (WebDAV)
    208: 'Already Reported',  # RFC '584'2
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Large',
    415: 'Unsupported Media Type',
    416: 'Request Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'I\'m a teapot',  # RFC '232'4
    422: 'Unprocessable Entity',  # RFC '251'8 (WebDAV)
    423: 'Locked',  # RFC '251'8 (WebDAV)
    424: 'Failed Dependency',  # RFC '251'8 (WebDAV)
    425: 'No code',  # WebDAV Advanced Collections
    426: 'Upgrade Required',  # RFC '281'7
    428: 'Precondition Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    449: 'Retry with',  # unofficial Microsoft
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    506: 'Variant Also Negotiates',  # RFC '229'5
    507: 'Insufficient Storage',  # RFC '251'8 (WebDAV)
    509: 'Bandwidth Limit Exceeded',  # unofficial
    510: 'Not Extended',  # RFC '277'4
    511: 'Network Authentication Required'
}


class HTTPServer:
    def __init__(self, addr, port, handler):
        """
        Make a new Server object.
        :param addr: the address you want to run on. example - '127.0.0.1'.
        :param port: the port you want to run on. example - 8080.
        :param handler: handler class you want to use. the handler must extend this file's Handler.
        """
        if not issubclass(handler, Handler):
            sys.stderr.write("The given handler is not an instance of this file's Handler.")
            sys.exit(-1)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.bind((addr, port))
        self.my_socket.listen(10)
        self.handler = handler
        print "[*] Server initialized on [" + addr + "] through port [" + str(port) + "]"

    def run(self):
        """
        Run the server, the code writen after this call will not run until you stop the server.
        """
        print "[*] Server started"
        while 1:
            connection, client_address = self.my_socket.accept()
            client_handler = self.handler(self, connection, client_address)
            t = Thread(target=client_handler.handler)
            t.start()

    def run_in_background(self):
        """
            Run the server, the code writen after this call will run.
            """
        t = Thread(target=self.run)
        t.start()


class Handler:
    _ServerNameHeader = 'Server: FakeHTTP 2.0\n'
    _HEADERS_200 = "HTTP/1.1 200 OK\n"

    def __init__(self, HTTPserver, connection, client_address):
        # self._HTTPserver = HTTPserver
        self._connection = connection
        self._client_address = client_address
        self._toSend = Queue.Queue()
        self._cookies = []
        self._ContentType = ""

    def handler(self):
        data = str(self._connection.recv(16384))
        if 'favicon.ico' in data:
            self._connection.send(_favicon)
            return
        if data.__len__() < 2:
            return
        # print data
        dataLines = data.splitlines()
        request_type = dataLines[0].split(' /')[0]
        if 'GET' not in request_type and 'POST' not in request_type and 'HTTP/1.1' not in dataLines[0]:
            self._connection.send('noob')
            self._connection.close()
            return

        path = re.search(request_type + r'(.*) HTTP/1.1', dataLines[0], flags=0).group(1)[1:]
        print "[*] " + str(datetime.now().strftime('%Y/%m/%d %H:%M:%S')) + ": New connection from " \
              + self._client_address[0] + ":" + str(
            self._client_address[1]) + " Using " + request_type + "    for " + path
        try:
            if request_type == 'GET':
                variables = self.pathVariables(path)
                self.DO_GET(path, variables)
            elif request_type == 'POST':
                variables = self.postVariables(data)
                files = self.getFiles(data)
                variables['files'] = files
                self.DO_POST(path, variables)
        except:
            print ""
            traceback.print_exc()
            self.SendStatusCode(500)
            return

        try:  # If connection closed, probably by SendStatusCode, return
            self._connection.send("")
        except:
            # print "connetion closed"
            return

        toSend = []
        ContentLength = -1  # Should be 0, only -1 worked :S
        while not self._toSend.empty():
            data = self._toSend.get() + '\n'
            toSend.append(data)
            ContentLength += len(data)
        self._connection.send(self._HEADERS_200 + self._ServerNameHeader + self._ContentType +
                              self._ContentLength(ContentLength) + self._CookiesToString(self._cookies) + "\n")
        for data in toSend:
            self._connection.send(data)
        self._connection.close()

    def send(self, data):
        """Sends."""
        # self._connection.send(data)
        self._toSend.put(data)
        return

    def SendStatusCode(self, errorCode):
        if _ErrorCodes.__contains__(errorCode):
            self._connection.send(self._MakeStatusCodeMessage(_ErrorCodes[errorCode]))
        else:
            print "[***] Error code " + str(errorCode) + " is not supported"
            self._connection.send(self._MakeStatusCodeMessage(_ErrorCodes[500]))
        self._connection.close()

    @staticmethod
    def getFiles(data):
        """
        Get files from request's data.
        :param data: HTTP request's data.
        :return: a dictionary in the structure of {'file name':'file data'}.
        """
        formBoundary = ""
        for line in data.splitlines():
            if line.__contains__("boundary"):
                formBoundary = line.split("boundary=")[1]
                break
        try:
            postdata = str(data).split(formBoundary)
            results = []
            for d in postdata:
                if 'filename' in d:
                    res = re.findall(
                        r'''\r\nContent-Disposition: form-data; name="(?:[^;]+)"; filename="(\S*)"\r\n(?:[^\n\n]*)\r\n\r\n((?:.*\n)*)''',
                        d, flags=0)
                    if len(res) > 0:
                        results.append(res[0])
            dicRes = {}
            for r in results:
                dicRes[r[0]] = r[1][:-1]
            return dicRes
        except:
            return {}

    @staticmethod
    def _MakeStatusCodeMessage(code):
        result = "HTTP/1.1 " + code + "\n\n"
        result += "<html><head><title>" + code + "!</title></head><body>"
        result += "<div align=center><font size=9 face='impact'><b>" + code + "!</b></font></div></body></html>"
        return result

    @staticmethod  # what the hell? pycharm told me to do this TODO understand
    def _ContentLength(size):
        """
        Generate a ContentLength header for the given size.
        :param size: Content Length
        :return: a ContentLength header for the given size.
        """
        return "Content-Length: " + str(size) + "\n"

    def SetCookie(self, name, value):
        """
        Add a new cookie for the user.
        For example, SetCookie('name', 'Shahar') will give the user a cookie
        that looks like 'name:Shahar'.
        :param name: Cookie name
        :param value: Cookie value
        :return:
        """
        self._cookies.append((name, value))
        return

    @staticmethod
    def _CookiesToString(cookies):
        """Args:
            cookies: An array of pairs of cookie's key and values.
        Returns:
            A string of the final cookie header."""
        if not cookies:
            return ''
        result = 'Set-Cookie: '
        for cookie in cookies:
            result += cookie[0] + '=' + cookie[1] + '; '
        return result[:result.__len__() - 2] + '\n'

    @staticmethod
    def SetFavicon(fileName):
        """Args:
            fileName(str): The name or path of the desired favicon for the current requested page."""
        global _favicon
        _favicon = open(fileName, 'rb').read()

    def SendFile(self, fileName):
        """Args:
            fileName(str): The name or path of the file you want to send."""
        fileType = str(fileName).split(".")
        fileType = fileType[len(fileType) - 1]
        self.SetContentType(fileType)
        self._toSend.queue.clear()
        self.send(open(fileName, 'rb').read())

    @staticmethod
    def pathVariables(path):
        """Args:
            path(str): The path you want to get variables from.
        Returns:
            A dictionary of the variable's name and values."""
        try:
            var_section = path.split('?')[1]
            name_and_value = str(var_section).split('&')
            return {pair.split('=')[0]: pair.split('=')[1] for pair in name_and_value}
        except:
            return {}

    @staticmethod
    def postVariables(headers):
        """Args:
            headers(str): The connection headers.
        Returns:
            A dictionary of POST keys and values."""
        # print headers
        headers = headers.splitlines()
        res = []
        dict_res = {}
        for line in headers:
            # print line
            res = re.findall(r'([^&]*)=([^&]*)', line, flags=0)
            # else: print "NON",
        for pair in res:
            dict_res[pair[0]] = pair[1]
        return dict_res

    @staticmethod
    def saveReceivedFiles(variables):
        """
        Pass DO_POST's variables here and this function will save the received files to
        'uploads' filder
        :param variables: DO_POST's 'variables'
        :return: void
        """
        if not os.path.exists(os.getcwd() + "/uploads"):
            os.mkdir(os.getcwd() + "/uploads")
        for fileName, fileData in variables['files'].iteritems():
            with open(os.getcwd() + "/uploads/" + fileName, 'a+') as f:
                f.write(fileData)

    # Same as MIME
    def SetContentType(self, ContentType):
        for MIMEtype in _MIME_types:
            if str.lower(ContentType) in _MIME_types[MIMEtype]:
                self._ContentType = "Content-Type: " + MIMEtype + "/" + ContentType + "; charset=utf-8\n"
                return
        print 'Content Type not supported!'
        self.SetContentType("plain")

    def DO_GET(self, path, variables={}):
        # print path + ' GET'
        msg = "requested: " + path + ", DO_GET is not defined by the implementing class"
        self.send(msg)
        print msg
        return

    def DO_POST(self, path, variables={}):
        # print path + ' POST'
        msg = "requested: " + path + ", DO_POST is not defined by the implementing class"
        # self.send(msg)
        print msg
        return


if __name__ == "__main__":
    sys.stderr.write("This is not a runnable file.\nTo use the HTTPServer, create an HTTPServer instance and"
                     " enter it an object that\nextends Handler and overrides DO_GET and DO_POST")
