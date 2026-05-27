import pytest

from fastcms.resource import Resource

from tests.conftest import Article


def test_resource_valid():
    class ArticleResource(Resource):
        model = Article

    assert ArticleResource.model is Article


def test_resource_missing_model():
    with pytest.raises(TypeError, match="must define 'model'"):

        class BadResource(Resource):
            pass


def test_resource_default_fields():
    class ArticleResource(Resource):
        model = Article

    assert ArticleResource.search_fields == []
    assert ArticleResource.sort_fields == []
    assert ArticleResource.prefix is None
    assert ArticleResource.tags is None
