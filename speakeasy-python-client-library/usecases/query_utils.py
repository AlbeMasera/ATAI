def is_recommendation_query(query):
    recommendation_keywords = ["recommend", "recommendation", "recommend movies like", "similar to", "like", "suggest"]
    return any(keyword in query.lower() for keyword in recommendation_keywords)
