"""An action model learning algorithm that uses the Oblique Tree algorithm with some concepts of N-SAM Learning."""
from typing import Dict, List, Optional, Tuple

from pddl_plus_parser.models import Domain, Observation

from sam_learning.core import LearnerDomain, NotSafeActionError
from sam_learning.core.oblique_tree_fluents_learning import ObliqueTreeFluentsLearning
from sam_learning.learners.numeric_sam import PolynomialSAMLearning


class ObliqueTreeModelLearner(PolynomialSAMLearning):
    """An action model learning algorithm that uses the Oblique Tree algorithm with some concepts of N-SAM Learning."""

    def __init__(self, partial_domain: Domain, preconditions_fluent_map: Optional[Dict[str, List[str]]] = None,
                 polynomial_degree: int = 1):
        super().__init__(partial_domain, preconditions_fluent_map, polynomial_degree)

    def learn_unsafe_action_model(self, positive_observations: List[Observation],
                                  negative_observations: List[Observation]) -> Tuple[LearnerDomain, Dict[str, str]]:
        """Learns the action model from the given observations using unsafe methods.

        :param positive_observations: the observations to learn the action model from.
        :param negative_observations: the negative observations containing faults in them.
        :return: the learned action model and the mapping from the action names to the action names in the
            learned domain.
        """
        self.logger.info("Learning the action model from the given observations.")
        allowed_actions = {}
        learning_metadata = {}
        super().deduce_initial_inequality_preconditions()
        for observation in positive_observations:
            for component in observation.components:
                super().handle_single_trajectory_component(component)

        for action_name, action in self.partial_domain.actions.items():
            if action_name not in self.storage:
                self.logger.debug(f"The action - {action_name} has not been observed in the trajectories!")
                continue

            numeric_preconditions_learner = ObliqueTreeFluentsLearning(
                action_name, self.polynom_degree, self.partial_domain)
            self.storage[action_name].filter_out_inconsistent_state_variables()
            try:
                action.numeric_preconditions = numeric_preconditions_learner.learn_preconditions(
                    positive_observations, negative_observations)
                action.numeric_effects = self.storage[action_name].construct_assignment_equations()
                allowed_actions[action_name] = action
                learning_metadata[action_name] = "OK"

            except NotSafeActionError as e:
                self.logger.debug(f"The action - {e.action_name} is not safe for execution, reason - {e.reason}")
                learning_metadata[action_name] = e.solution_type.name

        self.partial_domain.actions = allowed_actions
        return self.partial_domain, learning_metadata
