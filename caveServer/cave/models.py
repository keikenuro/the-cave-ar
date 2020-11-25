import os
import uuid
import datetime
from django.db import models


# --- STORAGE HANDLERS ---
def post_attache_file_storage(instance, filename: str) -> str:
    return f"post/{str(instance.uuid).replace('-', '')}/{filename}".strip()


def comment_attached_file_storage(instance, filename: str) -> str:
    file_name, file_ext = os.path.splitext(os.path.basename(filename))
    file_name = f"{str(instance.uuid).replace('-', '')}{file_ext}"
    return f"post/{str(instance.post.uuid).replace('-', '')}/{file_name}".strip()


# --- END STORAGE HANDLERS ---


# --- MODELS ---
class Tag(models.Model):
    class Meta:
        db_table = 'tag'
        ordering = ['name']

    name: str = models.CharField(primary_key=True, max_length=250)
    description: str = models.CharField(max_length=250)

    def __str__(self):
        return f"Tag(name={self.name}, description={self.description})"


class HashTag(models.Model):
    class Meta:
        db_table = 'hashtag'
        ordering = ['created_at', 'name']

    name: str = models.CharField(primary_key=True, max_length=250)
    created_at: datetime.datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"HashTag(name={self.name}, created_at={self.created_at.strftime('%d/%m/%Y %H:%M:%S.s')})"


class Post(models.Model):
    class Meta:
        db_table = 'post'
        ordering = ['created_at', 'no']

    no: int = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    location: str = models.CharField(max_length=2)
    title: str = models.CharField(max_length=250, blank=False, null=False)
    raw_content: str = models.TextField(blank=False, null=False)
    created_at: datetime.datetime = models.DateTimeField(auto_now_add=True)
    attached_img = models.ImageField(max_length=250, upload_to=post_attache_file_storage, null=True)
    views: int = models.BigIntegerField(null=False)
    signature: str = models.CharField(max_length=128, null=True, blank=True)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    hashtags = models.ManyToManyField(HashTag)

    def __str__(self):
        return (f"Post(no={self.no},"
                f"title={self.title}"
                f"location={self.location},"
                f"raw_content={self.raw_content:>50}"
                f"created_at={self.created_at.strftime('%d/%m/%Y %H:%M:%S.s')},"
                f"attached_img={self.attached_img.path},"
                f"views={self.views},"
                f"tag={self.tag},"
                f"hashtags={self.hashtags})")


class Comment(models.Model):
    class Meta:
        db_table = 'comment'
        ordering = ['created_at', 'no']

    no: int = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    location: str = models.CharField(max_length=2)
    created_at: datetime.datetime = models.DateTimeField(auto_now_add=True)
    raw_content: str = models.TextField(blank=False, null=False)
    attached_img = models.ImageField(max_length=250, blank=True, upload_to=comment_attached_file_storage, null=True)
    hashtags = models.ManyToManyField(HashTag)
    is_from_op = models.BooleanField(default=False)

    def __str__(self):
        return (f"Comment(no={self.no},"
                f"post={self.post},"
                f"location={self.location},"
                f"raw_content={self.raw_content:>50},"
                f"created_at={self.created_at.strftime('%d/%m/%Y %H:%M:%S.s')},"
                f"attached_img={self.attached_img.path if self.attached_img else 'no-data'},"
                f"hashtags={self.hashtags})")

# --- END MODELS ---
