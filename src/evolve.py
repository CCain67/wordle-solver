from .wordle import WordleSolver


# evolve.py
class EpochHandler:
    """
    Chain of Responsibility class which controls the flow of a evolution epoch:
        fitness evaluation -> breed -> cull
    """

    def __init__(self) -> None:
        pass


class Population:
    def __init__(self) -> None:
        pass


class Culler:
    def __init__(self) -> None:
        pass


class Breeder:
    def __init__(self) -> None:
        pass


class FitnessEvaluator:
    def __init__(self) -> None:
        pass
