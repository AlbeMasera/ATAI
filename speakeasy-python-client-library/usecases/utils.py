def remove_sent_endings(inp: str):
    return inp.replace(".", "").replace("?", "").replace(",", "").strip(" ").strip("\t")


def remove_different_minus_scores(query: str) -> str:
    return query.replace("–", "-")
