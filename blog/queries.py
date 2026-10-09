"""Queries behind the views. Part 2 of the lab happens in this file."""
from blog.models import Post


def posts_for_front_page():
    # select_related follows the ForeignKey (author) with a JOIN: one query for
    # posts and authors together. prefetch_related handles the many-to-many
    # (tags) with one extra query and joins the results in Python. Total: 2,
    # no matter how many posts there are.
    return (
        Post.objects.filter(published=True)
        .select_related("author")
        .prefetch_related("tags")
        .order_by("-published_at")
    )
