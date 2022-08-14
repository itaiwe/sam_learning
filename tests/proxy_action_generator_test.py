"""integration tests for the proxy action generator algorithm"""
from pathlib import Path

from pddl_plus_parser.lisp_parsers import DomainParser
from pytest import fixture
from typing import Iterable, List, Set, Dict, NoReturn

from pddl_plus_parser.models import Action, Domain, GroundedPredicate, Predicate

from sam_learning.core import ProxyActionGenerator
from tests.consts import WOODWORKING_DOMAIN_PATH

#
# def print_proxy_actions(proxy_actions: List[Action]) -> NoReturn:
#     print()
#     for a in proxy_actions:
#         print(a.name)
#         print(a.signature)
#         print("positive preconditions - ", a.positive_preconditions)
#         print("negative preconditions - ", a.negative_preconditions)
#         print("add effects - ", a.add_effects)
#         print("delete effects - ", a.delete_effects)
#
#
# @fixture()
# def woodworking_domain() -> Domain:
#     return DomainParser(domain_path=WOODWORKING_DOMAIN_PATH, partial_parsing=True).parse_domain()
#
#
# @fixture()
# def do_grind_add_effect_cnf_with_duplicates(woodworking_domain: Domain) -> Dict[str, Set[Predicate]]:
#     return {
#         "is-smooth": {
#             Predicate(name="is-smooth",
#                       signature={"verysmooth": woodworking_domain.types["surface"]})
#         },
#         "treatment": {
#             Predicate(
#                 name="treatment",
#                 signature={
#                     "?x": woodworking_domain.types["part"],
#                     "?newtreatment": woodworking_domain.types["treatmentstatus"]}),
#             Predicate(
#                 name="treatment",
#                 signature={
#                     "?x": woodworking_domain.types["part"],
#                     "?oldtreatment": woodworking_domain.types["treatmentstatus"]}),
#             Predicate(
#                 name="treatment",
#                 signature={
#                     "?x": (woodworking_domain.types["part"],),
#                     "untreated": (woodworking_domain.types["treatmentstatus"])}),
#         }
#     }
#
#
# @fixture()
# def cut_board_add_effect_cnf_with_duplicates(woodworking_domain: Domain) -> Dict[str, Set[Predicate]]:
#     return {
#         "boardsize": {
#             Predicate(
#                 name="boardsize",
#                 signature={
#                     "?b": woodworking_domain.types["board"],
#                     "?size_before": woodworking_domain.types["aboardsize"]
#                 }),
#             Predicate(
#                 name="boardsize",
#                 signature={"?b":woodworking_domain.types["board"],
#                            "?size_after": woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize",
#                 signature={"?b":woodworking_domain.types["board"],
#                             "?s1": woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize",
#                 signature={"?b":woodworking_domain.types["board"],
#                             "?s2": woodworking_domain.types["aboardsize"]}),
#         },
#         "boardsize-successor": {
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?s2":woodworking_domain.types["aboardsize"],
#                            "?size_before":woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?s1":woodworking_domain.types["aboardsize"],
#                             "?size_before":woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?s2":woodworking_domain.types["aboardsize"],
#                             "?s1":woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?size_after":woodworking_domain.types["aboardsize"],
#                            "?size_before":woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?size_after": woodworking_domain.types["aboardsize"],
#                            "?s2": woodworking_domain.types["aboardsize"]}),
#             Predicate(
#                 name="boardsize-successor",
#                 signature={"?size_after": woodworking_domain.types["aboardsize"],
#                            "?s1": woodworking_domain.types["aboardsize"]}),
#         }
#     }
#
#
# @fixture()
# def do_grind_preconditions(woodworking_domain: Domain) -> Set[Predicate]:
#     return {
#         Predicate(
#             name="grind-treatment-change",
#             signature=[("?m", (woodworking_domain.types["grinder"],)),
#                        ("?oldtreatment", (woodworking_domain.types["treatmentstatus"],)),
#                        ("?newtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#         Predicate(name="is-smooth", signature=[("?oldsurface", (woodworking_domain.types["surface"],))]),
#         Predicate(name="available", signature=[("?x", (woodworking_domain.types["part"],))]),
#         Predicate(name="colour", signature=[("?x", (woodworking_domain.types["part"],)),
#                                                       ("?oldcolor", (woodworking_domain.types["acolour"],))]),
#         Predicate(name="goalsize", signature=[("?x", (woodworking_domain.types["part"],)),
#                                                         ("small", (woodworking_domain.types["apartsize"],))])
#     }
#
#
# @fixture()
# def proxy_action_generator() -> ProxyActionGenerator:
#     return ProxyActionGenerator()
#
#
# def test_create_effects_combinations_create_correct_combination_when_no_delete_effects_available(
#         proxy_action_generator: LightProxyActionGenerator,
#         do_grind_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]]):
#     combined_combinations = proxy_action_generator.create_effects_combinations(do_grind_add_effect_cnf_with_duplicates,
#                                                                                {})
#
#     assert len(combined_combinations) == 1
#
#
# def test_create_effects_combinations_create_correct_combination_when_two_ambiguities_exist(
#         proxy_action_generator: LightProxyActionGenerator,
#         cut_board_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]]):
#     combined_combinations = proxy_action_generator.create_effects_combinations(cut_board_add_effect_cnf_with_duplicates,
#                                                                                {})
#
#     assert len(combined_combinations) == 2
#
#
# def test_create_effects_combinations_create_correct_combination_when_delete_effects_present(
#         proxy_action_generator: LightProxyActionGenerator,
#         do_grind_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]],
#         cut_board_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]]):
#     combined_combinations = proxy_action_generator.create_effects_combinations(cut_board_add_effect_cnf_with_duplicates,
#                                                                                do_grind_add_effect_cnf_with_duplicates)
#
#     assert len(combined_combinations) == 3
#
#
# def test_create_effects_product_creates_both_potential_effects_and_preconditions(
#         woodworking_domain: Domain, proxy_action_generator: LightProxyActionGenerator):
#     test_predicates = [Predicate(
#         name="treatment",
#         signature=[
#             ("?x", (woodworking_domain.types["part"],)),
#             ("?newtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#         Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?oldtreatment", (woodworking_domain.types["treatmentstatus"],))]), ]
#     test_effect_cnfs = {
#         "treatment": set(test_predicates)
#     }
#     combined_combinations = proxy_action_generator.create_effects_combinations(test_effect_cnfs, {})
#     result_product = proxy_action_generator.create_effects_product(combined_combinations)
#
#     extracted_effects = set()
#     for index, (selected_effect, power_set_preconditions) in enumerate(result_product):
#         effect_predicate, _ = selected_effect
#         extracted_effects.add(effect_predicate)
#         assert len(power_set_preconditions) == 1
#         precondition_predicate = power_set_preconditions[0]
#         assert precondition_predicate != effect_predicate
#
#     assert extracted_effects == set(test_predicates)
#
#
# def test_create_effects_product_creates_both_potential_effects_and_preconditions_when_there_are_more_predicates(
#         woodworking_domain: Domain, proxy_action_generator: LightProxyActionGenerator):
#     test_predicates = [Predicate(
#         name="treatment",
#         signature=[
#             ("?x", (woodworking_domain.types["part"],)),
#             ("?newtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#         Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?oldtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#         Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?notrealtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#     ]
#     test_effect_cnfs = {
#         "treatment": set(test_predicates)
#     }
#     combined_combinations = proxy_action_generator.create_effects_combinations(test_effect_cnfs, {})
#     result_product = proxy_action_generator.create_effects_product(combined_combinations)
#
#     for index, (_, power_set_preconditions) in enumerate(result_product):
#         assert len(power_set_preconditions) == 2
#
#
# def test_create_effects_product_creates_correct_product_when_multiple_fluents_present(
#         proxy_action_generator: LightProxyActionGenerator,
#         do_grind_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]],
#         cut_board_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]]):
#     combined_combinations = proxy_action_generator.create_effects_combinations(cut_board_add_effect_cnf_with_duplicates,
#                                                                                do_grind_add_effect_cnf_with_duplicates)
#     result_product = proxy_action_generator.create_effects_product(combined_combinations)
#     assert len(result_product) == 72  # the product of the list sizes.
#     for power_set_items in result_product:
#         preconditions = power_set_items[-1]
#         assert len(preconditions) == 10
#
#
# def test_create_proxy_actions_with_a_simple_scenario(proxy_action_generator: LightProxyActionGenerator,
#                                                      woodworking_domain: Domain,
#                                                      do_grind_preconditions: Set[Predicate]):
#     test_action: Action = woodworking_domain.actions["do-grind"]
#     test_action_name = test_action.name
#     test_action_signature = test_action.signature
#     test_add_effects_cnf = {
#         "treatment": {Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?newtreatment", (woodworking_domain.types["treatmentstatus"],))]), Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?oldtreatment", (woodworking_domain.types["treatmentstatus"],))])}
#     }
#     delete_effects_cnf = {}
#
#     proxy_actions = proxy_action_generator.create_proxy_actions(action_name=test_action_name,
#                                                                 action_signature=test_action_signature,
#                                                                 surely_preconditions=do_grind_preconditions,
#                                                                 add_effect_cnfs=test_add_effects_cnf,
#                                                                 delete_effect_cnfs=delete_effects_cnf)
#     assert len(proxy_actions) == 2
#     print_proxy_actions(proxy_actions)
#
#
# def test_create_proxy_actions_with_three_predicate_ambiguous_effects(proxy_action_generator: LightProxyActionGenerator,
#                                                                      woodworking_domain: Domain,
#                                                                      do_grind_preconditions: Set[Predicate]):
#     test_action: Action = woodworking_domain.actions["do-grind"]
#     test_action_name = test_action.name
#     test_action_signature = test_action.signature
#     test_add_effects_cnf = {
#         "treatment": {Predicate(
#             name="treatment",
#             signature=[
#                 ("?x", (woodworking_domain.types["part"],)),
#                 ("?newtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#             Predicate(
#                 name="treatment",
#                 signature=[
#                     ("?x", (woodworking_domain.types["part"],)),
#                     ("?oldtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#             Predicate(
#                 name="treatment",
#                 signature=[
#                     ("?x", (woodworking_domain.types["part"],)),
#                     ("?blahtreatment", (woodworking_domain.types["treatmentstatus"],))]),
#         }
#     }
#     delete_effects_cnf = {}
#
#     proxy_actions = proxy_action_generator.create_proxy_actions(action_name=test_action_name,
#                                                                 action_signature=test_action_signature,
#                                                                 surely_preconditions=do_grind_preconditions,
#                                                                 add_effect_cnfs=test_add_effects_cnf,
#                                                                 delete_effect_cnfs=delete_effects_cnf)
#     assert len(proxy_actions) == 3
#     print_proxy_actions(proxy_actions)
#
#
# def test_create_proxy_actions_with_add_and_delete_effects(
#         proxy_action_generator: LightProxyActionGenerator,
#         woodworking_domain: Domain,
#         do_grind_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]],
#         cut_board_add_effect_cnf_with_duplicates: Dict[str, Set[Predicate]],
#         do_grind_preconditions: Set[Predicate]):
#     test_action: Action = woodworking_domain.actions["do-grind"]
#     test_action_name = test_action.name
#     test_action_signature = test_action.signature
#     proxy_actions = proxy_action_generator.create_proxy_actions(
#         action_name=test_action_name,
#         action_signature=test_action_signature,
#         surely_preconditions=do_grind_preconditions,
#         add_effect_cnfs=do_grind_add_effect_cnf_with_duplicates,
#         delete_effect_cnfs=cut_board_add_effect_cnf_with_duplicates)
#
#     assert len(proxy_actions) == 72
#     print_proxy_actions(proxy_actions)
