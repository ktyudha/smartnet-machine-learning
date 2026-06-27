from sklearn.tree import DecisionTreeClassifier


def build(**params):
    return DecisionTreeClassifier(random_state=42, **params)
