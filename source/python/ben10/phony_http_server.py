'''
Implements a simple HTTP server used for tests related with the HTTP.

Example:

    server, port = PhonyHttpServer.CreateAndStart()
    try:
        # Create a client and use the port to communicate
    finally:
        server.stop()

TODO: Perform expansions as necessary. Pass to the server what to serve. For now its a constant
value.
'''
from SimpleHTTPServer import SimpleHTTPRequestHandler
from ben10.foundation.decorators import Override
import BaseHTTPServer



#===================================================================================================
# PhonyHttpHandler
#===================================================================================================
class PhonyHttpHandler(SimpleHTTPRequestHandler):
    '''
    Phony HTTP handler that always respond with "Hello, <user-agent>".
    This is used to check if we are correctly sending the user-agent to the server when
    requesting stuff from there.
    '''

    def do_POST(self):
        '''
        Handle all POST requests with the same output containing the path, headers and form data
        information.
        '''
        import cgi

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD' : 'POST',
                'CONTENT_TYPE' : self.headers['Content-Type'],
            }
        )

        self.send_response(200)
        self.end_headers()

        self.wfile.write('Client: %s\n' % (self.client_address,))
        self.wfile.write('Path: %s\n' % self.path)
        self.wfile.write('Form data:\n')

        for field_name in form.keys():
            from ben10.foundation.types_ import AsList
            field_item = AsList(form[field_name])
            for item in field_item:
                self.wfile.write(item.value + '\t')


    def do_GET(self):
        '''
        Handle all GET requests with the same output containing the path and all headers
        information.
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html')

        # Obtain the contents
        if callable(self.server.http_get_callback):
            contents = self.server.http_get_callback(self.path)
        else:
            contents = 'path = %s\n' % self.path
            for i_name, i_value in sorted(self.headers.dict.iteritems()):
                contents += '%s = %s\n' % (i_name, i_value)

        # Add content-length to the header
        self.send_header('content-length', str(len(contents)))
        self.end_headers()

        # Write the contents
        self.wfile.write(contents)


    def do_QUIT (self):
        '''
        Stops the server when receiving a HTTP QUIT request.
        '''
        self.send_response(200)
        self.end_headers()
        self.server.running = False


    def log_message(self, format, *args):
        message = "%s - - [%s] %s\n" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args
        ),
        self.server.log_message_callback(message)



#===================================================================================================
# ProxyHandler
#===================================================================================================
class ProxyHandler(PhonyHttpHandler):
    '''
    A proxy handler that will raise the HTTP error 407 (authentication required) if not login
    and password are defined at the handler.

    :cvar str login:
        The login that must be used on authentication. It can be anything different from empty.

    :cvar str password:
        The password that must be used on authentication. It can be anything different from empty.
    '''

    login = ''
    password = ''

    @Override(PhonyHttpHandler.do_GET)
    def do_GET(self):
        if not ProxyHandler.login.strip() or not ProxyHandler.password.strip():
            self.send_error(407)
        else:
            PhonyHttpHandler.do_GET(self)


    @classmethod
    def Reset(cls):
        '''
        Reset the login and password to empty values.
        '''
        ProxyHandler.login = ''
        ProxyHandler.password = ''



#===================================================================================================
# PhonyHTTPServer
#===================================================================================================
class PhonyHTTPServer(BaseHTTPServer.HTTPServer):
    '''
    Phony HTTP server with a "stop" method.

    Any file requestes returns "Hello, <user-agent>", where the user-agent is the contents of the
    user agent requested by the user.
    '''

    def __init__(self, *args, **kwargs):
        from ben10.foundation.callback import Callback
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)

        #@ivar log_message_callback: Callback
        #    Called when a log message is generated.
        self.log_message_callback = Callback()

        #@ivar http_get_callback: callable(path) | None
        #    Called to obtain the contents of the given path (url). If not defined, HTTP GET returns
        #    the default contents, with the headers data.
        self.http_get_callback = None


    def serve_forever(self):
        """Handle one request at a time until stopped."""
        self.running = True
        while self.running:
            self.handle_request()


    def start(self):
        '''
        Starts to server by starting a thread calling "server_forever"
        '''
        import threading
        threading.Thread(target=self.serve_forever).start()


    def stop(self):
        '''
        Stop the server by sending a QUIT request to the server via HTTP.
        '''
        import httplib
        host = '127.0.0.1'
        port = self.server_address[1]
        conn = httplib.HTTPConnection(host, port)
        conn.request("QUIT", "/")
        conn.getresponse()


    @classmethod
    def CreateAndStart(cls, request_handler=None):
        '''
        Create a PhonyHttpServer and return it together with the port it is serving.

        :param BaseHTTPServer.BaseHTTPRequestHandler request_handler:
            Implementation of HTTP request handler that must be used by the phony editor.

        :rtype: PhonyHTTPServer, int
        :returns:
            The server instance and the port where the server is running.
        '''
        if request_handler is None:
            request_handler = PhonyHttpHandler

        server = PhonyHTTPServer(('', 0), request_handler)
        _address, port = server.socket.getsockname()

        # We have to explictly write the port in server_address because on Python 2.4 (dist-0703)
        # the value stored is "0", not the actual port AND we use this to send the "QUIT" message
        # (see stop implemetnation).
        if server.server_address[1] == 0:
            server.server_address = (server.server_address[0], port)

        server.start()
        return (server, port)
