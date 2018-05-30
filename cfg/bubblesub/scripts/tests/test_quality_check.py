import re
import typing as T

import pytest
from bubblesub.ass.event import Event
from bubblesub.ass.event import EventList

from ..quality_check import Violation
from ..quality_check import check_ass_tags
from ..quality_check import check_double_words
from ..quality_check import check_durations
from ..quality_check import check_punctuation


def test_violation_single_event() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=0)
    violation = Violation(event_list[0], 'test')
    assert repr(violation) == '#1: test'


def test_violation_multiple_events() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=0)
    event_list.insert_one(1, start=0, end=0)
    violation = Violation([event_list[0], event_list[1]], 'test')
    assert repr(violation) == '#1+#2: test'


def test_check_durations_empty_text() -> None:
    event = Event(start=0, end=100)
    assert len(list(check_durations(event))) == 0


def test_check_durations_comment() -> None:
    event = Event(start=0, end=100, text='test', is_comment=True)
    assert len(list(check_durations(event))) == 0


def test_check_durations_too_short() -> None:
    event = Event(start=0, end=100, text='test')
    violations = list(check_durations(event))
    assert len(violations) == 1
    assert violations[0].text == 'duration shorter than 250 ms'


def test_check_durations_too_short_long_text() -> None:
    event = Event(start=0, end=100, text='test test test test test')
    violations = list(check_durations(event))
    assert len(violations) == 1
    assert violations[0].text == 'duration shorter than 500 ms'


def test_check_durations_good_duration() -> None:
    event = Event(start=0, end=501, text='test test test test test')
    assert len(list(check_durations(event))) == 0


def test_check_durations_too_short_gap() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=500, text='test')
    event_list.insert_one(1, start=600, end=900, text='test')
    violations = list(check_durations(event_list[0]))
    assert len(violations) == 1
    assert violations[0].text == 'gap shorter than 250 ms (100 ms)'


def test_check_durations_too_short_gap_empty_lines() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=500, text='test')
    event_list.insert_one(1, start=550, end=550)
    event_list.insert_one(2, start=600, end=900, text='test')
    violations = list(check_durations(event_list[0]))
    assert len(violations) == 1
    assert violations[0].text == 'gap shorter than 250 ms (100 ms)'


def test_check_durations_too_short_gap_comments() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=500, text='test')
    event_list.insert_one(1, start=550, end=550, text='test', is_comment=True)
    event_list.insert_one(2, start=600, end=900, text='test')
    violations = list(check_durations(event_list[0]))
    assert len(violations) == 1
    assert violations[0].text == 'gap shorter than 250 ms (100 ms)'


def test_check_durations_good_gap() -> None:
    event_list = EventList()
    event_list.insert_one(0, start=0, end=500, text='test')
    event_list.insert_one(1, start=750, end=900, text='test')
    assert len(list(check_durations(event_list[0]))) == 0


@pytest.mark.parametrize('text, violation_text', [
    ('Text\\N', 'extra line break'),
    ('\\NText', 'extra line break'),
    ('Text\\NText\\NText', 'three or more lines'),
    ('Text\\N Text', 'whitespace around line break'),
    ('Text \\NText', 'whitespace around line break'),
    ('Text ', 'extra whitespace'),
    (' Text', 'extra whitespace'),
    ('Text  text', 'double space'),
    ('...', 'bad ellipsis (expected …)'),
    ('What youve done', 'missing apostrophe'),
    ('- What?\\N- No!', 'bad dash (expected \N{EN DASH})'),
    ('\N{EM DASH}What?\\N\N{EM DASH}No!', 'bad dash (expected \N{EN DASH})'),
    ('\N{EM DASH}What?', 'bad dash (expected \N{EN DASH})'),
    ('- What?', 'bad dash (expected \N{EN DASH})'),
    ('\N{EN DASH} What!', 'dialog with just one person'),
    ('What--', 'bad dash (expected \N{EM DASH})'),
    ('What\N{EN DASH}', 'bad dash (expected \N{EM DASH})'),
    ('W-what?', 'possible wrong stutter capitalization'),
    ('Ayuhara-san', None),
    ('What! what…', 'lowercase letter after sentence end'),
    ('What. what…', 'lowercase letter after sentence end'),
    ('What? what…', 'lowercase letter after sentence end'),
    ('What , no.', 'whitespace before punctuation'),
    ('What !', 'whitespace before punctuation'),
    ('What .', 'whitespace before punctuation'),
    ('What ?', 'whitespace before punctuation'),
    ('What :', 'whitespace before punctuation'),
    ('What ;', 'whitespace before punctuation'),
    ('What\\N, no.', 'line break before punctuation'),
    ('What\\N!', 'line break before punctuation'),
    ('What\\N.', 'line break before punctuation'),
    ('What\\N?', 'line break before punctuation'),
    ('What\\N:', 'line break before punctuation'),
    ('What\\N;', 'line break before punctuation'),
    ('What?No!', 'missing whitespace after punctuation mark'),
    ('What!No!', 'missing whitespace after punctuation mark'),
    ('What.No!', 'missing whitespace after punctuation mark'),
    ('What,no!', 'missing whitespace after punctuation mark'),
    ('What:no!', 'missing whitespace after punctuation mark'),
    ('What;no!', 'missing whitespace after punctuation mark'),
    ('What…no!', 'missing whitespace after punctuation mark'),
    ('What? No!', None),
    ('What! No!', None),
    ('What. No!', None),
    ('What, no!', None),
    ('What: no!', None),
    ('What; no!', None),
    ('What… no!', None),
    ('What?\\NNo!', None),
    ('What!\\NNo!', None),
    ('What.\\NNo!', None),
    ('What,\\Nno!', None),
    ('What:\\Nno!', None),
    ('What;\\Nno!', None),
    ('What…\\Nno!', None),
    ('test\ttest', 'unrecognized whitespace'),
    ('test\N{ZERO WIDTH SPACE}test', 'unrecognized whitespace'),
    ('….', 'extra comma or dot'),
    (',.', 'extra comma or dot'),
    ('?.', 'extra comma or dot'),
    ('!.', 'extra comma or dot'),
    (':.', 'extra comma or dot'),
    (';.', 'extra comma or dot'),
    ('…,', 'extra comma or dot'),
    (',,', 'extra comma or dot'),
    ('?,', 'extra comma or dot'),
    ('!,', 'extra comma or dot'),
    (':,', 'extra comma or dot'),
    (';,', 'extra comma or dot'),
])
def test_check_punctuation(text: str, violation_text: T.Optional[str]) -> None:
    event = Event(text=text)
    violations = list(check_punctuation(event))
    if violation_text is None:
        assert len(violations) == 0
    else:
        assert len(violations) == 1
        assert violations[0].text == violation_text


@pytest.mark.parametrize('text, violation_text_re', [
    ('text', None),
    ('{\\an8}', None),
    ('text{\\b1}text', None),
    ('{\\fsherp}', 'invalid syntax (.*)'),
    ('{}', 'pointless ASS tag'),
    ('{\\\\comment}', 'use notes to make comments'),
    ('{\\comment}', 'invalid syntax (.*)'),
    ('{\\a5}', 'using legacy alignment tag'),
    ('{\\an8comment}', 'use notes to make comments'),
    ('{comment\\an8}', 'use notes to make comments'),
    ('{\\an8}{\\fs5}', 'disjointed tags'),
])
def test_check_ass_tags(text, violation_text_re):
    event_list = EventList()
    event_list.insert_one(0, text=text)
    violations = list(check_ass_tags(event_list[0]))
    if violation_text_re is None:
        assert len(violations) == 0
    else:
        assert len(violations) == 1
        assert re.match(violation_text_re, violations[0].text)


@pytest.mark.parametrize('text, violation_text', [
    ('text', None),
    ('text text', 'double word (text)'),
    ('text{} text', 'double word (text)'),
    ('text{}\\Ntext', 'double word (text)'),
    ('text{}text', None),
])
def test_check_double_words(text, violation_text):
    event_list = EventList()
    event_list.insert_one(0, text=text)
    violations = list(check_double_words(event_list[0]))
    if violation_text is None:
        assert len(violations) == 0
    else:
        assert len(violations) == 1
        assert violations[0].text == violation_text
