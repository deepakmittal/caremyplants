import os
import httpx
import pytest

@pytest.mark.asyncio
async def test_theme_update():
    base_url = os.environ.get("BASE_URL")
    if not base_url:
        pytest.fail("BASE_URL environment variable is not set.")

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url)
        assert response.status_code == 200
        
        # The CSS is likely in a separate file, so let's find it in the HTML
        # and then check its content.
        # This is a bit brittle, but it's the most reliable way to check
        # the theme without knowing the exact CSS file name.
        
        html_content = response.text
        
        # Find the CSS file link in the HTML
        import re
        match = re.search(r'<link rel="stylesheet" [^>]*href="([^"]+)"', html_content)
        
        if match:
            css_path = match.group(1)
            css_url = f"{base_url}{css_path}"
            
            css_response = await client.get(css_url)
            assert css_response.status_code == 200
            
            # Check for the new primary color in the CSS file
            assert "#f59e0b" in css_response.text
        else:
            # If the CSS is not in a separate file, check the HTML itself
            # for inline styles or a style block.
            assert "#f59e0b" in html_content

