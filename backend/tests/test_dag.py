from app.kernel.dag_engine import DAG, CycleError


def test_validate_linear():
    dag = DAG([
        {"id": 1},
        {"id": 2, "depends_on": [1]},
        {"id": 3, "depends_on": [2]},
    ])
    result = dag.validate()
    assert result in ([1, 2, 3], [3, 2, 1])


def test_validate_parallel():
    dag = DAG([
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ])
    result = dag.validate()
    assert sorted(result) == [1, 2, 3]
    assert len(result) == 3


def test_validate_cycle_raises():
    dag = DAG([
        {"id": 1, "depends_on": [2]},
        {"id": 2, "depends_on": [3]},
        {"id": 3, "depends_on": [1]},
    ])
    import pytest
    with pytest.raises(CycleError):
        dag.validate()


def test_get_ready_tasks():
    dag = DAG([
        {"id": 1},
        {"id": 2, "depends_on": [1]},
        {"id": 3, "depends_on": [2]},
    ])
    assert dag.get_ready_tasks(set()) == [{"id": 1}]
    assert dag.get_ready_tasks({1}) == [{"id": 2, "depends_on": [1]}]
    assert dag.get_ready_tasks({1, 2}) == [{"id": 3, "depends_on": [2]}]


def test_get_execution_batches():
    dag = DAG([
        {"id": 1},
        {"id": 2},
        {"id": 3, "depends_on": [1, 2]},
        {"id": 4, "depends_on": [3]},
    ])
    batches = dag.get_execution_batches()
    assert batches == [
        [{"id": 1}, {"id": 2}],
        [{"id": 3, "depends_on": [1, 2]}],
        [{"id": 4, "depends_on": [3]}],
    ]


def test_get_execution_batches_with_completed():
    dag = DAG([
        {"id": 1},
        {"id": 2},
        {"id": 3, "depends_on": [1, 2]},
        {"id": 4, "depends_on": [3]},
    ])
    batches = dag.get_execution_batches(completed_ids={1, 2})
    assert batches == [
        [{"id": 3, "depends_on": [1, 2]}],
        [{"id": 4, "depends_on": [3]}],
    ]
