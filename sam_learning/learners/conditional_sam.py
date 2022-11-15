"""Module containing the algorithm to learn action models with conditional effects."""
import logging
from typing import Dict, List, Optional, Set, Tuple

from pddl_plus_parser.models import Domain, PDDLObject, State, GroundedPredicate, ActionCall, Observation, \
    ObservedComponent

from sam_learning.learners import SAMLearner
from sam_learning.core import DependencySet, LearnerDomain, create_fully_observable_predicates, extract_effects


class ConditionalSAM(SAMLearner):
    """Class dedicated to learning action models with conditional effects."""
    dependency_set: Dict[str, DependencySet]
    logger: logging.Logger
    max_antecedents_size: int

    def __init__(self, partial_domain: Domain, max_antecedents_size: int,
                 preconditions_fluent_map: Optional[Dict[str, List[str]]] = None):
        super().__init__(partial_domain)
        self.logger = logging.getLogger(__name__)
        self.preconditions_fluent_map = preconditions_fluent_map if preconditions_fluent_map else {}
        self.safe_actions = []
        self.max_antecedents_size = max_antecedents_size
        self.dependency_set = {}

    def _create_possible_predicates(
            self, positive_state_predicates: Set[GroundedPredicate],
            negative_state_predicates: Set[GroundedPredicate]) -> Set[GroundedPredicate]:
        """Create the possible predicates that can be in the state.

        :param observed_objects: the objects that were observed in the trajectory.
        :param state: the current state.
        :return: the grounded observed predicates.
        """
        self.logger.debug("Creating a set of both negative and positive predicates.")
        positive_predicates = positive_state_predicates.copy()
        negative_predicates = negative_state_predicates.copy()
        return positive_predicates.union(negative_predicates)

    def _update_action_effects(self, grounded_action: ActionCall,
                               positive_state_predicates: List[GroundedPredicate],
                               negative_state_predicates: List[GroundedPredicate]) -> None:
        """Set the correct data for the action's effects.

        :param grounded_action: the action that is currently being executed.
        :param next_state: the state following the execution of the action.
        :param negative_state_predicates: the negative predicates that were encountered in the previous state.
        """
        observed_action = self.partial_domain.actions[grounded_action.name]
        positive_next_state_matches = self.matcher.get_possible_literal_matches(
            grounded_action, list(positive_state_predicates))
        negative_next_state_matches = self.matcher.get_possible_literal_matches(
            grounded_action, list(negative_state_predicates))
        observed_action.add_effects.difference_update(negative_next_state_matches)
        observed_action.delete_effects.difference_update(positive_next_state_matches)

    def _find_literals_not_in_state(
            self, grounded_action: ActionCall, positive_predicates: List[GroundedPredicate],
            negative_predicates: List[GroundedPredicate]) -> Set[str]:
        """

        :param grounded_action:
        :param positive_predicates:
        :param negative_predicates:
        :return:
        """
        state_positive_literals = self.matcher.get_possible_literal_matches(
            grounded_action, list(positive_predicates))
        state_negative_literals = self.matcher.get_possible_literal_matches(
            grounded_action, list(negative_predicates))
        # since we want to capture the literals NOT in s' we will transpose the literals values.
        missing_next_state_literals_str = [f"(not {literal.untyped_representation})" for literal in
                                           state_positive_literals]
        missing_next_state_literals_str.extend([literal.untyped_representation for literal in state_negative_literals])
        return set(missing_next_state_literals_str)

    def _find_literals_existing_in_state(
            self, grounded_action: ActionCall, positive_predicates, negative_predicates) -> Set[str]:
        """

        :param grounded_action:
        :param positive_predicates:
        :param negative_predicates:
        :return:
        """
        state_positive_literals = self.matcher.get_possible_literal_matches(
            grounded_action, list(positive_predicates))
        state_negative_literals = self.matcher.get_possible_literal_matches(
            grounded_action, list(negative_predicates))
        # since we want to capture the literals NOT in s' we will transpose the literals values.
        existing_state_literals_str = [literal.untyped_representation for literal in state_positive_literals]
        existing_state_literals_str.extend([f"(not {literal.untyped_representation})" for literal in
                                            state_negative_literals])
        return set(existing_state_literals_str)

    def _is_action_safe(self, action, param, positive_preconditions):
        pass

    def _extract_effects_dependency_set(self, action, param):
        pass

    def _initialize_actions_dependencies(
            self, grounded_action: ActionCall,
            positive_state_predicates: Set[GroundedPredicate],
            negative_state_predicates: Set[GroundedPredicate]) -> None:
        """Initialize the dependency set for a single action.

        :param grounded_action: the action that is currently being observed.
        :param state: the state that is currently being observed.
        :param observed_objects: the objects that were observed in the trajectory.
        """
        grounded_predicates = self._create_possible_predicates(positive_state_predicates, negative_state_predicates)
        lifted_predicates = self.matcher.get_possible_literal_matches(grounded_action, list(grounded_predicates))
        dependency_set = DependencySet(self.max_antecedents_size)
        dependency_set.initialize_dependencies(set(lifted_predicates))
        self.dependency_set[grounded_action.name] = dependency_set

    def _initialize_action_effects(
            self, grounded_action: ActionCall,
            positive_state_predicates: Set[GroundedPredicate],
            negative_state_predicates: Set[GroundedPredicate]) -> None:
        """Initialize the effects of the action to include all possible lifted predicates that appear in the state.

        :param grounded_action:
        :param positive_state_predicates
        :param negative_state_predicates:
        :return:
        """
        grounded_predicates = self._create_possible_predicates(positive_state_predicates, negative_state_predicates)
        lifted_predicates = self.matcher.get_possible_literal_matches(grounded_action, list(grounded_predicates))
        self.partial_domain.actions[grounded_action.name].add_effects.update(lifted_predicates)
        self.partial_domain.actions[grounded_action.name].delete_effects.update(lifted_predicates)

    def _update_effects_data(self, grounded_action: ActionCall,
                             negative_state_predicates: Set[GroundedPredicate],
                             next_state: State, previous_state: State) -> None:
        """

        :param grounded_action:
        :param negative_state_predicates:
        :param next_state:
        :param previous_state:
        :return:
        """
        positive_next_state_predicates, negative_next_state_predicates = \
            create_fully_observable_predicates(next_state, negative_state_predicates)
        positive_pre_state_predicates, negative_pre_state_predicates = create_fully_observable_predicates(
            previous_state, negative_state_predicates)
        self._update_action_effects(grounded_action, positive_next_state_predicates, negative_next_state_predicates)
        self.remove_not_possible_dependencies(grounded_action,
                                              previous_state,
                                              next_state,
                                              positive_pre_state_predicates,
                                              negative_pre_state_predicates,
                                              positive_next_state_predicates,
                                              negative_next_state_predicates)
        self.remove_impossible_effects(grounded_action, positive_next_state_predicates, negative_next_state_predicates)

    def remove_existing_previous_state_dependencies(
            self, grounded_action: ActionCall, positive_pre_state_predicates, negative__state_predicates,
            positive_next_state_predicates, negative_next_state_predicates) -> None:
        """

        :param grounded_action:
        :param positive_pre_state_predicates:
        :param negative__state_predicates:
        :param positive_next_state_predicates:
        :param negative_next_state_predicates:
        :return:
        """
        missing_next_state_literals_str = self._find_literals_not_in_state(
            grounded_action, positive_next_state_predicates, negative_next_state_predicates)
        existing_previous_state_literals_str = self._find_literals_existing_in_state(
            grounded_action, positive_pre_state_predicates, negative__state_predicates)
        for literal in missing_next_state_literals_str:
            self.dependency_set[grounded_action.name].remove_dependencies(
                literal=literal, literals_to_remove=existing_previous_state_literals_str)

    def remove_non_existing_previous_state_dependencies(
            self, grounded_action: ActionCall, previous_state: State, next_state: State,
            positive_pre_state_predicates: List[GroundedPredicate],
            negative_pre_state_predicates: List[GroundedPredicate]) -> None:
        """

        :param grounded_action:
        :param previous_state:
        :param next_state:
        :param positive_pre_state_predicates:
        :param negative_pre_state_predicates:
        :return:
        """
        grounded_add_effects, grounded_del_effects = extract_effects(previous_state, next_state)
        lifted_add_effects = self.matcher.get_possible_literal_matches(
            grounded_action, list(grounded_add_effects))
        lifted_delete_effects = self.matcher.get_possible_literal_matches(
            grounded_action, list(grounded_del_effects))
        effects_str = [literal.untyped_representation for literal in lifted_add_effects]
        effects_str.extend([f"(not {literal.untyped_representation})" for literal in lifted_delete_effects])
        missing_pre_state_literals_str = self._find_literals_not_in_state(grounded_action,
                                                                          positive_pre_state_predicates,
                                                                          negative_pre_state_predicates)
        for literal in effects_str:
            self.dependency_set[grounded_action.name].remove_dependencies(
                literal=literal, literals_to_remove=missing_pre_state_literals_str)

    def remove_not_possible_dependencies(
            self, grounded_action: ActionCall, previous_state: State, next_state: State,
            positive_pre_state_predicates: List[GroundedPredicate],
            negative_pre_state_predicates: List[GroundedPredicate],
            positive_next_state_predicates: List[GroundedPredicate],
            negative_next_state_predicates: List[GroundedPredicate]) -> None:
        """

        :param grounded_action:
        :param previous_state:
        :param next_state:
        :param positive_pre_state_predicates:
        :param negative_pre_state_predicates:
        :param positive_next_state_predicates:
        :param negative_next_state_predicates:
        :return:
        """
        self.remove_existing_previous_state_dependencies(
            grounded_action, positive_pre_state_predicates, negative_pre_state_predicates,
            positive_next_state_predicates, negative_next_state_predicates)
        self.remove_non_existing_previous_state_dependencies(
            grounded_action, previous_state, next_state, positive_pre_state_predicates, negative_pre_state_predicates)

    def remove_impossible_effects(self, grounded_action: ActionCall,
                                  positive_predicates: List[GroundedPredicate],
                                  negative_predicates: List[GroundedPredicate]) -> None:
        """

        :param grounded_action:
        :param positive_predicates:
        :param negative_predicates:
        :return:
        """
        positive_literals = self.matcher.get_possible_literal_matches(grounded_action, list(positive_predicates))
        negative_literals = self.matcher.get_possible_literal_matches(grounded_action, list(negative_predicates))
        self.partial_domain.actions[grounded_action.name].add_effects.difference_update(negative_literals)
        self.partial_domain.actions[grounded_action.name].delete_effects.difference_update(positive_literals)

    def add_new_action(self, grounded_action: ActionCall, previous_state: State,
                       next_state: State, negative_state_predicates: Set[GroundedPredicate]) -> None:
        """Create a new action in the domain.

        :param grounded_action: the grounded action that was executed according to the trajectory.
        :param previous_state: the state that the action was executed on.
        :param next_state: the state that was created after executing the action on the previous
        :param negative_state_predicates: the negative predicates that were encountered in the state.
        """
        self.logger.info(f"Adding the action {str(grounded_action)} to the domain.")
        observed_action = self.partial_domain.actions[grounded_action.name]
        super()._add_new_action_preconditions(
            grounded_action, observed_action, negative_state_predicates, previous_state)
        self._update_effects_data(grounded_action, negative_state_predicates, next_state, previous_state)
        self.observed_actions.append(observed_action.name)
        self.logger.debug(f"Finished adding the action {grounded_action.name}.")

    def update_action(
            self, grounded_action: ActionCall, previous_state: State, next_state: State,
            negative_state_predicates: Set[GroundedPredicate]) -> None:
        """Create a new action in the domain.

        :param grounded_action: the grounded action that was executed according to the trajectory.
        :param previous_state: the state that the action was executed on.
        :param next_state: the state that was created after executing the action on the previous
            state.
        :param negative_state_predicates: the negative predicates that were encountered in the state.
        """
        super()._update_action_preconditions(grounded_action, previous_state)
        self._update_effects_data(grounded_action, negative_state_predicates, next_state, previous_state)
        self.logger.debug(f"Done updating the action - {grounded_action.name}")

    def handle_single_trajectory_component(
            self, component: ObservedComponent, observed_objects: Dict[str, PDDLObject]) -> None:
        """

        :param component:
        :param observed_objects:
        :return:
        """
        previous_state = component.previous_state
        grounded_action = component.grounded_action_call
        next_state = component.next_state
        action_name = grounded_action.name
        positive_state_predicates, negative_state_predicates = super()._create_complete_world_state(
            observed_objects, previous_state)
        if action_name not in self.observed_actions:
            self._initialize_actions_dependencies(
                grounded_action, positive_state_predicates, negative_state_predicates)
            self._initialize_action_effects(grounded_action, positive_state_predicates, negative_state_predicates)
            self.add_new_action(grounded_action, previous_state, next_state, negative_state_predicates)

        else:
            self.update_action(grounded_action, previous_state, next_state, negative_state_predicates)

    def construct_safe_actions(self) -> None:
        """Constructs the single-agent actions that are safe to execute."""
        for action in self.partial_domain.actions.values():
            if action.name not in self.observed_actions:
                continue

            self.logger.debug("Constructing safe action for %s", action.name)
            if not self._is_action_safe(action, self.dependency_set[action.name], action.positive_preconditions):
                self.logger.warning("Action %s is not safe to execute!", action.name)
                action.positive_preconditions = set()
                action.negative_preconditions = set()
                continue

            self.logger.debug("Action %s is safe to execute.", action.name)
            self._extract_effects_dependency_set(action, self.dependency_set[action.name])
            self.safe_actions.append(action.name)

    def learn_action_model(self, observations: List[Observation]) -> Tuple[LearnerDomain, Dict[str, str]]:
        """Learn the SAFE action model from the input trajectories.

        :param observations: the list of trajectories that are used to learn the safe action model.
        :return: a domain containing the actions that were learned.
        """
        self.logger.info("Starting to learn the action model!")
        super().deduce_initial_inequality_preconditions()
        for observation in observations:
            observed_trajectory_objects = observation.grounded_objects
            for component in observation.components:
                self.handle_single_trajectory_component(component, observed_trajectory_objects)

        self.construct_safe_actions()
        learning_report = super()._construct_learning_report()
        return self.partial_domain, learning_report
