import pytest

from rag.chunk import Chunk, chunk_text


def test_short_paragraphs_pack_into_one_chunk():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunk_text(text, "doc.md", max_chars=1000)
    assert len(chunks) == 1
    assert "First paragraph." in chunks[0].text
    assert "Third paragraph." in chunks[0].text


def test_packing_respects_max_chars():
    paras = "\n\n".join(f"paragraph number {i} with some filler text" for i in range(20))
    chunks = chunk_text(paras, "doc.md", max_chars=120)
    assert len(chunks) > 1
    assert all(len(c.text) <= 120 for c in chunks)


def test_oversized_paragraph_is_hard_split_with_overlap():
    long_para = "x" * 350
    chunks = chunk_text(long_para, "doc.md", max_chars=100, overlap=20)
    assert len(chunks) >= 4
    assert all(len(c.text) <= 100 for c in chunks)


def test_metadata_is_populated_and_indices_sequential():
    text = "\n\n".join(f"para {i}" for i in range(10))
    chunks = chunk_text(text, "guide.md", max_chars=30)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.source == "guide.md" for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_empty_text_yields_no_chunks():
    assert chunk_text("\n\n   \n\n", "doc.md") == []


@pytest.mark.parametrize("bad", [(0, 0), (100, 100), (100, 150), (100, -1)])
def test_invalid_parameters_raise(bad):
    max_chars, overlap = bad
    with pytest.raises(ValueError):
        chunk_text("some text", "doc.md", max_chars=max_chars, overlap=overlap)
