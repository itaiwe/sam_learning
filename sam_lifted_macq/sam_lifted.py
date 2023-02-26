"""The Safe Action Model Learning algorithm module."""
import os,sys
sys.path.append("./")
import logging
from collections import defaultdict, OrderedDict
from itertools import combinations
from typing import List, Tuple, Dict, Set

from pddl_plus_parser.models import Observation, Predicate, ActionCall, State, Domain, ObservedComponent, PDDLObject, GroundedPredicate, PDDLType

# sys.path.append(os.path.abspath('../../sam_helper'))

from .sam_helper import PredicatesMatcher, extract_effects, LearnerDomain, contains_duplicates, VocabularyCreator, \
    LearnerAction

from .sam_model import SAMLearner

from .observer import Observer

from . import Model, LearnedAction, LearnedFluent

import subprocess as sub

class SAM_Observer:
    """Class that represents the safe action model learner algorithm.

    Notice: This class does not support domains with constants or with the same object mapped to multiple parameters.
    """

    logger: logging.Logger
    partial_domain: LearnerDomain
    matcher: PredicatesMatcher
    observed_actions: List[str]


    @staticmethod
    def _extract_sam_predicate(pred, type_name_to_obj):
        """Extract SAM predicate if name of predicate not seen yet

        Args:
            pred (Fluent): predicate given in the observation list that we want to scan
            type_name_to_obj (dict): dictionary from name of type to the object

        Returns:
            Predicate: SAM's pddl+ predicate to add to predicate_name_to_obj dictionary
        """
        predicate_name = pred.name
        predicate_signature = OrderedDict()
        for predicate_param in pred.objects:
            if predicate_param.obj_type not in type_name_to_obj:
                type_name_to_obj[predicate_param.obj_type] = PDDLType(predicate_param.obj_type)
            param_type = type_name_to_obj[predicate_param.obj_type]
            predicate_signature[f'?{predicate_param.name}'] = param_type
        return Predicate(predicate_name,signature=predicate_signature)

    @staticmethod
    def _extract_sam_action(macq_comp, type_name_to_obj):
        """Extract SAM action if name not seen yet

        Args:
            macq_comp (Action): Macq action given from parsing
            type_name_to_obj (dict): dictionary from name of type to the object

        Returns:
            LearnerAction: SAM's pddl+ action to add to action_name_to_obj dictionary
        """
        action_name = macq_comp.name
        action_signature = OrderedDict()
        for action_param in macq_comp.obj_params:
            if action_param.obj_type not in type_name_to_obj:
                type_name_to_obj[action_param.obj_type] = PDDLType(action_param.obj_type)
            param_type = type_name_to_obj[action_param.obj_type]
            action_signature[f'?{action_param.name}'] = param_type
        return LearnerAction(action_name,signature=action_signature)
        
    def __new__(cls, obs_lists, debug: bool):
        """Creating main entrypoint for SAM through MACQ

        Args:
            obs_lists (List of ObservationList): observations received from macq.
            debug (bool): Not used in algorithm yet.
        """
        # change observation here
        action_obs = [list() for _ in obs_lists]
        for id, obs_list in enumerate(obs_lists):
            for idx, obs in enumerate(obs_list):
                action = obs.action
                if idx != 0:
                    post = obs.state.fluents
                    action_obs[id][-1] = (action_obs[id][-1][0], action_obs[id][-1][1], post)
                if action:  # Final step has no action
                    action_obs[id].append((obs.state.fluents, obs.action))

       
        action_name_to_obj = {} # map name of a lifted action to an ActionLearner obj
        type_name_to_obj = {} # map name of a lifted type to an ActionLearner obj
        predicate_name_to_obj = OrderedDict() # map name of a lifted fluent to an ActionLearner obj


        observations = [Observation() for _ in obs_lists]
        for i in range(len(action_obs)):
            for j in range(len(action_obs[i])):
                comp = action_obs[i][j] # states should be State(name, GroundedPredicate(name, signature, param to value dict))
                comp = (OrderedDict(comp[0]), comp[1], OrderedDict(comp[2]))
                

                # Get lifted predicated obj - pre state
                for p in comp[0].keys():
                    predicate_name = p.name
                    if predicate_name not in predicate_name_to_obj:
                        predicate_name_to_obj[predicate_name] = SAM_Observer._extract_sam_predicate(p, type_name_to_obj)
                
                # Get lifted action obj
                action_name = comp[1].name
                if action_name not in action_name_to_obj:
                    action_name_to_obj[action_name] = SAM_Observer._extract_sam_action(comp[1], type_name_to_obj)

                # Get lifted predicated obj - post state
                for p in comp[2].keys():
                    predicate_name = p.name
                    if predicate_name not in predicate_name_to_obj:
                        predicate_name_to_obj[predicate_name] = SAM_Observer._extract_sam_predicate(p, type_name_to_obj)

                comp0sig = [OrderedDict() for _ in comp[0]]
                for idx, p in enumerate(comp[0]):
                    params = predicate_name_to_obj[p.name].signature
                    for index in params:
                        comp0sig[idx][index] = params[index]
                
                comp2sig = [OrderedDict() for _ in comp[2]]
                for idx, p in enumerate(comp[2]):
                    params = predicate_name_to_obj[p.name].signature
                    for index in params:
                        comp0sig[idx][index] = params[index]


#state: lifted name: set(groundedpredicates)
                indices, predicates = {}, {}
                state, mapping, val = {}, {}, []
                for k, p in enumerate(list(comp[0].keys())):
                    if p.name not in predicates:
                        predicates[p.name] = []; predicates[p.name].append((k, p))
                    else:
                        predicates[p.name].append((k, p))
                for l_p in predicates:
                    for k, p in predicates[l_p]:
                        new_p = p
                        if comp[0][p]:
                            for par in p.objects:
                                index = list(predicate_name_to_obj[new_p.name].signature.values()).index(PDDLType(par.obj_type), \
                                    indices[new_p.name][-1] + 1 if new_p.name in indices else 0)
                                if new_p.name not in indices:
                                    indices[new_p.name] = []; indices[new_p.name].append(index)
                                else:
                                    indices[new_p.name].append(index)
                                key = list(predicate_name_to_obj[new_p.name].signature.keys())[index]
                                mapping[key] = par.name
                            val.append(GroundedPredicate(new_p.name, comp0sig[k], mapping))
                        indices = {}
                        mapping = {}
                    state[f'{l_p}'] = set(val)
                    val = []
                prev_state = State(state, {})
                act = ActionCall(comp[1].name, [comp[1].obj_params[k].name for k in range(len(comp[1].obj_params))])
                
                indices, predicates = {}, {}
                state, mapping, val = {}, {}, []
                for k, p in enumerate(list(comp[2].keys())):
                    if p.name not in predicates:
                        predicates[p.name] = []; predicates[p.name].append((k, p))
                    else:
                        predicates[p.name].append((k, p))
                for l_p in predicates:
                    for k, p in predicates[l_p]:
                        new_p = p
                        if comp[2][p]:
                            for par in p.objects:
                                index = list(predicate_name_to_obj[new_p.name].signature.values()).index(PDDLType(par.obj_type), \
                                    indices[new_p.name][-1] + 1 if new_p.name in indices else 0)
                                if new_p.name not in indices:
                                    indices[new_p.name] = []; indices[new_p.name].append(index)
                                else:
                                    indices[new_p.name].append(index)
                                key = list(predicate_name_to_obj[new_p.name].signature.keys())[index]
                                mapping[key] = par.name
                            val.append(GroundedPredicate(new_p.name, comp2sig[k], mapping))
                        indices = {}
                        mapping = {}
                    state[f'{l_p}'] = set(val)
                    val = []
                post_state = State(state, {})
                observations[i].add_component(prev_state, act, post_state)
                # print(prev_state.state_predicates, act, post_state.state_predicates)
#lifted: grounded in object mapping
        partial_domain = SAM_Observer.create_partial_domain(type_name_to_obj, predicate_name_to_obj, action_name_to_obj)
        print(str(partial_domain))
        SAM = SAMLearner(partial_domain)
        # for com in observations[0].components:
        #     print(str(com))
        return SAM.learn_action_model(observations)

    @staticmethod
    def create_partial_domain(name_to_type, name_to_predicate, name_to_action):
        # create partial domain here
        d = Domain()
        d.name = "new_domain"
        d.requirements = [":typing"]

        #  Get name_to_type (PddlType)
        d.types = name_to_type
        #  Get name_to_predicate (Predicate)
        d.predicates = name_to_predicate
        #  Get name_to_action (LearnerAction)
        d.actions = name_to_action
        return d

    