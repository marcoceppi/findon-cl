
import pytest
import asynctest

from unittest.mock import patch

from findoncl.scrapers.craigslist import Craigslist


def test_Craigslist_build_url():
    c = Craigslist(regions=[], categories=[])
    assert 'https://my-region.craigslist.org/search/scategories' == c.build_url('my-region', 'scategories')


def test_Craigslist():
    c = Craigslist(regions=[], categories='cta')
    assert [] == c.regions
    assert ['cta'] == c.categories

    c = Craigslist(regions='washdc', categories=['cta'])
    assert ['washdc'] == c.regions
    assert ['cta'] == c.categories

    c = Craigslist(regions='washdc', categories='cta')
    assert ['washdc'] == c.regions
    assert ['cta'] == c.categories


def test_Craigslist_bad_values():
    with pytest.raises(TypeError):
        Craigslist(regions=[], categories=None)

    with pytest.raises(TypeError):
        Craigslist(regions=None, categories=[])


@pytest.mark.asyncio
@patch('findoncl.scrapers.craigslist.ClientSession')
async def test_Craigslist_close(mock_client_session):
    mock_client_session.return_value.close = asynctest.CoroutineMock()
    c = Craigslist(regions=[], categories=[])
    await c.close()
    mock_client_session.return_value.close.assert_called()


@pytest.mark.asyncio
async def test_Craigslist_run():
    with patch.object(Craigslist, 'search_site', new_class=asynctest.CoroutineMock) as mock_search_site:
        mock_search_site.return_value = ['test', 'success', 'a cl record']
        c = Craigslist(regions=['test'], categories=['electronics'])
        records = await c.run()
        mock_search_site.assert_called_with('test', 'electronics')
        assert ['test', 'success', 'a cl record'] == records
