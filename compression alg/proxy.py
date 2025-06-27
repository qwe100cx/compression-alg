from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import re
import cssmin
import jsmin
import chardet

app = Flask(__name__)

def detect_encoding(content):
    result = chardet.detect(content)
    return result['encoding'] if result['confidence'] > 0.7 else 'utf-8'

def compress_image(image_data, format='WEBP', quality=70):
    img = Image.open(BytesIO(image_data))
    output = BytesIO()

    if format.upper() == 'JPEG':
        img = img.convert('RGB')
    img.save(output, format, quality=quality)
    return output.getvalue()

def minify_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'\s+', ' ', html)
    return html.strip()

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return "Error: URL parameter is missing", 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept-Charset': 'utf-8'
        }
        response = requests.get(url, headers=headers)

        encoding = detect_encoding(response.content)
        decoded_content = response.content.decode(encoding)

        content_type = response.headers.get('Content-Type', '')

        if 'text/html' in content_type:
            soup = BeautifulSoup(decoded_content, 'html.parser', from_encoding=encoding)

            if soup.meta and soup.meta.get('charset'):
                soup.meta['charset'] = 'utf-8'
            else:
                meta = soup.new_tag('meta', charset='utf-8')
                soup.head.insert(0, meta) if soup.head else soup.insert(0, meta)

            for tag in soup(['script', 'iframe', 'video', 'style']):
                tag.decompose()

            for img in soup.find_all('img'):
                if img.get('src'):
                    img['src'] = f"/proxy_image?url={img['src']}"

            html = str(soup)
            html = minify_html(html)

            return Response(html, content_type='text/html; charset=utf-8')

        elif 'image/' in content_type:
            optimized_img = compress_image(response.content)
            return Response(optimized_img, content_type='image/webp')

        elif 'text/css' in content_type:
            css = cssmin.cssmin(decoded_content)
            return Response(css, content_type='text/css; charset=utf-8')

        elif 'application/javascript' in content_type:
            js = jsmin.jsmin(decoded_content)
            return Response(js, content_type='application/javascript; charset=utf-8')

        return Response(response.content, content_type=content_type)

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/proxy_image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return "Error: URL parameter is missing", 400

    try:
        response = requests.get(url)
        optimized_img = compress_image(response.content)
        return Response(optimized_img, content_type='image/webp')
    except Exception as e:
        return f"Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(port=5000)