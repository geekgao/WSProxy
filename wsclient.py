import asyncio
import websockets
import ssl
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="Start the server.")
    parser.add_argument(
        "--socks5_host", type=str, default="127.0.0.1", help="SOCKS5 host"
    )
    parser.add_argument("--socks5_port", type=int, default=1080, help="SOCKS5 port")
    parser.add_argument(
        "--ws_server_uri",
        type=str,
        default="wss://remote.server:8765",
        help="WebSocket server URI",
    )
    parser.add_argument(
        "--ca_pem", type=str, default="ca.pem", help="Path to CA certificate"
    )
    parser.add_argument(
        "--client_cert_pem",
        type=str,
        default="client_cert.pem",
        help="Path to client certificate",
    )
    parser.add_argument(
        "--client_key_pem",
        type=str,
        default="client_key.pem",
        help="Path to client key",
    )
    parser.add_argument(
        "--token", type=str, default="your_token", help="Authorization token"
    )
    return parser.parse_args()


async def handle_client(client_reader, client_writer, args):
    headers = {"Authorization": f"Bearer {args.token}"}
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations(cafile=args.ca_pem)
    ssl_context.load_cert_chain(
        certfile=args.client_cert_pem, keyfile=args.client_key_pem
    )

    async with websockets.connect(
        args.ws_server_uri,
        ssl=ssl_context,
        subprotocols=["my_secure_protocol"],
        extra_headers=headers,
    ) as websocket:

        async def forward_data(reader, writer):
            try:
                while True:
                    data = await reader.read(1024)
                    if not data:
                        break
                    await writer.send(data)
            except Exception as e:
                print(f"Forwarding error: {e}")
            finally:
                writer.close()

        async def websocket_to_client():
            try:
                while True:
                    data = await websocket.recv()
                    client_writer.write(data)
                    await client_writer.drain()
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                client_writer.close()

        await asyncio.gather(
            forward_data(client_reader, websocket), websocket_to_client()
        )


async def start_server(args):
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, args), args.socks5_host, args.socks5_port
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(start_server(args))
