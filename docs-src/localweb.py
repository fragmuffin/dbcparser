# run using:
#   ./go.sh web

import os
import time
import http.server
import socketserver
import threading
import webbrowser

PORT = 9040
socketserver.TCPServer.allow_reuse_address = True

Handler = http.server.SimpleHTTPRequestHandler

os.chdir('./_build/html/')
httpd = socketserver.ThreadingTCPServer(("", PORT), Handler)


print("serving: http://localhost:%i/" % PORT)
try:
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    webbrowser.open("http://localhost:%i/" % PORT)

    while True:  # wait for Ctrl+C
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[keyboard interrupt]")

finally:
    httpd.shutdown()
    httpd.server_close()
    server_thread.join()
    print("[http shutdown successfully]")
