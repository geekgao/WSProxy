# WSProxy
Forward local socks5 proxy data to the remote end using websocket. Just a TOY proxy in Python.
---

USAGE
```
usage: wsserv.py [-h] [--host HOST] [--port PORT] --cert_file CERT_FILE --key_file KEY_FILE --ca_file CA_FILE --token TOKEN
wsserv.py: error: the following arguments are required: --cert_file, --key_file, --ca_file, --token



usage: wsclient.py [-h] [--socks5_host SOCKS5_HOST] [--socks5_port SOCKS5_PORT] [--ws_server_uri WS_SERVER_URI] [--ca_pem CA_PEM]
                   [--client_cert_pem CLIENT_CERT_PEM] [--client_key_pem CLIENT_KEY_PEM] [--token TOKEN]

Start the server.

options:
  -h, --help            show this help message and exit
  --socks5_host SOCKS5_HOST
                        SOCKS5 host
  --socks5_port SOCKS5_PORT
                        SOCKS5 port
  --ws_server_uri WS_SERVER_URI
                        WebSocket server URI
  --ca_pem CA_PEM       Path to CA certificate
  --client_cert_pem CLIENT_CERT_PEM
                        Path to client certificate
  --client_key_pem CLIENT_KEY_PEM
                        Path to client key
  --token TOKEN         Authorization token
```
