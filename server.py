import asyncio
import json
import os
from aiohttp import web

# ============ تنظیمات ============
TOKEN = "mysecret123"        # رمز ضبط‌کننده — حتماً عوضش کن
HOST = "0.0.0.0"
PORT = 8080
# =================================

listeners = set()   # شنونده‌های WebSocket

HERE = os.path.dirname(os.path.abspath(__file__))

async def index(request):
    return web.FileResponse(os.path.join(HERE, "index.html"))

async def ws_send(request):
    """ضبط‌کننده به اینجا وصل می‌شه و صدا می‌فرسته"""
    if request.query.get("token") != TOKEN:
        return web.Response(status=403, text="bad token")

    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)
    print(f"🎙️ ضبط‌کننده وصل شد | شنونده‌ها: {len(listeners)}")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.BINARY:
                data = msg.data
                # پخش زنده برای همه شنونده‌ها
                dead = []
                for listener in listeners:
                    try:
                        await listener.send_bytes(data)
                    except Exception:
                        dead.append(listener)
                for d in dead:
                    listeners.discard(d)
    finally:
        print("🎙️ ضبط‌کننده قطع شد")

    return ws

async def ws_listen(request):
    """مرورگر شنونده به اینجا وصل می‌شه"""
    ws = web.WebSocketResponse(max_msg_size=0)
    await ws.prepare(request)
    listeners.add(ws)
    print(f"👂 شنونده جدید | کل: {len(listeners)}")

    try:
        async for _ in ws:
            pass
    finally:
        listeners.discard(ws)
        print(f"👂 شنونده رفت | کل: {len(listeners)}")

    return ws

async def status(request):
    return web.json_response({
        "listeners": len(listeners),
        "live": len(listeners) > 0
    })

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/send", ws_send)
app.router.add_get("/listen", ws_listen)
app.router.add_get("/status", status)

if __name__ == "__main__":
    print(f"🚀 سرور روی http://{HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT, print=None)
