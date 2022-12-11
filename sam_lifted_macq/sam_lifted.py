"""The Safe Action Model Learning algorithm module."""
import os,sys
sys.path.append("./")
import logging
from collections import defaultdict
from itertools import combinations
from typing import List, Tuple, Dict, Set

from pddl_plus_parser.models import Observation, Predicate, ActionCall, State, Domain, ObservedComponent, PDDLObject, GroundedPredicate

from ...sam_helper import PredicatesMatcher, extract_effects, LearnerDomain, contains_duplicates, VocabularyCreator, \
    LearnerAction

from sam_model import SAMLearner

from observer import Observer

from . import Model, LearnedAction, LearnedFluent

class SAM_Observer:
    """Class that represents the safe action model learner algorithm.

    Notice: This class does not support domains with constants or with the same object mapped to multiple parameters.
    """

    logger: logging.Logger
    partial_domain: LearnerDomain
    matcher: PredicatesMatcher
    observed_actions: List[str]

    def __new__(cls, obs_lists):
        # change observation here
        action_obs = [list() for _ in obs_lists]
        for id, obs_list in enumerate(obs_lists):
            for idx, obs in enumerate(obs_list):
                action = obs.action
                if action:  # Final step has no action
                    action_obs[id].append((obs.state.fluents, obs.action))
                if idx != 0:
                    post = obs.state.fluents
                    action_obs[id][-1] = (action_obs[id][-1][0], action_obs[id][-1][1], post)
        observations = [Observation() for _ in obs_lists]
        for i in range(len(action_obs)):
            for j in range(len(action_obs[i])):
                comp = action_obs[i][j] # states should be State(name, GroundedPredicate(name, signature, param to value dict (problem)))
                observations[i].add_component(State({f"{i}{j}{k}": set(GroundedPredicate(p.name, str(p), \
                    {f"{par.obj_type}{idx}": par.name for idx, par in enumerate(p.objects)})) for k, p in enumerate(comp[0])}, None), \
                        ActionCall(comp[1].name, [comp[1].obj_params[k].obj_type + " " \
                    + comp[1].obj_params[k].name for k in range(len(comp[1].obj_params))]), State({f"{i}{j}{k}": \
                        set(GroundedPredicate(p.name, str(p), {f"{par.obj_type}{idx}": par.name for idx, par in enumerate(p.objects)}))\
                             for k, p in enumerate(comp[2])}, None)) # check this conversion for set - unknown if correct
        fluents = Observer._get_fluents(obs_lists)
        actions = Observer._get_actions(obs_lists)
        partial_domain = SAM_Observer.create_partial_domain(fluents, actions)
        SAM = SAMLearner(partial_domain)
        return SAM.learn_action_model(observations)

    @staticmethod
    def create_partial_domain(fluents, actions):
        ### TODO: implement with Roni
        pass

    