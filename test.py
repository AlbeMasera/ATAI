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
    extracted_titles = recognizer.extract_movie_titles(title)
    print(f"Original: {title}, Extracted: {extracted_titles}")
