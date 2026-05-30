from app.storage import _is_direct_video_url


def test_direct_video_url_detection():
    assert _is_direct_video_url("https://cdn.example.com/video.mp4")
    assert _is_direct_video_url("https://cdn.example.com/video.MOV?token=abc")


def test_platform_url_is_not_direct_video_url():
    assert not _is_direct_video_url("https://www.youtube.com/watch?v=abc")
    assert not _is_direct_video_url("https://www.instagram.com/reel/abc/")
