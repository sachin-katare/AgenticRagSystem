from app.services.query_classifier import QueryClassifier


def test_query_classifier_routes_policy_question_to_semantic() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("What rules apply to audio ads?")

    assert classification.route == "semantic"
    assert "meaning" in classification.reason


def test_query_classifier_routes_exact_count_to_structured() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("How many streaming audio campaigns are there?")

    assert classification.route == "structured"
    assert "exact table calculation" in classification.reason


def test_query_classifier_routes_grouped_maximum_to_structured() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("Which region has the highest revenue?")

    assert classification.route == "structured"
    assert "exact table calculation" in classification.reason


def test_query_classifier_routes_meaning_plus_count_to_hybrid() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("How many high-risk renewals mention attribution issues?")

    assert classification.route == "hybrid"
    assert "semantic meaning" in classification.reason


def test_query_classifier_routes_broad_question_to_clarification() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("Tell me about sales")

    assert classification.route == "clarification"
    assert "too broad" in classification.reason


def test_query_classifier_routes_empty_question_to_clarification() -> None:
    classifier = QueryClassifier()

    classification = classifier.classify("   ")

    assert classification.route == "clarification"
    assert "empty" in classification.reason
