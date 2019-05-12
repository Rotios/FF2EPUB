import os.path
import codecs
import zipfile
import tempfile
import re
from shutil import copyfile
from jinja2 import Environment, PackageLoader
from docutils.core import publish_string, publish_doctree

class ConvertTextToEPub:

    def convert_text_to_epub(self, destination, sources, story_info):
        try:
            zip_file = zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED)        

            story_info.update({
                'files': sources,
                'chapters': [],
                'identifier':story_info['title']
            })

            temp_dir = tempfile.mkdtemp()
            os.mkdir(os.path.join(temp_dir, 'content'))

            cwd = os.path.dirname(os.path.realpath(__file__))

            zip_file.write(os.path.join(cwd,'templates', 'mimetype'), 'mimetype', zipfile.ZIP_STORED)
            zip_file.write(os.path.join(cwd,'templates', 'META-INF', 'container.xml'), 'META-INF/container.xml', zipfile.ZIP_STORED)

            env = Environment(loader=PackageLoader(__name__, "templates"))
            template = env.get_template("content_page.html")

            files = []
            for source in sources:
                source['media_type'] = 'application/xhtml+xml'
                with codecs.open(source['path'],'r',encoding='utf8') as f:
                    chapter_content = f.read()
                    
                content = {
                    'title': source['name'],
                    'content': self.translate_html(chapter_content)
                }
                
                text = template.render(content)
                
                path_to_temp_content = os.path.join(temp_dir, 'content', source['fileName'])
                with codecs.open(path_to_temp_content, 'w+', 'utf-8') as f:
                    f.write(text)

                zip_file.write(path_to_temp_content, 'content/' + source['fileName'], zipfile.ZIP_STORED)

                story_info['chapters'].append(source)
                files.append(source['fileName'])

            self.zip_content(env, temp_dir, story_info, zip_file, '00_content.opf')
            self.zip_content(env, temp_dir, story_info, zip_file, '00_toc.ncx')
            self.zip_content(env, temp_dir, story_info, zip_file, '00_stylesheet.css')

        finally:
            if zip_file:
                zip_file.close()

    def zip_content(self, env, temp_dir, story_info, zip_file, name):
        template = env.get_template(name)
        path = os.path.join(temp_dir, 'content', name)
        with codecs.open(path, 'w', 'utf-8') as out:
            out.write(template.render(story_info))

        zip_file.write(path, 'content/' + name, zipfile.ZIP_DEFLATED)

    def translate_html(self, chapter_content):
        content = chapter_content.replace('<br>','<br/>')
        return "<br/>" + content

    def encode_entities(self, text):
        return text.replace(
            "&", "&amp;").replace(
            ">", "&gt;").replace(
            "<", "&lt;").replace(
            r"\_", "&#95;")
