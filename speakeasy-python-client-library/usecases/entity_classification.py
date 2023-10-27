import rdflib
import utils


from EntityRec import EntityRecognition, NerGroups
import crowdAnswerer
from answer import Answer
import embeddingsRec
import embeddings

GRAPH_FILE = "../Project/Resources/14_graph.nt"
GRAPH_FILE_SMALL = "../Project/Resources/small_graph.ttl"
GRAPH_PICKLE = "../Project/Graph/graph_pickle_2.pickle"

MMP_PICKLE = "../Project/media/multimediaprocessor.pickle"


class EntryClassification(object):
    def __init__(self):
        self.ner = EntityRecognition()
        self.embeddingAnswer = embeddings.EmbeddingAnswerer()

        self.embeddingRecogniser = embeddingsRec.EmbeddingRecogniser()
        self.crowd = crowdAnswerer.CrowdAnswerer(self.embeddingRecogniser, self.graph)

        print("[+] Answerer READY")

    # Start function of all the question answering
    def start(self, query: str) -> Answer:
        query = utils.remove_different_minus_scores(query)
        print("[+] start classification")

        predicate = self.embeddingRecogniser.get_predicates(query)

        if predicate:
            crowd_answer = self.crowd.might_answer(query, predicate.predicate)
            if not crowd_answer:
                crowd_answer = crowdAnswerer.CrowdAnswer(
                    crowdAnswerer.AnswerLevel.No,
                    "There was an error in the crowd answerer.",
                    None,
                )

            print(f"[+] found PREDICATE in question")
            em_rl = self.embeddingAnswer.is_predicate_in_embedding(predicate.label)
            if em_rl:
                print(f"[+] found EMBEDDING in question {em_rl.relation_label}")
                answer, answered = self.answer_embedding_question(
                    predicate.fixed_query, em_rl
                )
                if answered:
                    return answer.with_crowd_opinion(crowd_answer.get_text())
                print(f"[X] EMBEDDING did not answer question")

            print("[!] not Embedding")
            print("[+] Try answer STATIC question")
            return self.answer_statical_question(
                predicate.predicate, query
            ).with_crowd_opinion(crowd_answer.get_text())

        return Answer.from_error("This seems to be a question that I cannot answer.")

    def answer_statical_question(
        self, predicate: rdflib.term.URIRef, query: str
    ) -> Answer:
        prediction = self.ner.get_single_prediction(query, is_question=True)
        if not prediction:
            return Answer.from_error(
                f"No NER entities found. Wanted to use graph to answer. \n Found predicate {predicate}"
            )

        if prediction.label == "PER":
            return self.graph.get_static_question_from_person(
                prediction.original_text, predicate
            )

        else:
            # if prediction.labels[0].value == "MISC" or prediction.labels[0].value == "ORG":
            return self.graph.get_static_question_from_movie(
                prediction.original_text, predicate
            )

            # else:
            #     print(f"[-] ERROR: Could not match label to action.")
            #     return Answer.error()

    # @utils.catch_exc_decor(exc_val=Answer("The graph failed to answer question. Sorry."))

    def get_static_question_from_person(
        self, name: str, predicate: rdflib.term.URIRef
    ) -> Answer:
        res = self.get_per(name)
        if not res:
            return Answer.person_not_found(name).with_hint(
                f"Tried to use graph to answer question. Found predicate {predicate}"
            )

        lbl = self.__object_label(res, predicate)
        if lbl:
            return Answer.from_question(lbl).with_hint(
                f"(Used graph to answer question.\n{res} -> {predicate})"
            )

        return Answer.from_error(
            f"No answer found in the graph for {res[0]} and predicate {predicate}"
        )

    def get_static_question_from_movie(
        self, name: str, predicate: rdflib.term.URIRef
    ) -> Answer:
        res = self.get_movie_with_label(name)
        if not res:
            return Answer.movie_not_found(name).with_hint(
                f"Tried to use graph to answer question. Found predicate {predicate}"
            )

        lbl = self.__object_label(res[0], predicate)
        if lbl:
            return Answer.from_question(lbl).with_hint(
                f"(Used graph to answer question.\n{res[0]} -> {predicate})"
            )

        return Answer.from_error(
            f"No answer found in the graph for {res[0]} and predicate {predicate}"
        )


if __name__ == "__main__":
    q = "who is director of Alice in Wonderland"
    q2 = "who is director of Pirates of the Caribbean: On Stranger Tides"
    q3 = "who is director of Shrek"
    q4 = "who is director of The Dark Knight"

    f0 = "Who is the director of Good Will Hunting?	"
    f1 = "Who directed The Bridge on the River Kwai?	"
    f2 = "Who is the director of Star Wars: Episode VI - Return of the Jedi?	"

    e1 = "Who is the screenwriter of The Masked Gang: Cyprus?"
    e2 = "What is the MPAA film rating of Weathering with You?"
    e3 = "What is the genre of Good Neighbors?"

    mmq1 = "Show me a picture of Halle Berry."
    mmq2 = "What does Julia Roberts look like?"
    mmq3 = "Let me know what Sandra Bullock looks like."

    r1 = "Recommend me a movie like The Dark Knight."
    r2 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises."
    r3 = "Recommend me a movie like The Dark Knight and The Dark Knight Rises and The Dark Knight Returns."
    r4 = "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies?"
    r5 = (
        "Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween."
    )
    r6 = "Recommend movies similar to Hamlet and Othello.	"

    c1 = "What is the box office of The Princess and the Frog?	"
    c2 = "Can you tell me the publication date of Tom Meets Zizou?	"
    c3 = "Who is the executive producer of X-Men: First Class?	"

    ec = EntryClassification()
    # print(ec.start(f0))
    # print(ec.start(f1))
    # print(ec.start(f2))
    #
    # print(ec.start(r1))
    # print(ec.start(r2))
    # print(ec.start(r3))
    # print(ec.start(r4))
    # print(ec.start(r5))
    # print(ec.start(r6))
    #
    print(ec.start(q))
    # print(ec.start(q2))
    # print(ec.start(q3))
    # print(ec.start(q4))
    # print(ec.start(e1))
    # print(ec.start(e2))
    # print(ec.start(e3))
    # print(ec.start(mmq1))
    # print(ec.start(mmq2))
    # print(ec.start(mmq3))
    #
    # print(ec.start(c1))
    # print(ec.start(c2))
    # print(ec.start(c3))

    # print(ec.movieRecommendation.recommend_embedding(["The Lion King", "Pocahontas", "The Beauty and the Beast"]))
    # print(ec.movieRecommendation.recommend_embedding(["Nightmare on Elm Street", "Friday the 13th", "Halloween"]))
    # print(ec.movieRecommendation.recommend_embedding(["Hangover"]))
    # print(ec.movieRecommendation.recommend_embedding(["genre"]))
    # print(ec.movieRecommendation.recommend_embedding(["The Dark Knight", "The Dark Knight Rises"]))
