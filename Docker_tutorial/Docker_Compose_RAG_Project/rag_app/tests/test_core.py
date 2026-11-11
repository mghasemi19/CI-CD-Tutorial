from app.core import split_text, format_context


def test_empty_string():
    assert split_text('   ') == []


def test_overlap():
    assert split_text('abcdefghij', size=6, overlap=2) == ['abcdef', 'efghij']


def test_invalid_overlap():
    try:
        split_text('abc', size=4, overlap=4)
    except ValueError:
        pass
    else:
        raise AssertionError('Expected ValueError')


def test_context_includes_sources():
    result = format_context(['Docker Compose manages services'], ['docker_compose.txt'])
    assert '[Source: docker_compose.txt]' in result
