import re
import typing
import logging

from django import forms

from .models import Tag
from .models import HashTag

log = logging.getLogger(__name__)


def _get_hashtags_from_content(content: str) -> typing.List[HashTag]:
    hashtags = []

    log.info(f"Getting hashtags from content: {content:>50}")
    if content and content != '':
        for pk in re.findall(r"(\#[a-zA-Z0-9]*)", content):
            hashtag, created = HashTag.objects.get_or_create(name=pk.lower().replace('#', ''))
            if not created:
                hashtag.save()
            hashtags.append(hashtag)
    log.info(f"Hashtags from content {content:>50}: {hashtags}")

    return hashtags


class CreatePostForm(forms.Form):
    title = forms.CharField(max_length=250, min_length=1)
    content = forms.CharField(min_length=1)
    tag = forms.CharField(min_length=1, max_length=250)
    attached_img = forms.ImageField(allow_empty_file=True)

    def get_hashtags_from_content(self) -> typing.List[HashTag]:
        content = self.cleaned_data['content']
        return _get_hashtags_from_content(content)

    def get_tag(self) -> Tag:
        return Tag.objects.get(pk=self.cleaned_data['tag'])


class CommentPostForm(forms.Form):
    content = forms.CharField(min_length=1)
    attached_img = forms.ImageField(allow_empty_file=True, required=False)

    def get_hashtags_from_content(self) -> typing.List[HashTag]:
        content = self.cleaned_data['content']
        return _get_hashtags_from_content(content)
