from nose.tools import eq_
from allmychanges.models import AutocompleteData


def test_create_words_objects_for_autocomplete():
    data = AutocompleteData.objects.create(
        title='Hello world!',
        type='source')
    eq_(2, len(data.words.all()))
