__author__ = 'Tomasz Rybotycki'

import unittest
from math import factorial
from typing import List

from numpy import array, zeros

from src.BosonSamplingSimulator import BosonSamplingSimulator
from src.LossyBosonSamplingExactDistributionCalculators import BosonSamplingExperimentConfiguration, \
    BosonSamplingWithFixedLossesExactDistributionCalculator
from src.Quantum_Computations_Utilities import calculate_total_variation_distance
from src.simulation_strategies.FixedLossSimulationStrategy import FixedLossSimulationStrategy


class TestClassicalLossyBosonSamplingSimulator(unittest.TestCase):

    def setUp(self) -> None:
        # Generate permutation matrix and define initial state.
        self.initial_state = [1, 1, 1, 1, 0]
        self.permutation_matrix = array([
            [0, 0, 1, 0, 0],
            [1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1],
            [0, 1, 0, 0, 0],
        ])

        # Define some additional variables for more clear experiment configuration assignment.
        self.number_of_particles_lost = 2

        # Create configuration object.
        self.experiment_configuration = BosonSamplingExperimentConfiguration(
            interferometer_matrix=self.permutation_matrix,
            initial_state=self.initial_state,
            initial_number_of_particles=sum(self.initial_state),
            number_of_modes=len(self.initial_state),
            number_of_particles_lost=self.number_of_particles_lost,
            number_of_particles_left=sum(self.initial_state) - self.number_of_particles_lost
        )

    def test_approximate_and_exact_distribution_distance(self) -> None:
        exact_distribution_calculator = \
            BosonSamplingWithFixedLossesExactDistributionCalculator(self.experiment_configuration)
        exact_distribution = exact_distribution_calculator.calculate_exact_distribution()
        # TR TODO: Delta in assertion should depend on samples number!
        approximate_distribution = self.__calculate_approximate_distribution()
        distance = calculate_total_variation_distance(exact_distribution, approximate_distribution)
        bound = self.__calculate_distribution_error_bound()
        self.assertAlmostEqual(distance, bound, delta=1e-2)

    def __calculate_approximate_distribution(self, samples_number: int = 5000) -> List[float]:
        """
        Prepares the approximate distribution using boson sampling simulation method described by
        Oszmaniec and Brod. Obviously higher number of samples will generate better approximation.
        :return: Approximate distribution as a list.
        """
        exact_distribution_calculator = \
            BosonSamplingWithFixedLossesExactDistributionCalculator(self.experiment_configuration)

        possible_outcomes = exact_distribution_calculator.get_outcomes_in_proper_order()

        strategy = FixedLossSimulationStrategy(self.permutation_matrix,
                                               self.experiment_configuration.number_of_particles_left,
                                               self.experiment_configuration.number_of_modes)
        simulator = BosonSamplingSimulator(self.experiment_configuration.number_of_particles_left,
                                           self.experiment_configuration.initial_number_of_particles,
                                           self.experiment_configuration.number_of_modes, strategy)
        outcomes_probabilities = zeros(len(possible_outcomes))
        for i in range(samples_number):
            result = simulator.get_classical_simulation_results()

            for j in range(len(possible_outcomes)):
                # Check if obtained result is one of possible outcomes.
                if all(result == possible_outcomes[j]):  # Expect all elements of resultant list to be True.
                    outcomes_probabilities[j] += 1
                    break

        for i in range(len(outcomes_probabilities)):
            outcomes_probabilities[i] /= samples_number

        return outcomes_probabilities

    def __calculate_distribution_error_bound(self) -> float:
        n = self.experiment_configuration.initial_number_of_particles
        l = self.experiment_configuration.number_of_particles_left
        error_bound = 1.0 - (float(factorial(n)) / (pow(n, l) * factorial(n - l)))
        return error_bound
