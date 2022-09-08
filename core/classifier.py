from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from core.files import Data
from core import filter


class BertClassifier:
    def __init__(self, data: Data, test_split: Optional[float] = None, random_state: int = None):
        self.test_split = test_split
        self.random_state = random_state
        self.data = data
        self.score: Optional[float] = None

        self.entry_ids, self.messages = self.__messages__()
        self.classifier: SentenceTransformer = SentenceTransformer('bert-base-nli-mean-tokens')
        self.embeds = self.classifier.encode(self.messages)

    def __messages__(self) -> (dict, list[str]):
        entry_ids = []
        messages_list = []

        for m in self.data.nonsense():
            messages_list.append(m)
            entry_ids.append(-1)

        for entry in self.data.linked_faq():
            for m in entry.messages():
                entry_ids.append(entry.id)
                messages_list.append(m)

        return entry_ids, messages_list

    def predict(self, message: str) -> (Optional[int], int):
        message = self.data.clean_message(message)

        if not filter.is_valid(message):
            return None, None

        if len(self.messages) == 0:
            return None, None

        embed = self.classifier.encode([message])[0]

        p = cosine_similarity(
            [embed],
            self.embeds
        )[0]

        max_idx = p.argmax()
        class_idx = self.entry_ids[max_idx]

        if class_idx == -1:
            # nonsense
            return None, p.max()

        return class_idx, p.max()


class SvcClassifier:
    def __init__(self, data: Data, test_split: Optional[float] = None, random_state: int = None):
        self.test_split = test_split
        self.random_state = random_state
        self.data = data
        self.score: Optional[float] = None

        self.classifier: Optional[SVC] = None
        self.vectorizer: Optional[CountVectorizer] = None

        self.__load__()

    def __load__(self) -> None:
        if not self.data.is_valid():
            return

        sentences_train, sentences_test, y_train, y_test, class_weights = self.__get_data__()
        X_train, X_test = self.__load_vectorizer__(sentences_train, sentences_test)
        self.__load_classifier__(X_train, y_train)

        if self.test_split:
            sample_weight = []
            for value in y_test:
                sample_weight.append(1 - class_weights[value])

            self.score = self.classifier.score(X_test, y_test, sample_weight=sample_weight)

    def __load_vectorizer__(self, sentences_train, sentences_test) -> (np.ndarray, np.ndarray):
        self.vectorizer = CountVectorizer()
        return self.vectorizer.fit_transform(sentences_train), self.vectorizer.transform(sentences_test)

    def __load_classifier__(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        self.classifier = SVC(probability=True, class_weight="balanced", random_state=self.random_state)
        self.classifier.fit(X_train, y_train)

    def __get_data__(self) -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray):
        sentences = []
        y = []

        for text in self.data.nonsense():
            sentences.append(text)
            y.append(0)

        for entry in self.data.linked_faq():
            for message in entry.messages():
                sentences.append(message)
                y.append(entry.id + 1)

        class_weights = np.unique(y, return_counts=True)[1] / len(y)
        sentences_train, sentences_test, y_train, y_test = train_test_split(sentences, y, test_size=self.test_split,
                                                                            random_state=self.random_state,
                                                                            shuffle=True)
        return sentences_train, sentences_test, y_train, y_test, class_weights

    def predict(self, message: str) -> (Optional[int], int):
        if self.classifier is None:
            return None, None

        word_count = len(message.split(" "))
        if word_count < 3:
            return None, None

        if len(message) > 100:
            return None, None

        message = self.data.clean_message(message)

        if len(message) == 0:
            return None, None

        vector = self.vectorizer.transform([message]).toarray()[0]

        p = self.classifier.predict_proba([vector])
        argmax = p.argmax()
        class_idx = argmax - 1 if argmax > 0 else None

        return class_idx, p.max()
