from django.http import HttpRequest, HttpResponse

from django_nextjs.render import render_nextjs_page


async def nextjs_frontend(request: HttpRequest, path: str = "") -> HttpResponse:
    """Proxy page rendering to the Next.js frontend."""
    return await render_nextjs_page(request)
