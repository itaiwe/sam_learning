"""Generates proxy actions for the ESAM algorithm."""
from itertools import combinations, product
from typing import List, Dict, Set, Any, Tuple



def n_choose_k(array: List[Any], k: int, effect_type: str) -> List[Tuple[Any, ...]]:
    """Implementation of the combinatorial choosing method.

    :param array: the array containing the items that we are choosing from the subset.
    :param k: the number of elements to choose from the list.
    :param effect_type: the type of the effect, i.e. add or delete effect.
    :return: the combination of items based on the input number of elements.
    """
    fluent_combinations = list(combinations(array, k))
    return [(*combination, effect_type) for combination in fluent_combinations]


class ProxyActionGenerator:
    """Class that is able to know whether an action contains duplicates and can create a proxy action to represent
    the inconsistent action usage."""

    def get_unit_clause_effects(
            self, effect_cnf_clauses: Dict[str, Set[Predicate]]) -> Set[Predicate]:
        """

        :param effect_cnf_clauses:
        :return:
        """
        unit_clause_effects = set()
        for cnf_effects in effect_cnf_clauses.values():
            if len(cnf_effects) == 1:
                unit_clause_effects.update(cnf_effects)

        return unit_clause_effects

    def get_precondition_fluents(
            self, precondition_cnfs: Dict[str, Set[ComparablePredicate]]) -> Set[ComparablePredicate]:
        """

        :param precondition_cnfs:
        :return:
        """
        precondition_predicates = set()
        for cnf in precondition_cnfs.values():
            precondition_predicates.update(cnf)

        return precondition_predicates

    def create_proxy_actions(self, action_name: str, action_signature: SignatureType,
                             surely_preconditions: Set[ComparablePredicate],
                             add_effect_cnfs: Dict[str, Set[ComparablePredicate]],
                             delete_effect_cnfs: Dict[str, Set[ComparablePredicate]]) -> List[Action]:
        """Creates the proxy action permutations based on the algorithm to create the power set of safe actions.

        :param action_name: the name of the original action that exists in the original domain.
        :param action_signature: the original signature of the action as known in the domain.
        :param surely_preconditions: the stored preconditions for the designated action.
        :param add_effect_cnfs: the add effects CNFs learned through the learning process.
        :param delete_effect_cnfs: the delete effects CNFs learned through the learning process.
        :return:
        """
        surely_add_effects = self.get_unit_clause_effects(add_effect_cnfs)
        surely_delete_effects = self.get_unit_clause_effects(delete_effect_cnfs)

        combined_combinations = self.create_effects_combinations(add_effect_cnfs, delete_effect_cnfs)
        effects_preconditions_product = self.create_effects_product(combined_combinations)

        proxy_actions = []
        for index, product_item in enumerate(effects_preconditions_product):
            effect_items = product_item[:-1]
            preconditions = product_item[-1]
            add_effects = []
            delete_effects = []
            for effect, effect_type in effect_items:
                if effect_type == "add-effect":
                    add_effects.append(effect)

                elif effect_type == "delete-effect":
                    delete_effects.append(effect)

            all_preconditions = list(surely_preconditions.union(preconditions))
            effect = Effect()
            effect.addlist = surely_add_effects.union(add_effects)
            effect.dellist = surely_delete_effects.union(delete_effects)
            new_action = Action(name=f"proxy-{action_name}-{index}",
                                signature=action_signature,
                                precondition=all_preconditions,
                                effect=effect)
            proxy_actions.append(new_action)

        return proxy_actions

    def create_effects_product(self, combined_combinations: List[List[Tuple[Any, ...]]]) -> List[Tuple[Any, ...]]:
        """

        :param combined_combinations:
        :return:
        """
        preconditions_effects_product = []
        selected_effects_product = list(product(*combined_combinations))
        for product_item in selected_effects_product:
            filtered_in_precondition = []
            for index, selected_effect_fluent in enumerate(product_item):
                relevant_fluents_variants = combined_combinations[index]
                fluent_preconditions_items = filter(lambda f: f != selected_effect_fluent, relevant_fluents_variants)
                fluent_preconditions = [item[0] for item in fluent_preconditions_items]
                filtered_in_precondition.extend(fluent_preconditions)

            preconditions_effects_product.append((*product_item, filtered_in_precondition))

        return preconditions_effects_product

    def create_effects_combinations(self, add_effect_cnfs, delete_effect_cnfs) -> List[List[Tuple[Any, ...]]]:
        non_unit_add_effect_fluents = [fluent_name for fluent_name in add_effect_cnfs if
                                       len(add_effect_cnfs[fluent_name]) > 1]
        non_unit_del_effect_fluents = [fluent_name for fluent_name in delete_effect_cnfs if
                                       len(delete_effect_cnfs[fluent_name]) > 1]
        combined_combinations = []
        for fluent_name in non_unit_add_effect_fluents:
            # For now we only support the case where don't remove parameters from the signature.
            combined_combinations.append(n_choose_k(list(add_effect_cnfs[fluent_name]), 1, "add-effect"))
        for fluent_name in non_unit_del_effect_fluents:
            combined_combinations.append(n_choose_k(list(delete_effect_cnfs[fluent_name]), 1, "delete-effect"))
        return combined_combinations
