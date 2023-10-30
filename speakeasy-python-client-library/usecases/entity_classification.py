import os
from typing import Tuple, List, Dict
import rdflib
import utils


from EntityRec import EntityRecognition
import crowdAnswer
from answer import Answer
import embeddingsRec
import embeddings
from Graph import Graph


# Get the absolute path to the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the "data" folder
data_folder = os.path.join(current_directory, "data")

# Use absolute paths for loading files from the "data" folder
GRAPH_PICKLE = os.path.join(data_folder, "pickle_graph.pickel")


class EntryClassification(object):
    def __init__(self):
        self.ner = EntityRecognition()
        self.embeddingAnswer = embeddings.EmbeddingAnswerer()
        self.graph = Graph(GRAPH_PICKLE, is_pickle=True)
        self.embeddingRecogniser = embeddingsRec.EmbeddingRecogniser()
        self.crowd = crowdAnswer.CrowdAnswerer(self.embeddingRecogniser, self.graph)

        print("Answerer is ready!")

    # Start function of all the question answering
    def start(self, query: str) -> Answer:
        query = utils.remove_hyphen_add_dash(query)
        print("Start classification")

        predicate = self.embeddingRecogniser.get_predicates(query)

        if predicate:
            crowd_answer = self.crowd.might_answer(query, predicate.predicate)
            if not crowd_answer:
                crowd_answer = crowdAnswer.CrowdAnswer(
                    crowdAnswer.AnswerLevel.No,
                    "There was an error in the crowd answerer.",
                    None,
                )

            print(f"Found 'predicate' in question")
            em_rl = self.embeddingAnswer.is_predicate_in_embedding(predicate.label)
            if em_rl:
                print(f"Found 'embedding' in question {em_rl.relation_label}")
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

        return Answer.from_error("Sorry, I cannot answer this question.")

    def answer_statical_question(self, predicate: rdflib.term.URIRef, query: str) -> Answer:
        prediction = self.ner.get_single_prediction(query, is_question=True)
        if not prediction:
            return Answer.from_error(
                f"Could not find NER entities. Instead found predicate: {predicate}"
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

    # Answer questions about a person using the graph
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
            f"Could not find the answer in the graph for {res[0]} and predicate {predicate}"
        )

    # Answer questions about a movie using the graph
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
            f"Could not find the answer in the graph for {res[0]} and predicate {predicate}"
        )

    # Answer a question using embeddings based on the recognized entity and relation
    def answer_embedding_question(
        self, query: str, relation: embeddings.EmbeddingRelation
    ) -> Tuple[Answer, bool]:
        print(f"[+] start embedding answering of q: {query}")
        prediction = self.ner.get_single_prediction(query, is_question=True)
        if not prediction:
            return (
                Answer.from_error(
                    f"No NER entities found. Wanted to use embedding answerer. \n Found predicate {relation.relation_label}"
                ),
                True,
            )

        entity: rdflib.IdentifiedNode | None = None
        hints = f"(Tried Embedding Answerer with predicate {relation.relation_label})"
        if prediction.label == "PER":
            res = self.graph.get_per(prediction.original_text)
            if not res:
                return (
                    Answer.person_not_found(prediction.original_text).with_hint(hints),
                    True,
                )
            entity = res

        else:  
            # ignore labels
            res = self.graph.get_movie_with_label(prediction.original_text)
            if not len(res):
                return (
                    Answer.movie_not_found(prediction.original_text).with_hint(hints),
                    True,
                )
            entity = res[0]

        if not entity:
            return Answer.error()

        hints = f"(Used Embedding of {entity} + {relation.relation_label})"
        answer_entity = self.embeddingAnswer.calculate_embedding_node(
            entity, relation.relation_key
        )
        if not answer_entity:
            return (
                Answer.from_error(
                    f"Could not calculate question in embedding. Sorry."
                ).with_hint(hints),
                False,
            )

        answer_label = self.graph.entity_2_label(answer_entity)
        if not answer_label:
            return (
                Answer.from_error(
                    f"Could not find the label of the calculated answer {answer_entity} in graph. Sorry."
                ).with_hint(hints),
                True,
            )
        return Answer.from_general_graph_node(answer_label).with_hint(hints), True


if __name__ == "__main__":
    q = "who is director of Alice in Wonderland"
    q2 = "who is director of Pirates of the Caribbean: On Stranger Tides"
    q3 = "who is director of Shrek"
    q4 = "who is director of The Dark Knight"

    f0 = "Who is the director of Good Will Hunting?	"
    f1 = "Who directed The Bridge on the River Kwai?	"
    f2 = "Who directed Star Wars: Episode VI - Return of the Jedi?	"

    e1 = "Who is the screenwriter of The Masked Gang: Cyprus?"
    e2 = "What is the MPAA film rating of Weathering with You?"
    e3 = "What is the genre of Good Neighbors?"

    c1 = "What is the box office of The Princess and the Frog?	"
    c2 = "Can you tell me the publication date of Tom Meets Zizou?	"
    c3 = "Who is the executive producer of X-Men: First Class?	"

    ec = EntryClassification()
    answer = ec.start(f2)
    print(answer.get_text())

    # print(ec.start(q2))
    # print(ec.start(q3))
    # print(ec.start(q4))
    #
    # print(ec.start(f0))
    # print(ec.start(f1))
    # print(ec.start(f2))
    # 
    # print(ec.start(e1))
    # print(ec.start(e2))
    # print(ec.start(e3))
    #
    # print(ec.start(c1))
    # print(ec.start(c2))
    # print(ec.start(c3))
