from spec_cli.models import Spec, SpecStatus
from spec_cli.storage import children_of, open_blockers


def _spec(id_, status, blocked_by=(), parent=""):
    return Spec(id=id_, title=id_, status=status, blocked_by=list(blocked_by), parent=parent)


def test_open_blockers():
    a = _spec("0001", SpecStatus.DRAFT)
    b = _spec("0002", SpecStatus.IMPLEMENTED)
    c = _spec("0003", SpecStatus.CLOSED)
    dependent = _spec("0004", SpecStatus.APPROVED, blocked_by=["0001", "0002", "0003", "9999"])
    all_specs = [a, b, c, dependent]

    # only 0001 (draft) is still open; 0002/0003 resolved; 9999 doesn't exist
    assert [s.id for s in open_blockers(dependent, all_specs)] == ["0001"]

    a.status = SpecStatus.IMPLEMENTED
    assert open_blockers(dependent, all_specs) == []


def test_no_blockers_by_default():
    solo = _spec("0001", SpecStatus.APPROVED)
    assert open_blockers(solo, [solo]) == []


def test_children_of():
    m = _spec("0001", SpecStatus.DRAFT)
    a = _spec("0002", SpecStatus.DRAFT, parent="0001")
    b = _spec("0003", SpecStatus.DRAFT, parent="0001")
    other = _spec("0004", SpecStatus.DRAFT, parent="0099")
    all_specs = [m, a, b, other]

    assert [s.id for s in children_of("0001", all_specs)] == ["0002", "0003"]
    assert children_of("0099", all_specs) == [other]
    assert children_of("0001", [m]) == []
