import jwt
import uuid
import typing
import hashlib
import logging
import datetime
import requests
import functools

from django.http import HttpRequest
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators import http
from django.shortcuts import redirect
from django.conf import settings
from django.core.exceptions import PermissionDenied

from .models import Post
from .models import Comment

from .forms import CreatePostForm
from .forms import CommentPostForm

log = logging.getLogger(__name__)

FILE_MANAGER_API_KEY = "6d207e02198a847aa98d0a2a901485a5"


def get_ip_from_request(meta: dict) -> str:
    log.info(f"Getting IP from {meta}")
    x_forwarded_for: str = meta.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = meta.get('REMOTE_ADDR')
    return ip


def get_country_code_from_ip(meta: dict) -> str:
    log.info(f"Get country info from {meta}")

    ip = get_ip_from_request(meta)
    if ip:
        log.info(f"Retrieving geo-information from ip: {ip}")
        try:
            response = requests.get(f'https://api.ipgeolocationapi.com/geolocate/{ip}')
            if response.status_code == 200:
                country_code = response.json()['alpha2']
                log.info(f"Country code for ip: {ip}, {country_code}")
                return country_code
            else:
                log.error(f"Failed to retrieve geo information from ip: {ip}, {response.content}")
        except Exception as err:
            log.error(f"Failed to retrieve geo information from ip: {ip}, using default", err)
    return 'AR'


def get_signature(request: HttpRequest, fail_on_missing: bool = True) -> typing.Optional[str]:
    signature = request.session.get('signature')
    if not signature and fail_on_missing:
        log.error("Missing signature from session!")
        raise PermissionDenied()
    return signature


def get_session_model(request: HttpRequest, fail_on_missing: bool = True) -> typing.Optional[dict]:
    session_model = request.session.get('model')
    if not session_model:
        if fail_on_missing:
            log.error("Missing model from session!")
            raise PermissionDenied()
        else:
            return None
    try:
        return jwt.decode(session_model, settings.SECRET_KEY)
    except Exception as err:
        log.error(f"Unable to verify session model: {session_model}", err)
        if fail_on_missing:
            raise PermissionDenied()
        else:
            return None


def validate_signature(model: dict, signature: str) -> bool:
    expected = jwt.encode(model, settings.SECRET_KEY)
    expected = hashlib.sha512(expected).hexdigest()
    return signature == expected


def delete_from_session(request: HttpRequest, field: str) -> typing.NoReturn:
    try:
        del request.session[field]
    except KeyError:
        pass


def required_session_signed(func: typing.Callable):
    @functools.wraps(func)
    def wrap(request: HttpRequest, *args, **kwargs):
        delete_session = False

        try:
            model = get_session_model(request)
            signature = get_signature(request)

            if not validate_signature(model, signature):
                log.error("Unable to complete operation, missmatch between model and signature in session!")
                delete_session = True

        except PermissionDenied as err:
            log.error(f"Unable to complete operation, missing required fields from session!", err)
            delete_session = True

        if delete_session:
            delete_from_session(request, 'signature')
            delete_from_session(request, 'model')
            return HttpResponse(status=401)

        return func(request, *args, **kwargs)
    return wrap


@http.require_POST
@required_session_signed
def create_post(request: HttpRequest) -> HttpResponse:
    creation = CreatePostForm(request.POST, request.FILES)
    if creation.is_valid():
        post = Post()
        post.tag = creation.get_tag()
        post.title = creation.cleaned_data['title']
        post.raw_content = creation.cleaned_data['content']
        if creation.cleaned_data['attached_img']:
            post.attached_img = creation.cleaned_data['attached_img']
        post.views = 0
        post.location = get_country_code_from_ip(request.META)
        post.signature = get_signature(request)

        post.save()

        for hashtag in creation.get_hashtags_from_content():
            post.hashtags.add(hashtag)

        log.info(f"New post created: {post}")
        return redirect(f'/p/{str(post.uuid)}')
    else:
        log.error(f"Unable to create post due to validation errors: {creation.errors}")
        return HttpResponse(status=500, content=str(creation.errors), content_type='text/html')


@http.require_POST
@required_session_signed
def create_comment(request: HttpRequest, post_no: int) -> HttpResponse:
    form = CommentPostForm(request.POST, request.FILES)
    if form.is_valid():
        comment = Comment()
        comment.raw_content = form.cleaned_data['content']
        comment.location = get_country_code_from_ip(request.META)

        comment.post = Post.objects.get(pk=post_no)

        signature = get_signature(request, fail_on_missing=False)
        comment.is_from_op = signature == comment.post.signature

        if form.cleaned_data['attached_img']:
            comment.attached_img = form.cleaned_data['attached_img']

        comment.save()
        log.info(f"New comment created: {comment}")
        return redirect(f'/p/{comment.post.uuid}')
    else:
        log.error(f"Unable to create comment due to validation errors: {form.errors}")
        return HttpResponse(status=500, content=str(form.errors), content_type="text/html")


@http.require_POST
def sign_session(request: HttpRequest) -> HttpResponse:
    redirect_to = request.POST.get('redirect', '/')
    if not get_session_model(request, fail_on_missing=False):
        model = {
            'ip': get_ip_from_request(request.META),
            'signature': str(uuid.uuid4())
        }
        model = jwt.encode(model, settings.SECRET_KEY)
        signature = hashlib.sha512(model).hexdigest()

        request.session['model'] = model.decode('utf-8')
        request.session['signature'] = signature

    return redirect(redirect_to)


@http.require_GET
def get_count_new_comments(request: HttpRequest, post_no: int) -> HttpResponse:
    start = request.GET.get('start', None)

    if not start:
        return JsonResponse({}, status=400)

    created_at = datetime.datetime.fromtimestamp(int(start))
    post = Post.objects.get(pk=post_no)

    log.info(f"Searching comments from post {post.no} that were created after {created_at}")

    comments = post.comment_set.filter(created_at__gte=created_at).count()
    return JsonResponse({
        "comments": comments
    })
