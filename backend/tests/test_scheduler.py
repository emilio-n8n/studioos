from app.kernel.scheduler import Scheduler


def test_get_ready_empty():
    scheduler = Scheduler([])
    assert scheduler.get_ready() == []


def test_get_ready_with_deps():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2, "depends_on": [1]},
    ])
    ready = scheduler.get_ready()
    assert ready == [{"id": 1}]


def test_mark_completed():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2, "depends_on": [1]},
    ])
    assert scheduler.get_ready() == [{"id": 1}]
    scheduler.mark_completed(1)
    assert scheduler.get_ready() == [{"id": 2, "depends_on": [1]}]


def test_is_done():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2},
    ])
    assert scheduler.is_done() is False
    scheduler.mark_completed(1)
    assert scheduler.is_done() is False
    scheduler.mark_completed(2)
    assert scheduler.is_done() is True


def test_get_progress():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2},
    ])
    assert scheduler.get_progress()["total"] == 2
    assert scheduler.get_progress()["completed"] == 0
    assert scheduler.get_progress()["remaining"] == 2

    scheduler.mark_completed(1)

    assert scheduler.get_progress()["total"] == 2
    assert scheduler.get_progress()["completed"] == 1
    assert scheduler.get_progress()["remaining"] == 1

    scheduler.mark_completed(2)

    assert scheduler.get_progress()["total"] == 2
    assert scheduler.get_progress()["completed"] == 2
    assert scheduler.get_progress()["remaining"] == 0


def test_mark_failed():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2},
    ])
    scheduler.mark_failed(1)
    assert scheduler.is_done() is False


def test_get_status():
    scheduler = Scheduler([
        {"id": 1},
        {"id": 2, "depends_on": [1]},
        {"id": 3, "depends_on": [2]},
    ])
    assert scheduler.get_status() == {1: "READY", 2: "BLOCKED", 3: "BLOCKED"}

    scheduler.mark_completed(1)
    assert scheduler.get_status() == {
        1: "COMPLETED",
        2: "READY",
        3: "BLOCKED",
    }

    scheduler.mark_completed(2)
    assert scheduler.get_status() == {
        1: "COMPLETED",
        2: "COMPLETED",
        3: "READY",
    }

    scheduler.mark_completed(3)
    assert scheduler.get_status() == {
        1: "COMPLETED",
        2: "COMPLETED",
        3: "COMPLETED",
    }
