from nose.tools import eq_
from allmychanges.models import AutocompleteData


def test_create_words_objects_for_autocomplete():
    data = AutocompleteData.objects.create(
        title='Hello world!',
        type='source')
    eq_(3, len(data.words2.all()))
    eq_(sorted(['hello', 'world!', 'hello world!']),
        sorted([item.word for item in data.words2.all()]))
