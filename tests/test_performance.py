"""Check image output contracts: URLs, source quality and author intent."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser

from PIL import Image
from hooks import performance


class Tags(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.tags = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ImageBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / '图 image.png'
        Image.new('RGB', (1800, 1000), '#f5f5f5').save(self.source)
        self.config = {'config_file_path': str(self.root / 'mkdocs.yml'), 'site_dir': str(self.root / 'site')}
        self.page = SimpleNamespace(file=SimpleNamespace(url='notes/chapter/'))
        file = SimpleNamespace(dest_uri='notes/assets/图 image.png', abs_src_path=str(self.source))
        performance.on_files([file], self.config)

    def render(self, content):
        return performance.on_page_content(content, self.page, self.config, [])

    def test_encoded_images_have_variants_and_original_link(self):
        content = self.render('<p><img src="../assets/%E5%9B%BE%20image.png" alt="a &gt; b"></p>')
        tags = Tags(content).tags
        image = next(attrs for tag, attrs in tags if tag == 'img')
        link = next(attrs for tag, attrs in tags if tag == 'a')
        self.assertEqual(image['alt'], 'a > b')
        self.assertEqual((image['width'], image['height']), ('1800', '1000'))
        self.assertEqual(link['href'], '../assets/%E5%9B%BE%20image.png')
        self.assertIn('640w', image['srcset'])
        for variant in (self.root / 'site/assets/optimized').iterdir():
            with Image.open(variant) as file:
                self.assertLessEqual(file.width, 1800)
            self.assertLess(variant.stat().st_size, self.source.stat().st_size)
        self.assertTrue(self.source.exists())

    def test_images_below_the_first_are_lazy_and_remote_urls_survive(self):
        content = self.render('<img src="https://example.com/a.png"><img src="https://example.com/b.png">')
        images = [a for t, a in Tags(content).tags if t == 'img']
        self.assertEqual([i['loading'] for i in images], ['eager', 'lazy'])
        self.assertEqual(images[1]['src'], 'https://example.com/b.png')

    def test_existing_links_and_explicit_size_are_preserved(self):
        content = self.render('<a href="original"><img src="../assets/%E5%9B%BE%20image.png" width="300" loading="eager"></a>')
        tags = Tags(content).tags
        self.assertEqual(sum(t == 'a' for t, _ in tags), 1)
        image = next(a for t, a in tags if t == 'img')
        self.assertEqual(image['width'], '300')
        self.assertNotIn('height', image)
        self.assertEqual(image['loading'], 'eager')

    def test_code_examples_and_emoji_are_not_rewritten(self):
        content = '<pre><code>&lt;img src="foo"&gt;</code></pre><img class="twemoji" src="emoji.svg">'
        self.assertEqual(self.render(content), content)

    def test_custom_srcset_is_preserved(self):
        content = self.render('<img src="../assets/%E5%9B%BE%20image.png" srcset="custom.webp 640w">')
        image = next(a for t, a in Tags(content).tags if t == 'img')
        self.assertEqual(image['srcset'], 'custom.webp 640w')

    def test_animated_images_remain_animated(self):
        source = self.root / 'animated.webp'
        Image.new('RGB', (20, 20), 'red').save(source, save_all=True, append_images=[Image.new('RGB', (20, 20), 'blue')], duration=100, loop=0)
        performance.on_files([SimpleNamespace(dest_uri='notes/animated.webp', abs_src_path=str(source))], self.config)
        content = self.render('<img src="../animated.webp">')
        image = next(a for t, a in Tags(content).tags if t == 'img')
        self.assertEqual(image['src'], '../animated.webp')
        self.assertNotIn('srcset', image)


if __name__ == '__main__':
    unittest.main()
