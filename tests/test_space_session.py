import unittest

from app.space_session import add_document, answer, new_session


class SpaceSessionTests(unittest.TestCase):
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
