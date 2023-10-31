from unittest import mock
from unittest.mock import Mock, patch

import bs4
import pytest
from bs4 import NavigableString

from sec_parser.processing_engine.html_tag import EmptyNavigableStringError, HtmlTag


def test_init_with_non_empty_navigable_string():
    # Arrange
    nav_string = NavigableString("Hello")

    # Act
    with patch("warnings.warn") as mock_warn:
        html_tag = HtmlTag(nav_string)

    # Assert
    mock_warn.assert_called()
    tag = html_tag._bs4  # separate variable for readability
    assert isinstance(tag, bs4.Tag)
    assert tag.name == "span"
    assert tag.string == "Hello"


def test_init_with_empty_navigable_string():
    # Arrange
    nav_string = NavigableString("")

    # Act & Assert
    with pytest.raises(EmptyNavigableStringError):
        HtmlTag(nav_string)


def test_init_with_unsupported_type():
    # Arrange
    unsupported_element = 42  # an integer

    # Act & Assert
    with pytest.raises(TypeError):
        HtmlTag(unsupported_element)


def test_without_tags():
    # Arrange
    soup = bs4.BeautifulSoup("<div><p>Text <b>inside</b> a paragraph</p></div>", "html.parser")
    div_tag = soup.find("div")
    html_tag = HtmlTag(div_tag)

    # Act
    without_b_tag = html_tag.without_tags(["b"])

    # Assert
    actual = without_b_tag.get_source_code(pretty=True)
    assert actual == "<div>\n <p>\n  Text\n  a paragraph\n </p>\n</div>\n"


def test_to_dict():
    # Arrange
    tag = bs4.Tag(name="span")
    tag.string = "A" * 60

    # Act
    actual = HtmlTag(tag).to_dict()

    # Assert
    assert actual == {
        "tag_name": "span",
        "text_preview": "AAAAAAAAAAAAAAAAAAAA...[20]...AAAAAAAAAAAAAAAAAAAA",
        "html_preview": "<span>AAAAAAAAAAAAAA...[33]...AAAAAAAAAAAAA</span>",
        "html_hash": "3836a62b",
    }


@pytest.mark.parametrize(
    ("name", "html_string", "expected"),
    values := [
        ("root_with_single_child", "<div><p></p></div>", True),
        ("root_with_string", "<div><p></p>Hello</div>", False),
        ("root_with_multiple_children", "<div><p></p><a></a></div>", False),
        ("deep_unary_tree", "<div><p><a><i></i></a></p></div>", True),
        ("table", "<div><table><tr><a></a><i></i></tr></table></div>", True),
    ],
    ids=[v[0] for v in values],
)
def test_is_unary_tree(name, html_string, expected):
    # Arrange
    soup = bs4.BeautifulSoup(html_string, "html.parser")
    div_tag = soup.find("div")
    html_tag = HtmlTag(div_tag)

    # Act
    actual = html_tag.is_unary_tree()

    # Assert
    assert actual==expected


def test_get_pretty_source_code():
    # Arrange
    tag = bs4.Tag(name="div")
    tag.string = "Hello, world!"
    html_tag = HtmlTag(tag)

    # Act
    pretty_source_code = html_tag.get_source_code(pretty=True)

    # Assert
    assert pretty_source_code == "<div>\n Hello, world!\n</div>\n"


@pytest.mark.parametrize(
    ("method_to_call", "method_to_patch"),
    values := [
        (
            "get_approx_table_metrics",
            "sec_parser.processing_engine.html_tag.get_approx_table_metrics",
        ),
    ],
    ids=[v[0] for v in values],
)
def test_wrappers(method_to_patch, method_to_call):
    # Arrange
    html_tag = HtmlTag(Mock(spec=bs4.Tag))

    # Act
    with mock.patch(method_to_patch) as mocked_function:
        getattr(html_tag, method_to_call)()

    # Assert
    mocked_function.assert_called_once()


def test_wrap_tags_in_new_parent():
    # Arrange
    tag1 = bs4.Tag(name="p")
    tag1.string = "This is the first paragraph."

    tag2 = bs4.Tag(name="p")
    tag2.string = "This is the second paragraph."

    html_tag1 = HtmlTag(tag1)
    html_tag2 = HtmlTag(tag2)

    # Act
    new_parent_tag_name = "div"
    new_parent = html_tag1.wrap_tags_in_new_parent(new_parent_tag_name, [html_tag1, html_tag2])

    # Assert
    assert new_parent.name == new_parent_tag_name
    assert new_parent.get_source_code(pretty=True) == "<div>\n <p>\n  This is the first paragraph.\n </p>\n <p>\n  This is the second paragraph.\n </p>\n</div>\n"