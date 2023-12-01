import re
import requests
from bs4 import BeautifulSoup


class JournalParser:
    ARCHIVE_PATH = 'index.php/LFWB/issue/archive'
    def __init__(self, url):
        self.url = url
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/114.0.0.0 Safari/537.36',
        }

    def get_available_years(self):
        archive_url = self.url + self.ARCHIVE_PATH
        years = list()
        while True:
            response = requests.get(archive_url, headers=self.headers)
            # response.encoding = 'utf8'
            soup = BeautifulSoup(response.text, 'lxml')

            curr_years = soup.find_all('h3')
            for item in curr_years:

                if item.text not in years:
                    years.append(item.text)

            next_hyperlink = soup.find('a', class_="next")
            if next_hyperlink is None:
                break
            archive_url = next_hyperlink.attrs['href']
        return years

    def get_available_numbers(self, year):
        archive_url = self.url + self.ARCHIVE_PATH
        numbers = list()
        while True:
            response = requests.get(archive_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'lxml')

            archive_list = soup.find('ul', class_='issues_archive')
            if archive_list is None:
                break
            curr_items = archive_list.find_all('li')
            for item in curr_items:
                if item.find('h3', string=str(year)) is not None:
                    issue_items = item.find_all('a', class_='title')
                    if not len(issue_items):
                        continue
                    for issue in issue_items:
                        if issue.text not in numbers:
                            numbers.append(issue.text.strip())
            next_hyperlink = soup.find('a', class_="next")
            if next_hyperlink is None:
                break
            archive_url = next_hyperlink.attrs['href']
        return numbers

    def get_issue_data(self, year, number):
        archive_url = self.url + self.ARCHIVE_PATH
        while True:
            response = requests.get(archive_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'lxml')

            curr_items = soup.find_all('li')
            for item in curr_items:
                if item.find('h3', string=str(year)) is not None:
                    issue_items = item.find_all('a', class_='title')
                    if issue_items is None:
                        continue
                    for issue in issue_items:
                        if issue.text.strip() == number:
                            issue = self.load_issue_data(issue.attrs['href'])
                            return issue

            next_hyperlink = soup.find('a', class_="next")
            if next_hyperlink is None:
                break
            archive_url = next_hyperlink.attrs['href']

    def load_issue_data(self, url):
        issue = dict()
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')

        issue['url'] = url
        header = soup.find('h1').text
        issue['year'] = re.search(r'20\d{2}', header)[0]
        issue['number'] = re.search(r'(?<=№)\s*\d+', header)[0].strip()
        div = soup.find('div', class_='pub_id doi')
        if div is not None:
            issue['doi'] = div.find('a').attrs['href'].replace(r'https://doi.org/', '')

        div = soup.find('div', class_='published')
        if div is not None:
            issue['data'] = div.find('span', class_='value').text.strip()

        articles = list()
        divs = soup.findAll('div', class_='obj_article_summary')
        if divs is not None:
            for div in divs:
                article_url = div.find('a').attrs['href']
                article = self.load_article_data(article_url)
                article['pages'] = div.find('div', class_='pages').text.strip()
                articles.append(article)
        issue['article'] = articles
        return issue

    def load_article_data(self, url):
        article = dict()
        if url is None:
            return article

        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')

        article['url'] = url
        article['title'] = soup.find('h1', class_='page_title').text.strip()

        tag_text = str(soup.find('ul', class_='authors'))
        authors_match = re.search(r'<li>.+</li>', tag_text, flags=re.DOTALL)
        authors_data = self.get_authors_data(authors_match[0])
        article['authors'] = authors_data

        end_authors = authors_match.end()
        # -5 - для того, чтобы убрать </ul>
        organizations_raw = tag_text[end_authors: -5]
        organizations = self.get_organizations(organizations_raw)
        article['organizations'] = organizations

        section = soup.find('section', class_='item doi')
        article['doi'] = section.find('a').attrs['href'].replace(r'https://doi.org/', '')
        section = soup.find('section', class_='item abstract')
        if section is not None:
            p = section.find('p')
            if p is not None:
                article['abstract'] = p.text.strip()
            else:
                h2 = section.find('h2')
                if h2 is not None:
                    h2.decompose()
                article['abstract'] = section.text.strip()
        else:
            article['abstract'] = None

        return article

    @staticmethod
    def get_authors_data(author_raw):
        soup = BeautifulSoup(author_raw, 'lxml')
        author_items = soup.find_all('li')

        author_data = list()
        for item in author_items:
            author = dict()
            spans = item.find_all('span')
            for span in spans:
                small = span.find('small')
                # если нет маленьких символов - это автор
                if small is None:
                    # <span class="orcid" style="display:inline">
                    # <a href="https://orcid.org/0000-0002-5850-002X" target="_blank">
                    # <img alt="ID" src="/public/site/images/webadmin/ID.png"/>
                    # </a>
                    # </span>
                    if span.string is None:
                        continue
                    author['name'] = span.string.strip()
                # если есть маленькие символы - это аффилиация
                else:
                    affiliations = re.split(r'\s*,\s*', small.string.strip())
                    author['affiliation'] = [int(x) for x in affiliations]
            if len(author):
                author_data.append(author)
        return author_data

    @staticmethod
    def get_organizations(organizations_raw):
        # убираем цифры
        organizations_raw = re.sub(r'<small>.+?</small>\s*', "", organizations_raw.strip())
        # разделим на подстроки
        organizations = re.split(r'\s*<br\s*/>\s*', organizations_raw)
        return organizations
