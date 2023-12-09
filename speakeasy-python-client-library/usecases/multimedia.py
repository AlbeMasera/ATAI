import json
import os
from Graph import Graph


# Get the absolute path to the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define the relative path to the "data" folder
data_folder = os.path.join(current_directory, "data")

# Use absolute paths for loading files from the "data" folder
JSON_PATH = os.path.join(data_folder, "images.json")


class Multimedia(object):
    def __init__(self, graph: Graph):
        self.graph = graph

        with open(JSON_PATH, "r") as f:
            self._json_src = json.load(f)

    def get_image_from_lable(self, label: str) -> str:
        imdb_ids = self.graph.get_imdb_id_with_label(label)
        return self.get_image_from_imdb_id(imdb_ids)

    def get_image_from_imdb_id(self, imdb_ids: [str]) -> str:
        for imdb_id in imdb_ids:
            for i, o in enumerate(self._json_src):
                if imdb_id in o["cast"] or imdb_id in o["movie"]:
                    return o["img"]
        return "Error"


if __name__ == "__main__":
    graph = Graph(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "data",
            "pickle_graph.pickel",
        )
    )
    multimedia = Multimedia(graph)
    print(multimedia.get_image_from_lable("Tom Hanks"))
