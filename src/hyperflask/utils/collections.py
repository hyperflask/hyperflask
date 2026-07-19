from flask_collections.collection import BaseCollection


class ModelCollection(BaseCollection):
    @classmethod
    def matches_config(cls, config):
        return config.get("model")

    def load(self):
        pass
