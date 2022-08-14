"""An extension to SAM-Learning that is able to learn even if there are repeated objects in the actions."""
import logging

from pddl_plus_parser.models import Domain, Observation, Predicate, ActionCall
from typing import List, Dict, Set

from sam_learning.core import LearnerDomain, PredicatesMatcher, ProxyActionGenerator
from sam_learning.learners import SAMLearner


class ExtendedSAM(SAMLearner):
    """An extension to SAM-Learning that is able to learn even if there are repeated objects in the actions."""

    logger: logging.Logger
    observations: List[Observation]
    partial_domain: LearnerDomain
    observed_actions: List[str]
    matcher: PredicatesMatcher
    add_effect_cnfs: Dict[str, Dict[str, Set[Predicate]]]
    delete_effect_cnfs: Dict[str, Dict[str, Set[Predicate]]]
    action_calls_with_duplicates: Dict[str, List[ActionCall]]
    actions_possible_preconditions: Dict[str, Set[Predicate]]
    proxy_action_generator: ProxyActionGenerator

    def __init__(self, partial_domain: Domain):
        super().__init__(partial_domain)
