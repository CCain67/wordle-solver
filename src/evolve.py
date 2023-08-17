"""This module defines the classes which are required to run the evolutionary algorithm"""
from __future__ import annotations

from random import random, sample, uniform

from scipy.stats import hmean

from .wordle import ALPHABET, WordleSimulator, WordleSolver


class EpochHandler:
    """
    Chain of Responsibility class which controls the flow of an evolution epoch:
        fitness evaluation -> breed -> cull
    """

    def run_epochs(
        self,
        number_of_epochs: int,
        cutoff_number: int,
        population: Population,
        answer_pool: list[str],
    ) -> Population:
        breeder = Breeder()
        culler = Culler()
        evaluator = FitnessEvaluator()

        epoch = 0
        while epoch <= number_of_epochs:
            evaluation_results = evaluator.evaluate(population, answer_pool)
            population = culler.cull_population(evaluation_results, cutoff_number)

            elites = population.members[:cutoff_number]

            new_members = 0
            while new_members < cutoff_number:
                population.members += [breeder.crossover(*sample(elites, 2))]
                new_members += 1
            epoch += 1
        return population


class Population:
    def __init__(self, members: list[WordleSolver] = None) -> None:
        self.members = members

    def __getitem__(self, key) -> WordleSolver:
        return self.members[key]

    def __iter__(self):
        return iter(self.members)

    def __len__(self) -> int:
        return len(self.members)

    @classmethod
    def from_random(cls, population_size: int, initial_guess: str = None) -> Population:
        """Constructs a population of random solvers of size {population_size}"""
        return cls(
            [
                WordleSolver(
                    initial_guess=initial_guess,
                    weights={letter: uniform(-1, 1) for letter in ALPHABET},
                )
                for i in range(population_size)
            ]
        )


class Breeder:
    """Class which produces offspring from two parent solvers, or mutates a given solver"""

    def crossover(
        self, parent_solver_a: WordleSolver, parent_solver_b: WordleSolver
    ) -> WordleSolver:
        t = random()
        return WordleSolver(
            weights={  # computation below gives a point on the line between the "genes"
                letter: t
                * (parent_solver_a.weights[letter] - parent_solver_b.weights[letter])
                + parent_solver_b.weights[letter]
                for letter in ALPHABET
            }
        )

    def mutate(
        self, solver: WordleSolver, number_of_genes_to_alter: int = 1
    ) -> WordleSolver:
        letters = sample(ALPHABET, number_of_genes_to_alter)
        solver_genes = solver.weights
        for letter in letters:
            t = random()
            solver_genes[letter] = t * (-1.0) + (1 - t) * solver_genes[letter]
        return solver


class Culler:
    """Class which culls a population of WordleSolvers depending on given parameters"""

    def cull_population(self, population_score: dict, cutoff_number: int) -> Population:
        length = len(population_score)
        return Population(list(population_score.keys())[: length - cutoff_number])


class FitnessEvaluator:
    """Class which evaluates the fitness of each member of a population
    of wordle solvers, and generates a report.
    """

    def evaluate(self, population: Population, answer_pool: list[str]) -> dict:
        """Evaluates the population of WordleSolvers given on a fixed answer pool"""
        simulator = WordleSimulator()
        results = {
            solver: hmean(
                simulator.partial_simulation(solver, answer_pool).value_counts()
            )
            for solver in population
        }
        return dict(sorted(results.items(), key=lambda item: item[1]))
