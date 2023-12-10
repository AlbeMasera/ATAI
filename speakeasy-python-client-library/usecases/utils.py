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


GET_FILM_BY_NAME_FILTER = """
            SELECT DISTINCT ?film ?queryByTitle WHERE{
                ?film wdt:P31/wdt:P279* wd:Q2431196.                                                                 
                ?film rdfs:label ?queryByTitle.                                                          
                FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
            }
            LIMIT 1
        """

GET_IMDB_ID_BY_NAME_FILTER = """
            SELECT DISTINCT ?imdb_id WHERE{                                                              
                ?film wdt:P345 ?imdb_id.                                                          
                ?film rdfs:label ?queryByTitle.                                                          
                FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
            }
            LIMIT 5
        """

GET_GENRE_BY_LABLE = """
            SELECT DISTINCT ?genreTitle WHERE{                                                              
                ?film wdt:P136 ?genre.                                                          
                ?film rdfs:label ?queryByTitle.  
                ?genre rdfs:label ?genreTitle.                                                         
                FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
            }
            LIMIT 1
        """

RECCOMENDATION_WORDS = [
    "recommend",
    "suggest",
    "advice",
    "advise",
    "propose",
    "offer",
    "love",
    "enjoy",
    "prefer",
]
