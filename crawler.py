import os, re, csv
import requests
import bs4
from math import ceil
from subprocess import Popen, PIPE
from io import StringIO

DIR = os.path.split(os.path.abspath(__file__))[0]


class Crawler:

    URL = "http://www.vestnik.udm.net/"
    ENCODING = 'utf-8'

    CSV_HEADERS = (
        'path',
        'author',
        'sex',
        'birthday',
        'header',
        'created',
        'sphere',
        'genre_fi',
        'type',
        'topic',
        'chronotop',
        'style',
        'audience_age',
        'audience_level',
        'audience_size',
        'source',
        'publication',
        'publisher',
        'publ_year',
        'medium',
        'country',
        'region',
        'language'
    )

    OUT_PATH = DIR + '\\газета\\'
    CSV_PATH = OUT_PATH + '\\' + 'metadata.csv'

    _csv = None
    _csv_file = None

    def __init__(self, metadata=True):
        if metadata:
            if not os.path.exists(os.path.split(self.CSV_PATH)[0]):
                os.makedirs(os.path.split(self.CSV_PATH)[0])
            self._csv_file = open(self.CSV_PATH, 'w')
            self._csv = csv.DictWriter(self._csv_file, self.CSV_HEADERS, delimiter='\t')
            self._csv.writeheader()

    def count_links_per_page(self):
        return requests.get(self.URL).text.count("h2") / 2

    def get_links(self, max_count):
        lpp = self.count_links_per_page()
        pages = ceil(max_count / lpp)
        links = []
        for i in range(pages):
            page_result = requests.get("%s?paged=%i" % (self.URL, i+1))
            if page_result.status_code == requests.codes.ok:
                dom = bs4.BeautifulSoup(page_result.text, 'html.parser')
                for h2 in dom('h2'):
                    if h2.a is not None:
                        links.append(h2.a['href'])
                    if len(links) == max_count:
                        break
        return links

    def get_data(self, link):
        def escape(string):
            return (
                string
                    #.replace('\xa0', ' ')
                    #.replace('\x85', '...')
                    #.replace('\x91', "'")
                    #.replace('\x92', "'")
                    #.replace('\x93', '"')
                    #.replace('\x94', '"')
                    #.replace('\x96', '-')
                    #.replace('\x97', '-')
                    .replace(chr(0xf0fc), '\t')
            )
        data = {}
        page_result = requests.get(link)
        if page_result.status_code == requests.codes.ok:
            page_result.encoding = self.ENCODING
            dom = bs4.BeautifulSoup(page_result.text, 'html.parser')

            content = dom.find('div', attrs={'class': 'entry-content'})
            data.update({
                'content': escape(content.get_text().strip('\n\r\xa0 '))
            })

            header = dom.find('h1', attrs={'class': 'entry-title'})
            data.update({
                'header': escape(header.get_text().strip('\n\r\xa0 '))
            })

            date = dom.find('span', attrs={'class': 'entry-date'}).get_text()
            datelist = date.split('.')
            data.update({'date': date})
            publ_year = datelist[2]
            data.update({'publ_year': publ_year})

            author = dom.find('span', attrs={'class': 'author vcard'}).a.get_text()
            data.update({
                'author': author
            })

            topic = dom.find('a', attrs={'rel': 'category'}).get_text()
            data.update({
                'topic': topic
            })

            data.update({
                'source': escape(link)
            })

            data.update({
                'sex': '',
                'birthday': '',
                'sphere': 'публицистика',
                'genre_fi': '',
                'type': '',
                'chronotop': '',
                'style': 'нейтральный',
                'audience_age': 'н-возраст',
                'audience_level': 'н-уровень',
                'audience_size': 'районная',
                'publication': 'Вестник',
                'publisher': '',
                'medium': 'газета',
                'country': 'Россия',
                'region': 'Удмуртская Республика',
                'language': 'ru'
            })
        return data

    def create_files(self, data):
        datelist = data['date'].split('.')
        month = int(datelist[1])
        year = int(datelist[2])
        header = re.sub(r'[\\/*?:"<>|]', "", data['header'])
        src_plain_path = "%s\\plain\\%i\\%i\\%s.txt" % (self.OUT_PATH, year, month, header)
        mystem_plain_path = "%s\\mystem-plain\\%i\\%i\\%s.txt" % (self.OUT_PATH, year, month, header)
        mystem_xml_path = "%s\\mystem-xml\\%i\\%i\\%s.xml" % (self.OUT_PATH, year, month, header)

        if not os.path.exists(os.path.split(src_plain_path)[0]):
            os.makedirs(os.path.split(src_plain_path)[0])
        if not os.path.exists(os.path.split(mystem_plain_path)[0]):
            os.makedirs(os.path.split(mystem_plain_path)[0])
        if not os.path.exists(os.path.split(mystem_xml_path)[0]):
            os.makedirs(os.path.split(mystem_xml_path)[0])

        with StringIO(data['content']) as content_io:
            with open(mystem_plain_path, 'wb') as o:
                Mystem.process(content_io, o)
            content_io.seek(0)
            with open(mystem_xml_path, 'wb') as o:
                Mystem.process(content_io, o, True)
            content_io.seek(0)
            with open(src_plain_path, 'w') as f:
                f.write(
                    "@au %s\n@ti %s\n@da %s\n@topic %s\n@url %s\n%s"
                    % (
                        data['author'],
                        data['header'],
                        data['date'],
                        data['topic'],
                        data['source'],
                        content_io.read()
                    )
                )
        data.update({'path': "plain\\%i\\%i\\%s.txt" % (year, month, header)})
        return data

    def update_metadata(self, data):
        if self._csv is not None:
            clean_data = {}
            for k in data.keys():
                if k in self.CSV_HEADERS:
                    clean_data.update({k: data[k]})
            self._csv.writerow(clean_data)


class Mystem:

    EXE = DIR + '\\mystem.exe'

    @staticmethod
    def process(src_file, out_file, xml=False):
        cmd = [Mystem.EXE, "-e", Crawler.ENCODING, "--format"]
        if xml:
            cmd.append("xml")
        else:
            cmd.append("text")
        out = Popen(cmd, stdin=PIPE, stdout=PIPE) \
            .communicate(bytes(src_file.read(), Crawler.ENCODING))[0]
        out_file.write(out)
