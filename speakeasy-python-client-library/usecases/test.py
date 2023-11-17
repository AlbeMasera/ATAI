
# TEST FOR ENTITY EXTRACTION
from entity_recognizer import EntityRecognizer

# Initialize the EntityRecognizer
recognizer = EntityRecognizer()

# Sample movie titles to test
test_titles = [
    "The Dark Knight",
    "Inception",
    "Forrest Gump",
    "The Matrix",
    # Add more titles as needed
]

# Test each title
for title in test_titles:
    extracted_entities = recognizer.extract_entities(title)
    extracted_titles = [entity.word for entity in extracted_entities]
    print(f"Original: {title}, Extracted: {extracted_titles}")

'''
# TEST FOR RECOMMENDATION
from Graph import Graph
from embeddings import EmbeddingAnswerer
from recommender import MovieRecommender
import os

if __name__ == "__main__":
    # Initialize the necessary components

    graph = Graph(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data",
                "pickle_graph.pickel",
            )
        )
    embedding_answerer = EmbeddingAnswerer()
    recommender = MovieRecommender(graph, embedding_answerer)

    # Sample recommendation queries
    test_titles = ["inception"]
   
    recommendations = recommender.recommend(test_titles, n_recommendations=5)


    print("Recommendations:", recommendations)

["Hamlet ", "Othello"]
["Nightmare on Elm Street", "Friday the 13th", "Halloween"]
["The Lion King ", "Pocahontas", "Beauty and the Beast"]
[The Dark Knight", "Inception", "Forrest Gump", "The Matrix"]

Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies? 
Recommend movies like Nightmare on Elm Street, Friday the 13th, and Halloween. 

'''
