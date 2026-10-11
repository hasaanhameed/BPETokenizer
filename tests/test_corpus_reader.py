import tempfile
import unittest
from pathlib import Path

from tokenizer.bpe import END_OF_TEXT
from tokenizer.corpus_reader import read_chunks

TEXT = "".join(f"دستاویز {i}\r\nline two\n" + END_OF_TEXT for i in range(50)) + "trailing text"


class ReadChunksTest(unittest.TestCase):
    def test_chunks_rejoin_exactly_and_end_at_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus.txt"
            path.write_text(TEXT, encoding="utf-8", newline="")
            chunks = list(read_chunks(path, chunk_chars=37))
        self.assertEqual("".join(chunks), TEXT)
        self.assertTrue(all(chunk.endswith(END_OF_TEXT) for chunk in chunks[:-1]))
        self.assertGreater(len(chunks), 1)


if __name__ == "__main__":
    unittest.main()
