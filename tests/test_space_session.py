import unittest

from app.space_design import library, present
from app.space_session import add_document, answer, new_session


class SpaceSessionTests(unittest.TestCase):
    def test_html_views_escape_untrusted_text(self):
        session, _ = add_document(
            new_session(), "<script>alert(1)</script>.txt", b"Zebras <script>alert(1)</script>"
        )
        self.assertNotIn("<script>", library(session))
        result = answer("Zebras", session)
        rendered = present("<img src=x onerror=alert(1)>", result, 1.2, "Hybrid")
        self.assertNotIn("<script>", rendered[1] + rendered[2])
        self.assertNotIn("<img src=x", rendered[1])
        self.assertIn("&lt;script&gt;", rendered[2])

    def test_adding_after_removal_keeps_unique_chunk_ids(self):
        session = new_session()
        removed = session["chunks"][0]["document_id"]
        session["chunks"] = [c for c in session["chunks"] if c["document_id"] != removed]
        session, _ = add_document(session, "new.txt", b"A new document after a removal")
        ids = [c["id"] for c in session["chunks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_uploads_are_isolated_between_sessions(self):
        first, second = new_session(), new_session()
        updated, _ = add_document(
            first, "private.txt", b"The unique deployment identifier is zebraquartz."
        )
        self.assertEqual(len(first["documents"]), 5)
        self.assertEqual(len(updated["documents"]), 6)
        self.assertTrue(answer("zebraquartz", updated)[1])
        self.assertEqual(answer("zebraquartz", second)[1], [])

    def test_duplicate_and_reset(self):
        original = new_session()
        updated, _ = add_document(original, "a.txt", b"Session fixture")
        duplicate, _ = add_document(updated, "b.txt", b"Session fixture")
        self.assertEqual(len(duplicate["documents"]), 6)
        self.assertEqual(len(new_session()["documents"]), 5)

    def test_excerpts_match_the_returned_sources(self):
        text, rows, sources = answer("hybrid search", new_session())
        self.assertIn(sources[0]["text"], text)
        self.assertEqual(rows[0][1], sources[0]["document"])

    def test_session_capacity_is_bounded(self):
        session = new_session()
        for i in range(10):
            session, _ = add_document(session, f"{i}.txt", f"Unique fixture {i}".encode())
        with self.assertRaisesRegex(ValueError, "limit"):
            add_document(session, "overflow.txt", b"One more file")
