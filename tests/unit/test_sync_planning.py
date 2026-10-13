from sync.planning import Limits, SyncPlan, billable_pages, build_plan, check_guards

B = "gs://derecho-urbanistico-prueba/urbanismo"


def test_build_plan_imports_new_and_deletes_removed() -> None:
    bucket = {f"{B}/legislacion/a.pdf", f"{B}/ordenanzas/b.pdf"}
    indexed = {f"{B}/legislacion/a.pdf", f"{B}/doctrina/c.pdf"}

    plan = build_plan(bucket, indexed)

    assert plan.to_import == [f"{B}/ordenanzas/b.pdf"]
    assert plan.to_delete == [f"{B}/doctrina/c.pdf"]


def test_build_plan_without_changes_is_empty() -> None:
    uris = {f"{B}/legislacion/a.pdf"}
    assert build_plan(uris, uris).is_empty


def test_billable_pages_caps_at_ocr_limit() -> None:
    assert billable_pages(17) == 17
    assert billable_pages(632) == 500


def test_guards_pass_for_normal_hourly_change() -> None:
    plan = SyncPlan(to_import=["x"] * 3, to_delete=["y"])
    assert check_guards(plan, new_pages=60, bucket_count=140, indexed_count=138, limits=Limits()) == []


def test_guards_block_too_many_new_docs_or_pages() -> None:
    plan = SyncPlan(to_import=["x"] * 51)
    reasons = check_guards(plan, new_pages=3001, bucket_count=189, indexed_count=138, limits=Limits())
    assert len(reasons) == 2


def test_guards_block_mass_deletion() -> None:
    plan = SyncPlan(to_delete=["y"] * 30)
    reasons = check_guards(plan, new_pages=0, bucket_count=108, indexed_count=138, limits=Limits())
    assert len(reasons) == 1


def test_guards_block_empty_bucket_listing() -> None:
    plan = SyncPlan(to_delete=["y"] * 138)
    reasons = check_guards(plan, new_pages=0, bucket_count=0, indexed_count=138, limits=Limits())
    assert any("bucket" in r for r in reasons)
