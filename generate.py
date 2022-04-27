import markdown
import os
import shutil
from pygments import highlight
import yaml
from typing import Tuple, Sequence

extensions = ['extra']


def read_markdownfile_with_header(filename: str) -> Tuple[str, dict]:
    """ Reads a markdown file and returns the content as a string plus the header as a dictionary.

    Parameters
    ----------
    filename : str
        The name of the markdown file to read.

    Returns
    -------
    markdown_content : str
        The content of the markdown file as a string.
    header : dict
        The header of the markdown file as a dictionary (yaml output).
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")

    with open(filename, 'r') as f:
        content = f.readlines()

    header = []
    rest = []
    header_content = False
    for line in content:
        if line.startswith('---'):
            header_content = ~header_content
            continue
        if header_content:
            header.append(line)
        else:
            rest.append(line)

    return ''.join(rest), yaml.load(''.join(header), yaml.FullLoader)

def generate_program(filename: str,
                     theme: str = 'default',
                     section_class='') -> str:
    """ Generates a program page.

    Parameters
    ----------
    filename : str
        The name of the program file to write.
    index_template : str
        The name of the template file to use.
    """

    content_str, header = read_markdownfile_with_header(filename)

    if header['active'] is False:
        return ''

    theme_dir = os.path.join('theme', theme)
    index_template = os.path.join(theme_dir, 'schedule.html')

    with open(index_template, 'r') as f:
        template = f.read()

    name = filename.split('/')[-1].split('.')[0]

    # data
    items = header['program']
    hl_item_format = """{time} <font color="0080FF">{title}</font> <br>"""
    item_format = """{time} {title} <br>"""
    description_format = """<span style="display:inline-block; width: 6em;"></span><i>{description}</i><br>"""

    day = None
    program_ = []
    for entry in items:
        item = {'day': "", 'time': '', 'title': '', 'description': False, 'highlight': False}
        item.update(entry)
        for k, v in item.items():
            item[k] = markdown.markdown(v, extensions=extensions)\
                              .replace('</p>', '')\
                              .replace('<p>', '') if isinstance(v, str) else v
        day_ = item['day']
        if day_ != day:
            day = day_
            program_.append(f"""<h2 id="day-{day:s}">{day:s}</h2>""")
            day = day_
        if item.get('highlight', False):
            program_.append(hl_item_format.format(**item))
        else:
            program_.append(item_format.format(**item))
        if item['description']:
            for line in item['description'].split('\n'):
                program_.append(description_format.format(description=line))

    template = template.replace('{{name}}', name)\
                       .replace('{{other-classes}}', section_class)\
                       .replace('{{title}}', header['title'])\
                       .replace('{{description}}', markdown.markdown(header['description'], extensions=extensions))\
                       .replace('{{program-content}}', '\n'.join(program_))

    # generate menu reference
    title = header['title']
    ref = f"""<li><a class="page-scroll" href="#section-{name:s}">{title:s}</a></li>"""
    return template, ref


def generate_section(section_filename: str,
                     theme: str = 'default',
                     section_class='') -> str:
    content_str, header = read_markdownfile_with_header(section_filename)

    if header['active'] is False:
        return '', ''

    theme_dir = os.path.join('theme', theme)
    index_template = os.path.join(theme_dir, 'section.html')

    with open(index_template, 'r') as f:
        template = f.read()

    name = section_filename.split('/')[-1].split('.')[0]

    template = template.replace('{{name}}', name)\
                       .replace('{{other-classes}}', section_class)\
                       .replace('{{title}}', header['title'])\
                       .replace('{{description}}', markdown.markdown(content_str, extensions=extensions))

    # generate menu reference
    title = header['title']
    ref = f"""<li><a class="page-scroll" href="#section-{name:s}">{title:s}</a></li>"""
    return template, ref


def generate_index(index_filename: str = 'content/index.md',
                   theme: str = None):
    """ Generates an index page.

    Parameters
    ----------
    index_filename : str
        The name of the index file to write.
    index_template : str
        The name of the template file to use.
    """

    # Index contains only a header
    _, header = read_markdownfile_with_header(index_filename)

    build_dir = os.path.join('_build', 'html')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    if theme is None:
        theme = header.get('theme', 'default')

    theme_dir = os.path.join('theme', theme)
    index_template = os.path.join(theme_dir, 'index.html')

    with open(index_template, 'r') as f:
        template = f.read()

    def merge_subdicts(root: dict) -> dict:
        res = root[0].copy()
        for sub in root[1:]:
            res.update(sub)
        return res

    event = merge_subdicts(header['event'])
    organizers = merge_subdicts(header['organizers'])
    imprint = merge_subdicts(header['imprint'])
    privacy = merge_subdicts(header['privacy-policy'])

    template = template.replace(r'{{event-title}}', event['title'])\
                       .replace(r'{{event-date}}', event['date'])\
                       .replace(r'{{event-venue}}', event['venue'])\
                       .replace(r'{{event-subtitle}}', event['subtitle'])\
                       .replace(r'{{organizer-logo}}', organizers['logo'])\
                       .replace(r'{{imprint-url}}', imprint['url'])\
                       .replace(r'{{imprint-name}}', imprint['name'])\
                       .replace(r'{{privacy-policy-url}}', privacy['url'])\
                       .replace(r'{{privacy-policy-name}}', privacy['name'])\
                       .replace(r'{{contact-url', organizers['contact_url'])\

    sections = []
    nav = []
    for section in header['content']:
        fname = os.path.join('content', section + '.md')
        if len(sections) % 2 == 0:
            section_class = ''
        else:
            section_class = "gray-bg"
        txt, reference = generate_section(fname, theme, section_class=section_class)
        if section == 'programme':
            txt, reference = generate_program(fname, theme, section_class=section_class)
        sections.append(txt)
        nav.append(reference)

    template = template.replace('{{sections}}', ''.join(sections))\
                       .replace('{{nav-content}}', '\n'.join(nav))

    # copy theme files
    shutil.copytree(theme_dir, build_dir)
    # copy static files
    shutil.copytree("static", os.path.join(build_dir, "static"))
    with open(os.path.join(build_dir, "index.html"), 'w') as f:
        f.write(template)
