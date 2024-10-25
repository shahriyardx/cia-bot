from aiohttp import web


@web.middleware
async def trailing_slash_middleware(request, handler):
    if request.path.endswith("/") or request.path == "/":
        return await handler(request)
    else:
        raise web.HTTPMovedPermanently(location=request.path + "/")
