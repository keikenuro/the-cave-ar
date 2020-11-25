import re

from django import template
from django.utils import html
from django.template import defaultfilters
from django.utils.safestring import mark_safe


register = template.Library()


def _get_hashtags_from_content(content: str) -> str:
    if content and content != '':
        for hashtag in re.findall(r"((?<!\w)\#[a-zA-Z0-9]*)", content):
            hashtag = hashtag.replace('#', '')
            if hashtag != '':
                content = content.replace('#' + hashtag, f'<a href="/hashtag/{hashtag.lower()}">#{hashtag}</a>')
    return mark_safe(content)


def _get_replies(content: str, context) -> str:
    token = ":::"
    if content and content != '':
        for reply in re.findall(r"((?<!\w):::[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12})", content):
            content = content.replace(reply, f'<a href="{context.path + reply.replace(token, "#")}">{reply}</a>')
    return mark_safe(content)


@defaultfilters.stringfilter
@register.filter(name='beautify', needs_autoescape=True)
def beautify(text, autoescape=True):
    return defaultfilters.linebreaksbr(
        defaultfilters.urlize(
            _get_hashtags_from_content(content=html.escape(text)),
            autoescape=autoescape), autoescape=autoescape)


@defaultfilters.stringfilter
@register.filter(name='beautify_comment', needs_autoescape=True)
def beautify_comment(text, context, autoescape=True):
    return _get_replies(defaultfilters.linebreaksbr(
        defaultfilters.urlize(
            _get_hashtags_from_content(html.escape(text)),
            autoescape=autoescape), autoescape=autoescape), context)
