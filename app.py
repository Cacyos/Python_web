import logging;logging.basicConfig(level = logging.INFO)
import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):
	return web.Response(body = b'<h1>Awesome</h1>',content_type = 'text/html')

@asyncio.coroutine
def init():
	app = web.Application()
	app.add_routes([web.get('/',index)])
	runner = web.AppRunner(app)
	yield from runner.setup()
	site = web.TCPSite(runner,'localhost','9000')
	# srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000) 
	#等待异步操作返回，不向下执行，而是进入消息循环中的另一个协程，注意是另一个，当前的不再向下执行了，直到有异步的返回值
	yield from site.start()
	print('服务器启动成功!')

loop = asyncio.get_event_loop()
loop.run_until_complete(init())
loop.run_forever()