import asyncio
import pytest
from app.utils.locks import document_lock


@pytest.mark.asyncio
async def test_document_lock_serializes_same_doc_id():
    order = []

    @document_lock(doc_id_arg="doc_id")
    async def critical_section(doc_id, delay, tag):
        order.append(f"start-{tag}")
        await asyncio.sleep(delay)
        order.append(f"end-{tag}")
        return tag

    async def run_pair():
        t1 = asyncio.create_task(critical_section(1, 0.1, "A"))
        t2 = asyncio.create_task(critical_section(1, 0.1, "B"))
        await asyncio.gather(t1, t2)

    await run_pair()
    # The second call should only start after the first ends
    assert order == ["start-A", "end-A", "start-B", "end-B"] or order == [
        "start-B",
        "end-B",
        "start-A",
        "end-A",
    ]


@pytest.mark.asyncio
async def test_document_lock_parallel_different_doc_ids():
    order = []

    @document_lock(doc_id_arg="doc_id")
    async def critical_section(doc_id, delay, tag):
        order.append(f"start-{tag}")
        await asyncio.sleep(delay)
        order.append(f"end-{tag}")
        return tag

    async def run_pair():
        t1 = asyncio.create_task(critical_section(1, 0.1, "A"))
        t2 = asyncio.create_task(critical_section(2, 0.1, "B"))
        await asyncio.gather(t1, t2)

    await run_pair()
    # Both can start before either ends (order is not strictly serialized)
    assert "start-A" in order and "start-B" in order
    assert "end-A" in order and "end-B" in order
    assert order.index("start-A") < order.index("end-A")
    assert order.index("start-B") < order.index("end-B")
