import pytest
from C_DefineParser import remove_comment


@pytest.mark.parametrize("src, out_expected", [
    ('ENV // bbb', 'ENV '),
    ('EN/**/V', 'EN    V'),
    ('EN/**/V/**/A', 'EN    V    A'),
    ('EN/* gg */V', 'EN        V'),
    ('EN/*\n123*/ggg', 'EN\n     ggg'),
])
def test_line_commend(src, out_expected):
    out = "\n".join(remove_comment(src.splitlines()))
    assert out == out_expected
