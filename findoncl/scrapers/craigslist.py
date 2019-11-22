
import asyncio
import collections

from aiohttp import ClientSession
from bs4 import BeautifulSoup


class CraigslistRecord(collections.UserDict):
    @classmethod
    def from_dom(cls, *, dom=None, region=None, category=None):
        data = {
            'id': None,
            'title': dom.find(id='titletextonly').string,
            'region': region,
            'category': category,
            'price': None,
            'url': dom.find(rel='canonical').get('href'),
            'description': dom.find(id='postingbody').get_text(),
            'meta': {},
            'created': dom.find('time').get('datetime'),
        }

        price = dom.find(class_='price')
        data['price'] = price.string if price else None

        for postinfo in dom.find_all(class_='postinginfo'):
            postinfo_text = postinfo.string

            if not postinfo_text:
                continue

            if 'post id:' in postinfo_text:
                # todo: cast to int?
                data['id'] = postinfo_text.replace('post id: ', '')

        for attrgroup in dom.find_all(class_='attrgroup'):
            for attr in attrgroup.find_all('span'):
                attr_data = attr.get_text()

                if not attr_data:
                    continue

                if ':' in attr_data:
                    key, val = attr_data.split(': ', 1)
                else:
                    key = '_title'
                    val = attr_data

                data['meta'][key] = val

        return cls(**data)


class Craigslist():
    def __init__(self, regions, categories):

        if isinstance(regions, str):
            regions = [regions]

        if isinstance(categories, str):
            categories = [categories]

        if not isinstance(regions, collections.Sequence):
            raise TypeError('regions must be a list type')

        if not isinstance(categories, collections.Sequence):
            raise TypeError('cagetories must be a list type')

        self.regions = regions
        self.categories = categories
        self.session = ClientSession()

    async def run(self):
        sites = []
        for region in self.regions:
            for category in self.categories:
                sites.append(self.search_site(region, category))

        results = await asyncio.gather(*sites)
        return [item for result in results for item in result]

    def build_url(self, region, category):
        return f'https://{region}.craigslist.org/search/{category}'

    async def search_site(self, region, category):
        url = self.build_url(region, category)

        site = await self.fetch(url)
        advert_links = self.parse_search(site)
        data = await asyncio.gather(*[self.fetch(link) for link in advert_links])
        return [CraigslistRecord.from_dom(dom=dom, region=region, category=category) for dom in data]

    async def close(self):
        await self.session.close()

    async def fetch(self, url):
        async with self.session.get(url) as response:
            text = await response.text()
            return BeautifulSoup(text, 'lxml')

    def parse(self, dom):
        links = []
        for link in dom.find_all('a'):
            if 'hdrlnk' not in link.get('class', []):
                continue
            links.append(link.get('href'))

        return links
