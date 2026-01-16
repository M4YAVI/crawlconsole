
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import re

def clean_and_convert(html, include_links=False, include_images=False):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Semantic cleaning: Remove noise elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
        tag.decompose()
    
    # Additional heuristic noise removal
    for tag in soup.find_all(attrs={"class": re.compile(r"(ad|banner|cookie|popup|subscription|login-modal)", re.I)}):
        tag.decompose()
        
    print(f"--- Before filtering: Links={len(soup.find_all('a'))}, Images={len(soup.find_all('img'))} ---")

    # Filter links if not requested
    if not include_links:
        print("Filtering links...")
        for tag in list(soup.find_all('a')):
            tag.unwrap() # Removes the tag but keeps text
            
    # Filter images if not requested
    if not include_images:
        print("Filtering images...")
        for tag in list(soup.find_all('img')):
            tag.decompose() # Removes message completely
            
    print(f"--- After filtering: Links={len(soup.find_all('a'))}, Images={len(soup.find_all('img'))} ---")

    clean_html = str(soup)
    print(f"Clean HTML: {clean_html}")
    
    markdown = md(clean_html, heading_style="ATX", strip=['script', 'style', 'button', 'input', 'form'])
    return markdown

# Test case mimicking the reported issue (Image inside Link)
html_sample = """
<div>
    <h1>Test Post</h1>
    <p>December 16, 2025</p>
    <a href="https://video.fna.fbcdn.net/v/t2/f2/m366/video.mp4">
        <img src="https://scontent.fmaa11-1.fna.fbcdn.net/v/t39.8562-6/image.png?_nc_cat=102" alt="Video Thumbnail">
    </a>
    <p>At Meta, we're using these advancements...</p>
</div>
"""

print("\n--- TEST: include_links=False, include_images=False ---")
result = clean_and_convert(html_sample, include_links=False, include_images=False)
print(f"RESULT:\n{result}\n")

print("\n--- TEST: include_links=True, include_images=True ---")
result_full = clean_and_convert(html_sample, include_links=True, include_images=True)
print(f"RESULT FULL:\n{result_full}\n")
