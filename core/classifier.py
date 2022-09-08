from typing import Optional

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from core import filter
from core.files import Data


class BertClassifier:
    def __init__(self, data: Data, test_split: Optional[float] = None, random_state: int = None):
        self.test_split = test_split
        self.random_state = random_state
        self.data = data
        self.score: Optional[float] = None

        self.entry_ids, self.messages = self.messages()
        self.classifier: SentenceTransformer = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeds = self.classifier.encode(self.messages)

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

    def messages(self) -> (dict, list[str]):
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
