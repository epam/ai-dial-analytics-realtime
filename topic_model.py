from bertopic import BERTopic

topic_model = BERTopic.load("./topic_model")
topic_model.transform(["test"])  # Make sure the model is loaded


def get_topic(request_messages, response_content):
    text = "\n\n".join([message['content'] for message in request_messages] + [response_content])

    topics, probs = topic_model.transform([text])
    topic = topic_model.get_topic(topics[0], full=True)

    # Model should have "GeneratedName" topic representation
    return topic["GeneratedName"][0][0]
