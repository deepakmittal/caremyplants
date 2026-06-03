import os
import re
import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL")

@pytest.mark.asyncio
async def test_background_color():
    if not BASE_URL:
        pytest.skip("BASE_URL environment variable is not set")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Make a GET request to the root URL
        response = await client.get("/")
        response.raise_for_status()
        html_content = response.text

        # 2. Parse the HTML response to find the URL of the CSS file
        # The CSS file will have a name like 'index-*.css'
        css_url_match = re.search(r'href="(/assets/index-[a-zA-Z0-9]+\.css)"', html_content)
        assert css_url_match is not None, "CSS file link not found in HTML"
        css_url = css_url_match.group(1)

        # 3. Make a GET request to that CSS file's URL
        css_response = await client.get(css_url)
        css_response.raise_for_status()
        css_content = css_response.text

        # 4. Check if the content of the CSS file contains the red background color
        # The CSS will be minified, so we need to account for that.
        assert "--bg-dark:#ff0000" in css_content.replace(" ", ""), "Background color not set to red"
