from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import api
from . import views

urlpatterns = [
    path('', views.Home.as_view()),
    path('hot', views.Hot.as_view()),
    path('stats', views.stats),
    path('p/<slug:uuid>', views.post),
    path('tags', views.Tags.as_view()),
    path('tags/<slug:name>', views.posts_by_tag),
    path('hashtag/<slug:name>', views.posts_by_hashtag),
    path('v1/post', api.create_post),
    path('v1/comment/<int:post_no>', api.create_comment),
    path('v1/comment/<int:post_no>/check', api.get_count_new_comments),
    path('v1/signature', api.sign_session),
]

for static_tuple in settings.STATICFILES_DIR:
    urlpatterns += static(static_tuple[0], document_root=static_tuple[1])
