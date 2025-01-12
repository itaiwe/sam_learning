"""Module test for Conditional SAM."""
from typing import Set

from pddl_plus_parser.lisp_parsers import DomainParser, ProblemParser, TrajectoryParser
from pddl_plus_parser.models import Domain, Problem, Observation, GroundedPredicate
from pytest import fixture

from sam_learning.core import DependencySet
from sam_learning.learners import ConditionalSAM
from sam_learning.learners.conditional_sam import _extract_predicate_data
from tests.consts import SPIDER_DOMAIN_PATH, SPIDER_PROBLEM_PATH, SPIDER_TRAJECTORY_PATH


@fixture()
def spider_domain() -> Domain:
    return DomainParser(SPIDER_DOMAIN_PATH, partial_parsing=True).parse_domain()


@fixture()
def spider_problem(spider_domain: Domain) -> Problem:
    return ProblemParser(problem_path=SPIDER_PROBLEM_PATH, domain=spider_domain).parse_problem()


@fixture()
def spider_observation(spider_domain: Domain, spider_problem: Problem) -> Observation:
    return TrajectoryParser(spider_domain, spider_problem).parse_trajectory(SPIDER_TRAJECTORY_PATH)


@fixture()
def conditional_sam(spider_domain: Domain) -> ConditionalSAM:
    return ConditionalSAM(spider_domain, max_antecedents_size=1)


@fixture()
def positive_initial_state_predicates(spider_observation: Observation) -> Set[GroundedPredicate]:
    initial_state = spider_observation.components[0].previous_state
    initial_state_predicates = set()
    for predicate in initial_state.state_predicates.values():
        initial_state_predicates.update(predicate)
    return initial_state_predicates


def test_merge_positive_and_negative_predicates_creates_correct_set_with_combined_positive_and_negative_predicates(
        conditional_sam: ConditionalSAM, positive_initial_state_predicates: Set[GroundedPredicate]):
    output_predicates = conditional_sam._merge_positive_and_negative_predicates(positive_initial_state_predicates,
                                                                                set())
    assert len(output_predicates) == len(positive_initial_state_predicates)


def test_initialize_actions_dependencies_sets_correct_effects(conditional_sam: ConditionalSAM,
                                                              spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].add_effects) > 0
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].delete_effects) > 0
    print(len(conditional_sam.partial_domain.actions[grounded_action.name].add_effects))
    print(len(conditional_sam.partial_domain.actions[grounded_action.name].delete_effects))


def test_initialize_actions_dependencies_adds_correct_dependencies(conditional_sam: ConditionalSAM,
                                                                   spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    assert conditional_sam.dependency_set[grounded_action.name] is not None


def test_update_action_effects_sets_correct_effects(conditional_sam: ConditionalSAM, spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    initialized_add_effects = conditional_sam.partial_domain.actions[grounded_action.name].add_effects
    initialized_delete_effects = conditional_sam.partial_domain.actions[grounded_action.name].delete_effects
    conditional_sam._update_action_effects(grounded_action)
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].add_effects) <= len(initialized_add_effects)
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].delete_effects) <= len(
        initialized_delete_effects)


def test_find_literals_not_in_state_correctly_sets_the_literals_that_do_not_appear_in_the_state(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    predicates_not_in_state = conditional_sam._find_literals_not_in_state(
        grounded_action=grounded_action,
        positive_predicates=conditional_sam.previous_state_positive_predicates,
        negative_predicates=conditional_sam.previous_state_negative_predicates)

    negative_preconditions = {"(currently-updating-movable )", "(currently-updating-unmovable )",
                              "(currently-updating-part-of-tableau )", "(currently-collecting-deck )",
                              "(currently-dealing )"}

    assert negative_preconditions.issubset(predicates_not_in_state)


def test_find_literals_existing_in_state_correctly_sets_the_literals_that_do_appear_in_the_state(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    predicates_not_in_state = conditional_sam._find_literals_existing_in_state(
        grounded_action=grounded_action,
        positive_predicates=conditional_sam.previous_state_positive_predicates,
        negative_predicates=conditional_sam.previous_state_negative_predicates)

    negated_negative_preconditions = {"(currently-updating-movable )", "(currently-updating-unmovable )",
                                      "(currently-updating-part-of-tableau )", "(currently-collecting-deck )",
                                      "(currently-dealing )"}

    assert not negated_negative_preconditions.issubset(predicates_not_in_state)


def test_remove_non_existing_previous_state_dependencies_removes_correct_predicates_from_literals_that_are_effects_only(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    previous_state = spider_observation.components[0].previous_state
    grounded_action = spider_observation.components[0].grounded_action_call
    next_state = spider_observation.components[0].next_state
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action, previous_state=previous_state, next_state=next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam._update_action_effects(grounded_action)
    conditional_sam._remove_non_existing_previous_state_dependencies(grounded_action, previous_state, next_state)
    not_dependencies = {"(currently-updating-movable )", "(currently-updating-unmovable )",
                        "(currently-updating-part-of-tableau )", "(currently-collecting-deck )",
                        "(currently-dealing )"}

    for not_dependency in not_dependencies:
        assert {not_dependency} not in conditional_sam.dependency_set[grounded_action.name].dependencies[
            "(currently-dealing )"]


def test_remove_existing_previous_state_dependencies_removes_correct_predicates_from_literals_not_in_effects(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    previous_state = spider_observation.components[0].previous_state
    grounded_action = spider_observation.components[0].grounded_action_call
    next_state = spider_observation.components[0].next_state
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action, previous_state=previous_state, next_state=next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam._update_action_effects(grounded_action)
    conditional_sam._remove_existing_previous_state_dependencies(grounded_action)
    not_dependencies = {"(currently-updating-movable )", "(currently-updating-unmovable )",
                        "(currently-updating-part-of-tableau )", "(currently-collecting-deck )",
                        "(currently-dealing )"}

    tested_literal = "(not (currently-collecting-deck ))"
    for not_dependency in not_dependencies:
        assert {not_dependency} in conditional_sam.dependency_set[grounded_action.name].dependencies[tested_literal]
        assert {f"(not {not_dependency})"} in conditional_sam.dependency_set[grounded_action.name].dependencies[
            tested_literal]


def test_update_effects_data_updates_the_relevant_effects_and_removes_irrelevant_literals_from_dependency_set(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    previous_state = spider_observation.components[0].previous_state
    grounded_action = spider_observation.components[0].grounded_action_call
    next_state = spider_observation.components[0].next_state
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action, previous_state=previous_state, next_state=next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    initialized_add_effects = conditional_sam.partial_domain.actions[grounded_action.name].add_effects
    initialized_delete_effects = conditional_sam.partial_domain.actions[grounded_action.name].delete_effects
    conditional_sam._update_effects_data(grounded_action, previous_state, next_state)
    not_dependencies = {"(currently-updating-movable )", "(currently-updating-unmovable )",
                        "(currently-updating-part-of-tableau )", "(currently-collecting-deck )",
                        "(currently-dealing )"}

    tested_literal = "(not (currently-collecting-deck ))"
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].add_effects) <= len(initialized_add_effects)
    assert len(conditional_sam.partial_domain.actions[grounded_action.name].delete_effects) <= len(
        initialized_delete_effects)
    for not_dependency in not_dependencies:
        assert {not_dependency} in conditional_sam.dependency_set[grounded_action.name].dependencies[tested_literal]
        assert {f"(not {not_dependency})"} in conditional_sam.dependency_set[grounded_action.name].dependencies[
            tested_literal]
        assert {not_dependency} not in conditional_sam.dependency_set[grounded_action.name].dependencies[
            "(currently-dealing )"]


def test_add_new_action_updates_action_negative_preconditions(conditional_sam: ConditionalSAM,
                                                              spider_observation: Observation,
                                                              spider_domain: Domain):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam.add_new_action(grounded_action,
                                   spider_observation.components[0].previous_state,
                                   spider_observation.components[0].next_state)

    added_action = conditional_sam.partial_domain.actions[grounded_action.name]
    negative_preconditions = {f"(not {precondition.untyped_representation})" for precondition in
                              added_action.negative_preconditions}
    assert negative_preconditions.issuperset({"(not (currently-updating-movable ))",
                                              "(not (currently-updating-unmovable ))",
                                              "(not (currently-updating-part-of-tableau ))",
                                              "(not (currently-collecting-deck ))",
                                              "(not (currently-dealing ))"})


def test_add_new_action_updates_action_positive_preconditions(conditional_sam: ConditionalSAM,
                                                              spider_observation: Observation,
                                                              spider_domain: Domain):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam.add_new_action(grounded_action,
                                   spider_observation.components[0].previous_state,
                                   spider_observation.components[0].next_state)

    added_action = conditional_sam.partial_domain.actions[grounded_action.name]
    positive_preconditions = {precondition.untyped_representation for precondition in
                              added_action.positive_preconditions}
    assert len(positive_preconditions) == 0


def test_add_new_action_updates_action_effects(conditional_sam: ConditionalSAM,
                                               spider_observation: Observation,
                                               spider_domain: Domain):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    initialized_add_effects = conditional_sam.partial_domain.actions[grounded_action.name].add_effects
    initialized_delete_effects = conditional_sam.partial_domain.actions[grounded_action.name].delete_effects
    conditional_sam.add_new_action(grounded_action,
                                   spider_observation.components[0].previous_state,
                                   spider_observation.components[0].next_state)

    added_action = conditional_sam.partial_domain.actions[grounded_action.name]
    assert len(added_action.add_effects) <= len(initialized_add_effects)
    assert len(added_action.delete_effects) <= len(initialized_delete_effects)


def test_update_action_updates_preconditions(conditional_sam: ConditionalSAM,
                                             spider_observation: Observation,
                                             spider_domain: Domain):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam.add_new_action(grounded_action,
                                   spider_observation.components[0].previous_state,
                                   spider_observation.components[0].next_state)
    conditional_sam.update_action(grounded_action,
                                  spider_observation.components[0].previous_state,
                                  spider_observation.components[0].next_state)

    added_action = conditional_sam.partial_domain.actions[grounded_action.name]
    negative_preconditions = {f"(not {precondition.untyped_representation})" for precondition in
                              added_action.negative_preconditions}
    assert negative_preconditions.issuperset({"(not (currently-updating-movable ))",
                                              "(not (currently-updating-unmovable ))",
                                              "(not (currently-updating-part-of-tableau ))",
                                              "(not (currently-collecting-deck ))",
                                              "(not (currently-dealing ))"})


def test_is_action_safe_with_a_new_action_returns_that_action_is_not_safe(conditional_sam: ConditionalSAM,
                                                                          spider_observation: Observation):
    grounded_action = spider_observation.components[0].grounded_action_call
    conditional_sam._create_fully_observable_triplet_predicates(
        current_action=grounded_action,
        previous_state=spider_observation.components[0].previous_state,
        next_state=spider_observation.components[0].next_state)

    conditional_sam._initialize_actions_dependencies(grounded_action)
    conditional_sam.add_new_action(grounded_action,
                                   spider_observation.components[0].previous_state,
                                   spider_observation.components[0].next_state)

    assert not conditional_sam._is_action_safe(conditional_sam.partial_domain.actions[grounded_action.name],
                                               conditional_sam.dependency_set[grounded_action.name])


def test_extract_predicate_data_returns_correct_predicate_when_predicate_contains_no_parameters(
        conditional_sam: ConditionalSAM, spider_domain: Domain):
    test_predicate = "(currently-updating-movable )"
    learner_action = conditional_sam.partial_domain.actions["start-dealing"]
    result_predicate = _extract_predicate_data(learner_action, test_predicate, spider_domain.constants)
    assert result_predicate.name == "currently-updating-movable"
    assert len(result_predicate.signature) == 0


def test_extract_predicate_data_returns_correct_predicate_predicate_contains_parameters(
        conditional_sam: ConditionalSAM, spider_domain: Domain):
    test_predicate = "(to-deal ?c ?totableau ?fromdeal ?from)"
    learner_action = conditional_sam.partial_domain.actions["deal-card"]
    result_predicate = _extract_predicate_data(learner_action, test_predicate, spider_domain.constants)
    assert result_predicate.name == "to-deal"
    assert len(result_predicate.signature) == 4
    assert result_predicate.signature["?c"].name == "card"
    assert result_predicate.signature["?totableau"].name == "tableau"
    assert result_predicate.signature["?fromdeal"].name == "deal"
    assert result_predicate.signature["?from"].name == "cardposition"


def test_extract_predicate_data_returns_correct_predicate_predicate_contains_constants(
        conditional_sam: ConditionalSAM, spider_domain: Domain):
    test_predicate = "(on ?c discard)"
    learner_action = conditional_sam.partial_domain.actions["collect-card"]
    result_predicate = _extract_predicate_data(learner_action, test_predicate, spider_domain.constants)
    assert result_predicate.name == "on"
    assert len(result_predicate.signature) == 2
    assert result_predicate.signature["?c"].name == "card"
    assert result_predicate.signature["discard"].name == "cardposition"


def test_construct_conditional_effects_from_dependency_set_constructs_correct_conditional_effect(
        conditional_sam: ConditionalSAM):
    dependecy_set = DependencySet(max_size_antecedents=1)
    dependecy_set.dependencies = {
        "(currently-updating-unmovable )": [{"(not (can-continue-group ?c ?to))"}],
        "(make-unmovable ?to)": [{"(not (can-continue-group ?c ?to))"}]
    }
    test_action = conditional_sam.partial_domain.actions["deal-card"]

    conditional_sam._construct_conditional_effects_from_dependency_set(test_action, dependecy_set)
    conditional_effects = conditional_sam.partial_domain.actions[test_action.name].conditional_effects
    assert len(conditional_effects) == 2

    possible_add_effects = ["(currently-updating-unmovable )", "(make-unmovable ?to)"]

    effect = conditional_effects.pop()
    assert len(effect.negative_conditions) == 1
    assert effect.negative_conditions.pop().untyped_representation == "(can-continue-group ?c ?to)"
    assert len(effect.positive_conditions) == 0
    add_effect = effect.add_effects.pop().untyped_representation
    assert add_effect in possible_add_effects

    possible_add_effects.remove(add_effect)

    effect = conditional_effects.pop()
    assert len(effect.negative_conditions) == 1
    assert effect.negative_conditions.pop().untyped_representation == "(can-continue-group ?c ?to)"
    assert effect.add_effects.pop().untyped_representation in possible_add_effects


def test_handle_single_trajectory_component_learns_correct_information(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    conditional_sam.current_trajectory_objects = spider_observation.grounded_objects
    conditional_sam.handle_single_trajectory_component(spider_observation.components[0])
    conditional_sam._remove_preconditions_from_effects(
        conditional_sam.partial_domain.actions["start-dealing"])
    pddl_action = conditional_sam.partial_domain.actions["start-dealing"].to_pddl()
    assert "(not (currently-updating-unmovable ))" in pddl_action
    assert "(not (currently-updating-movable ))" in pddl_action
    assert "(not (currently-collecting-deck ))" in pddl_action
    assert "(not (currently-updating-part-of-tableau ))" in pddl_action
    assert "(not (currently-dealing ))" in pddl_action


def test_is_action_safe_returns_true_when_dependency_set_contains_only_unconditional_effect_of_action(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    conditional_sam.current_trajectory_objects = spider_observation.grounded_objects
    conditional_sam.handle_single_trajectory_component(spider_observation.components[0])
    test_action = conditional_sam.partial_domain.actions["start-dealing"]
    conditional_sam.dependency_set[test_action.name].dependencies = {
        "(currently-dealing )": conditional_sam.dependency_set[test_action.name].dependencies["(currently-dealing )"]
    }
    assert conditional_sam._is_action_safe(test_action, conditional_sam.dependency_set[test_action.name])


def test_is_action_safe_returns_false_after_one_trajectory_component(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    conditional_sam.current_trajectory_objects = spider_observation.grounded_objects
    conditional_sam.handle_single_trajectory_component(spider_observation.components[0])
    test_action = conditional_sam.partial_domain.actions["start-dealing"]
    assert not conditional_sam._is_action_safe(test_action, conditional_sam.dependency_set[test_action.name])


def test_learn_action_model_learns_restrictive_action_mode(
        conditional_sam: ConditionalSAM, spider_observation: Observation):
    learned_model, _ = conditional_sam.learn_action_model([spider_observation])
    print(learned_model.to_pddl())