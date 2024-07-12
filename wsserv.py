import asyncio
import websockets
import ssl
import struct
import socket
import argparse

TOKEN = None


def validate_token(token):
    global TOKEN
    return token == TOKEN


async def handle_websocket(websocket, path):
    if "my_secure_protocol" not in websocket.subprotocols:
        await websocket.close(code=1002, reason="Unsupported protocol")
        return
    try:
        token = websocket.request_headers["Authorization"]
        if not validate_token(token):
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except KeyError:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # 解析SOCKS5握手
    data = await websocket.recv()
    if data[0] != 0x05:
        return

    # 响应SOCKS5握手
    await websocket.send(struct.pack("!BB", 0x05, 0x00))

    # 解析SOCKS5请求
    data = await websocket.recv()
    if data[1] != 0x01:
        return

    address_type = data[3]
    if address_type == 0x01:  # IPv4
        address = socket.inet_ntoa(data[4:8])
        port = struct.unpack("!H", data[8:10])[0]
    elif address_type == 0x03:  # 域名
        domain_length = data[4]
        address = data[5 : 5 + domain_length].decode()
        port = struct.unpack("!H", data[5 + domain_length : 7 + domain_length])[0]
    else:
        return

    # 连接目标服务器
    target_reader, target_writer = await asyncio.open_connection(address, port)

    # 响应SOCKS5连接建立
    await websocket.send(struct.pack("!BBBBIH", 0x05, 0x00, 0x00, 0x01, 0, 0))

    async def forward_data(reader, writer):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except Exception as e:
            print(f"Forwarding error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    # 双向转发数据
    await asyncio.gather(
        forward_data(websocket, target_writer), forward_data(target_reader, websocket)
    )


async def start_websocket_server(host, port, cert_file, key_file, ca_file, token):
    global TOKEN
    TOKEN = token

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(cafile=ca_file)
    ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1

    async with websockets.serve(
        handle_websocket,
        host,
        port,
        ssl=ssl_context,
        subprotocols=["my_secure_protocol"],
    ):
        await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a websocket server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Websocket server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Websocket server port (default: 8765)"
    )
    parser.add_argument(
        "--cert_file", type=str, required=True, help="Path to the SSL certificate file"
    )
    parser.add_argument(
        "--key_file", type=str, required=True, help="Path to the SSL key file"
    )
    parser.add_argument(
        "--ca_file", type=str, required=True, help="Path to the SSL CA file"
    )
    parser.add_argument(
        "--token", type=str, required=True, help="Token value for validation"
    )

    args = parser.parse_args()

    asyncio.run(
        start_websocket_server(
            args.host,
            args.port,
            args.cert_file,
            args.key_file,
            args.ca_file,
            args.token,
        )
    )
