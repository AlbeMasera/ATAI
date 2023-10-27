_SENTENCE_END = {"?", ".", ",", '"'}


def remove_sent_endings(inp: str):
    return inp.replace(".", "").replace("?", "").replace(",", "").strip(" ").strip("\t")


def remove_different_minus_scores(query: str) -> str:
    return query.replace("-", "–")


def add_sentence_ending(sentence: str, is_question=False):
    if len(sentence) <= 1:
        return sentence

    sentence = sentence.strip("\t").strip(" ")
    end = sentence[-1]
    if end in _SENTENCE_END:
        return sentence

    if is_question:
        return sentence.strip() + "?"
    return sentence.strip() + "."


def lower_remove_sent_endings_at_end(inp: str):
    return (
        inp.strip(" ").strip("\t").strip(".").strip("?").strip(",").strip("!").lower()
    )
