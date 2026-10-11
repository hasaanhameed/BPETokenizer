import heapq
from collections import Counter, defaultdict
from math import inf
from pathlib import Path

import regex
from tqdm import tqdm

END_OF_TEXT = "<|endoftext|>"
END_OF_TEXT_ID = 256
PATTERN = regex.compile(r" ?[\p{L}\p{M}‌]+| ?\p{N}{1,3}| ?[^\s\p{L}\p{M}\p{N}]+|\s+(?!\S)|\s+")


def pretokenize(text):
    return PATTERN.findall(text)


def build_vocab(merges):
    vocab = [bytes([b]) for b in range(256)] + [END_OF_TEXT.encode("utf-8")]
    for a, b in merges:
        vocab.append(vocab[a] + vocab[b])
    return vocab


def count_pairs(word):
    return Counter(zip(word, word[1:]))


def merge_word(word, pair, new_id):
    merged = []
    i = 0
    while i < len(word):
        if i + 1 < len(word) and (word[i], word[i + 1]) == pair:
            merged.append(new_id)
            i += 2
        else:
            merged.append(word[i])
            i += 1
    return merged


def pair_key(pair, count, vocab):
    a, b = pair
    return (count, vocab[a], vocab[b], a, b)


def split_words(text):
    return [word for piece in text.split(END_OF_TEXT) for word in pretokenize(piece)]


def train_reference(text, num_merges):
    words = [list(word.encode("utf-8")) for word in split_words(text)]
    vocab = build_vocab([])
    merges = []
    for _ in range(num_merges):
        counts = Counter()
        for word in words:
            counts.update(zip(word, word[1:]))
        if not counts:
            break
        pair = max(counts, key=lambda p: pair_key(p, counts[p], vocab))
        new_id = len(vocab)
        words = [merge_word(word, pair, new_id) for word in words]
        merges.append(pair)
        vocab.append(vocab[pair[0]] + vocab[pair[1]])
    return merges


def count_words(text):
    return Counter(split_words(text))


def train_fast(word_counts, num_merges, progress=False):
    words = [list(word.encode("utf-8")) for word in word_counts]
    freqs = list(word_counts.values())
    vocab = build_vocab([])
    pair_counts = Counter()
    pair_to_words = defaultdict(set)
    for i, word in enumerate(words):
        for pair, n in count_pairs(word).items():
            pair_counts[pair] += n * freqs[i]
            pair_to_words[pair].add(i)
    heap = [pair_key(pair, count, vocab) for pair, count in pair_counts.items()]
    heapq.heapify_max(heap)

    merges = []
    for _ in tqdm(range(num_merges), disable=not progress):
        pair = pop_best_pair(heap, pair_counts)
        if pair is None:
            break
        new_id = len(vocab)
        merges.append(pair)
        vocab.append(vocab[pair[0]] + vocab[pair[1]])

        changed = set()
        for i in pair_to_words.pop(pair):
            old_pairs = count_pairs(words[i])
            words[i] = merge_word(words[i], pair, new_id)
            new_pairs = count_pairs(words[i])
            for p in old_pairs.keys() | new_pairs.keys():
                delta = new_pairs[p] - old_pairs[p]
                if delta:
                    pair_counts[p] += delta * freqs[i]
                    changed.add(p)
            for p in old_pairs.keys() - new_pairs.keys() - {pair}:
                pair_to_words[p].discard(i)
            for p in new_pairs.keys() - old_pairs.keys():
                pair_to_words[p].add(i)

        for p in changed:
            if pair_counts[p] > 0:
                heapq.heappush_max(heap, pair_key(p, pair_counts[p], vocab))
            else:
                del pair_counts[p]
                pair_to_words.pop(p, None)
    return merges


def pop_best_pair(heap, pair_counts):
    while heap:
        count, _, _, a, b = heapq.heappop_max(heap)
        if pair_counts.get((a, b)) == count:
            return (a, b)
    return None


class BPETokenizer:
    def __init__(self, merges):
        self.merges = list(merges)
        self.vocab = build_vocab(self.merges)
        self.ranks = {pair: 257 + i for i, pair in enumerate(self.merges)}
        self.cache = {}

    def encode(self, text):
        ids = []
        for i, piece in enumerate(text.split(END_OF_TEXT)):
            if i > 0:
                ids.append(END_OF_TEXT_ID)
            for word in pretokenize(piece):
                ids.extend(self.encode_word(word))
        return ids

    def encode_word(self, word):
        if word not in self.cache:
            self.cache[word] = self.apply_merges(list(word.encode("utf-8")))
        return self.cache[word]

    def apply_merges(self, ids):
        while len(ids) > 1:
            pair = min(zip(ids, ids[1:]), key=lambda p: self.ranks.get(p, inf))
            if pair not in self.ranks:
                break
            ids = merge_word(ids, pair, self.ranks[pair])
        return ids

    def decode(self, ids):
        return b"".join(self.vocab[i] for i in ids).decode("utf-8")

    def save(self, path):
        lines = "".join(f"{a} {b}\n" for a, b in self.merges)
        Path(path).write_text(lines, encoding="utf-8", newline="\n")

    @classmethod
    def load(cls, path):
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        return cls(tuple(map(int, line.split())) for line in lines)
