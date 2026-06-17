import pytest

from fastcms.resource import Action, ALL_ACTIONS, Resource

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


def test_resource_default_actions_is_all():
    class ArticleResource(Resource):
        model = Article

    assert ArticleResource.actions == ALL_ACTIONS
    assert ArticleResource.actions == frozenset(Action)


def test_resource_actions_can_be_restricted():
    class ReadOnlyResource(Resource):
        model = Article
        actions = frozenset({Action.LIST, Action.RETRIEVE})

    assert ReadOnlyResource.actions == {Action.LIST, Action.RETRIEVE}
    assert Action.CREATE not in ReadOnlyResource.actions
