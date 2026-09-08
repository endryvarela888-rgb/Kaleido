from .models import Content

IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'}


def guess_content_type(filename):
    """Infers the content type from the uploaded file's extension. No file
    at all means a text-only post — the creator never has to pick a type
    by hand, it's implied by what they actually uploaded."""
    if not filename or '.' not in filename:
        return Content.ContentType.TEXT

    ext = filename.rsplit('.', 1)[-1].lower()
    if ext in IMAGE_EXTENSIONS:
        return Content.ContentType.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return Content.ContentType.VIDEO
    if ext in AUDIO_EXTENSIONS:
        return Content.ContentType.AUDIO
    return Content.ContentType.TEXT