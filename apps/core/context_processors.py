from apps.content.models import Category


def nav_categories(request):
    """
    Makes the category list available to every template that extends
    base.html (the navbar's search filter needs it on every page), without
    having to fetch it in every single view.
    """
    return {'nav_categories': Category.objects.all()}