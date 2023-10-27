IS_MOVIE = "wdt:P31 wd:Q2431196."
DIRECTED = "wdt:P57"

GET_FILM_BY_NAME_FILTER = """
                SELECT DISTINCT ?film ?queryByTitle WHERE{
                  ?film wdt:P31/wdt:P279* wd:Q2431196.                                                                 
                  ?film rdfs:label ?queryByTitle.                                                          
                  FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
                }
                LIMIT 1
            """

GET_FILM_DETAILS_BY_NAME_FILTER = """
                 SELECT DISTINCT ?film ?genre ?director ?production_com ?screenwriter ?country_of_origin ?producer WHERE{
                  ?film wdt:P31/wdt:P279* wd:Q2431196.
                  ?film rdfs:label ?queryByTitle.
                  FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
                  # FILTER(LANG(?queryByTitle) = "en")
                  OPTIONAL{?film wdt:P136 ?genre .}
                  OPTIONAL{?film wdt:P495 ?country_of_origin .}
                  OPTIONAL{?film wdt:P57 ?director .}
                  OPTIONAL{?film wdt:P58 ?screenwriter .}
                  OPTIONAL{?film wdt:P162 ?producer .}
                  OPTIONAL{?film wdt:P272 ?production_com .}
                }
                LIMIT 10
 """

GET_FILMS_BY_NAME_FILTER = """
                SELECT DISTINCT ?queryByTitle ?film WHERE{
                  ?film wdt:P31/wdt:P279* wd:Q2431196.                                                                 
                  ?film rdfs:label ?queryByTitle.                                                          
                  FILTER(REGEX(?queryByTitle, "%(filmName)s", "i"))
                  FILTER(LANG(?queryByTitle) = "en")
                }
                LIMIT 10 
            """

GET_PER_BY_LABEL = """
  SELECT DISTINCT ?item WHERE {
  	?item wdt:P31/wdt:P279* wd:Q5  .
    ?item rdfs:label ?queryByTitle.
    FILTER(REGEX(?queryByTitle,  "%(entityName)s", "i"))
  }
LIMIT 1
"""

GET_PER_BY_LABEL_WITH_IMDB = """
# search movies by name
SELECT DISTINCT ?per ?queryByTitle WHERE {
  ?per wdt:P31/wdt:P279* wd:Q5.
  ?per rdfs:label ?queryByTitle.
  # ?per wdt:P345 ?imdb_id.
  FILTER(REGEX(?queryByTitle, "%(entityName)s", "i"))
  # FILTER(LANG(?queryByTitle) = "en")
}
LIMIT 1
"""

GET_FILM_RECOMMENDATION_BY_DETAILS = """
SELECT DISTINCT ?film ?filmtitle WHERE{
    ?film wdt:P31/wdt:P279* wd:Q2431196.
    ?film rdfs:label ?filmtitle.

%(filmDetails)s

    FILTER(LANG(?filmtitle) = "en")
}
LIMIT 5
    """

GET_BY_MOVIE_SUB_LABEL_AND_PREDICATE = """
SELECT DISTINCT ?entity ?entity_label WHERE {
  {
    SELECT DISTINCT ?subject WHERE{
      ?subject wdt:P31/wdt:P279* wd:Q2431196.                                                                 
      ?subject rdfs:label ?queryByTitle.                                                          
      FILTER(REGEX(?queryByTitle, "%(entityName)s", "i"))
      FILTER(LANG(?queryByTitle) = "en")
    }
    LIMIT 1 
  }
  ?subject %(predicate)s ?entity.                                                                 # film => directed by FilmDirector
  ?entity rdfs:label ?entity_label.
  
  FILTER(LANG(?entity_label) = "en")
}
LIMIT 1
"""