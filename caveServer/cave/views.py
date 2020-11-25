import datetime

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators import http
from django.views.generic.list import ListView
from django.db.models import Count, Sum, Q
# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.conf import settings

from .models import Tag
from .models import Post
from .models import Comment
from .models import HashTag

from caveServer import website


class Home(ListView):
    model = Post
    paginate_by = 6
    extra_context = {
        'default_tag': 'Select tag from here...',
        'tags': Tag.objects.filter().all()
    }
    context_object_name = 'posts'
    template_name = 'home.html'
    queryset = Post.objects.annotate(
        num_comment=Count('comment'))
    ordering = ['-created_at', '-no', '-num_comment', '-views']


# @method_decorator(cache_page(5*60), name='dispatch')
class Hot(ListView):
    model = Post
    paginate_by = 15
    context_object_name = 'posts'
    template_name = 'hot.html'
    queryset = Post.objects.annotate(
        num_comment=Count('comment'))
    ordering = ['-num_comment', '-views']


# @method_decorator(cache_page(60*60), name='dispatch')
class Tags(ListView):
    model = Tag
    context_object_name = 'tags'
    template_name = 'tags.html'
    queryset = Tag.objects.all().annotate(posts=Count('post'))
    ordering = ['name']


@http.require_GET
# @cache_page(60*60)
def stats(request: HttpRequest) -> HttpResponse:
    context: dict = {
        'posts': [
            ('Total', Post.objects.count()),
            ('Created last hour', Post.objects.filter(
                created_at__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()),
            ('Created today', Post.objects.filter(
                created_at__gte=datetime.datetime.now() - datetime.timedelta(days=1)).count()),
            ('Total views', Post.objects.aggregate(total_views=Sum('views'))['total_views']),
            ('Most viewed post', Post.objects.order_by('-views').first().uuid),
            ('Most commented post', Post.objects.annotate(
                num_comment=Count('comment')).order_by('-comment').first().uuid),
            ('Country with most posts ', Post.objects.values_list('location')
                .annotate(location_count=Count('location'))
                .order_by('-location_count')
                .first())
        ],
        'comments': [
            ('Total', Comment.objects.count()),
            ('Total with images', Comment.objects.filter(~Q(attached_img='')).count()),
            ('Created last hour', Comment.objects.filter(
                created_at__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).count()),
            ('Created today', Comment.objects.filter(
                created_at__gte=datetime.datetime.now() - datetime.timedelta(days=1)).count()),
            ('Country with most comments ', Comment.objects.values_list('location')
             .annotate(location_count=Count('location'))
             .order_by('-location_count')
             .first())
        ],
        'tags': [
            ('Total', Tag.objects.count()),
        ],
        'hashtags': [
            ('Total', HashTag.objects.count())
        ],
        'server': [(k, v) for k, v in website.WEBSITE_INFO.items()]
    }

    for tag in Tag.objects.all():
        context['tags'].append((f'{tag.description} total', Post.objects.filter(tag=tag).count()))
        context['tags'].append((f'{tag.description} favourite country', Post.objects.filter(tag=tag)
            .values_list('location')
            .annotate(location_count=Count('location'))
            .order_by('-location_count')
            .first()))

    for hashtag in HashTag.objects.all():
        context['hashtags'].append((f'{hashtag.name} created at', hashtag.created_at))
        context['hashtags'].append((f'{hashtag.name} total used in posts', hashtag.post_set.count()))
        context['hashtags'].append((f'{hashtag.name} most used in country', hashtag.post_set.values_list('location')
             .annotate(location_count=Count('location'))
             .order_by('-location_count')
             .first()))

    return render(request, 'stats.html', context=context)


@http.require_GET
def post(request: HttpRequest, uuid: str) -> HttpResponse:
    post_obj = Post.objects.get(uuid=uuid)

    post_obj.views += 1
    post_obj.save()

    context = {
        'post': post_obj,
        'check_comments_interval_in_millis': settings.CHECK_COMMENTS_INTERVAL_IN_MILLIS
    }
    return render(request, 'post.html', context=context)


@http.require_GET
def posts_by_tag(request: HttpRequest, name: str) -> HttpResponse:
    try:
        tag = Tag.objects.get(pk=name)
        posts = Post.objects.filter(tag=tag).order_by('-no')
    except Tag.DoesNotExist:
        return render(request, 'tag.html', context={
            'posts': [],
            'tag': Tag(name=name, description=name)
        })

    paginator = Paginator(posts, 9)
    page_number = request.GET.get(key='page', default=1)

    return render(request, 'tag.html', context={
        'posts': paginator.get_page(page_number),
        'tag': tag
    })


@http.require_GET
def posts_by_hashtag(request: HttpRequest, name: str) -> HttpResponse:
    try:
        hashtag = HashTag.objects.get(pk=name.lower().replace('#', ''))
        posts = Post.objects.filter(hashtags__name=name.lower().replace('#', '')).order_by('-views')
    except HashTag.DoesNotExist:
        return render(request, 'hashtag.html', context={
            'posts': [],
            'hashtag': HashTag(name=name)
        })

    paginator = Paginator(posts, 9)
    page_number = request.GET.get(key='page', default=1)

    return render(request, 'hashtag.html', context={
        'posts': paginator.get_page(page_number),
        'hashtag': hashtag
    })
