import pytest

from app.models import LogoPosition, OverflowPolicy
from app.video_processing import _overlay_position, parse_timestamp, validate_clip_range


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("30", 30.0),
        ("30 seconds", 30.0),
        ("01:10", 70.0),
        ("00:02:15", 135.0),
        ("00:00:05.5", 5.5),
    ],
)
def test_parse_timestamp(value, expected):
    assert parse_timestamp(value) == expected


def test_validate_duration_clip():
    clip = validate_clip_range(
        total_duration=600,
        start_timestamp="00:02:15",
        clip_duration="30",
    )
    assert clip.start_seconds == 135
    assert clip.end_seconds == 165
    assert clip.duration_seconds == 30


def test_validate_end_timestamp_clip():
    clip = validate_clip_range(
        total_duration=300,
        start_timestamp="00:01:10",
        end_timestamp="00:01:40",
    )
    assert clip.duration_seconds == 30


def test_trim_overflow_to_available_duration():
    clip = validate_clip_range(
        total_duration=45,
        start_timestamp="00:00:35",
        clip_duration="30",
        overflow_policy=OverflowPolicy.trim,
    )
    assert clip.end_seconds == 45
    assert clip.duration_seconds == 10


def test_error_overflow_policy():
    with pytest.raises(ValueError, match="exceeds"):
        validate_clip_range(
            total_duration=45,
            start_timestamp="00:00:35",
            clip_duration="30",
            overflow_policy=OverflowPolicy.error,
        )


def test_overlay_bottom_right_expression():
    assert _overlay_position(LogoPosition.bottom_right, 24) == (
        "main_w-overlay_w-24",
        "main_h-overlay_h-24",
    )

