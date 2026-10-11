from tokenizer.bpe import END_OF_TEXT

CHUNK_CHARS = 8_000_000


def read_chunks(path, chunk_chars=CHUNK_CHARS):
    buffer = ""
    with open(path, encoding="utf-8", newline="") as file:
        while block := file.read(chunk_chars):
            buffer += block
            cut = buffer.rfind(END_OF_TEXT)
            if cut != -1:
                cut += len(END_OF_TEXT)
                yield buffer[:cut]
                buffer = buffer[cut:]
    if buffer:
        yield buffer
