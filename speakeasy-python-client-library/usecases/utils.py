_SENTENCE_ENDING = {"?", ".", ",", '"'}


def remove_sentence_ending(inp: str):
    return inp.replace(".", "").replace("?", "").replace(",", "").strip(" ").strip("\t")


def remove_hyphen_add_dash(query: str) -> str:
    return query.replace("-", "–")


def lowercase_remove_sentence_ending(inp: str):
    return (
        inp.strip(" ").strip("\t").strip(".").strip("?").strip(",").strip("!").lower()
    )

def add_sentence_ending(sentence: str, is_question=False):
    if len(sentence) <= 1:
        return sentence

    sentence = sentence.strip("\t").strip(" ")
    end = sentence[-1]
    if end in _SENTENCE_ENDING:
        return sentence

    if is_question:
        return sentence.strip() + "?"
    return sentence.strip() + "."
