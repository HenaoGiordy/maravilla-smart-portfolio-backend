from datetime import UTC, datetime

from app.workers.notification_schedule_worker import SchedulingPreference, should_send_now


def test_should_send_now_when_never_sent() -> None:
    pref = SchedulingPreference(frequency="daily", last_sent_at=None)
    now = datetime(2026, 4, 14, 10, 0, tzinfo=UTC)
    assert should_send_now(pref, now) is True


def test_should_send_now_daily_only_next_day() -> None:
    now = datetime(2026, 4, 14, 10, 0, tzinfo=UTC)
    pref_today = SchedulingPreference(frequency="daily", last_sent_at=datetime(2026, 4, 14, 8, 0, tzinfo=UTC))
    pref_yesterday = SchedulingPreference(frequency="daily", last_sent_at=datetime(2026, 4, 13, 23, 0, tzinfo=UTC))

    assert should_send_now(pref_today, now) is False
    assert should_send_now(pref_yesterday, now) is True


def test_should_send_now_weekly_changes_on_new_week() -> None:
    now = datetime(2026, 4, 14, 10, 0, tzinfo=UTC)
    same_week = SchedulingPreference(frequency="weekly", last_sent_at=datetime(2026, 4, 13, 10, 0, tzinfo=UTC))
    previous_week = SchedulingPreference(frequency="weekly", last_sent_at=datetime(2026, 4, 6, 10, 0, tzinfo=UTC))

    assert should_send_now(same_week, now) is False
    assert should_send_now(previous_week, now) is True


def test_should_send_now_monthly_changes_on_new_month() -> None:
    now = datetime(2026, 4, 14, 10, 0, tzinfo=UTC)
    same_month = SchedulingPreference(frequency="monthly", last_sent_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC))
    previous_month = SchedulingPreference(frequency="monthly", last_sent_at=datetime(2026, 3, 31, 10, 0, tzinfo=UTC))

    assert should_send_now(same_month, now) is False
    assert should_send_now(previous_month, now) is True
