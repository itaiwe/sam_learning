"""Module test for the vocabulary_creator module."""
from pddl_plus_parser.lisp_parsers import DomainParser, ProblemParser
from pddl_plus_parser.models import Domain, Problem
from pytest import fixture

from sam_learning.core import VocabularyCreator
from tests.consts import WOODWORKING_DOMAIN_PATH, ELEVATORS_DOMAIN_PATH, ELEVATORS_PROBLEM_PATH, \
    WOODWORKING_PROBLEM_PATH


@fixture()
def vocabulary_creator() -> VocabularyCreator:
    return VocabularyCreator()


@fixture()
def elevators_domain() -> Domain:
    domain_parser = DomainParser(ELEVATORS_DOMAIN_PATH, partial_parsing=True)
    return domain_parser.parse_domain()


@fixture()
def elevators_problem(elevators_domain: Domain) -> Problem:
    return ProblemParser(problem_path=ELEVATORS_PROBLEM_PATH, domain=elevators_domain).parse_problem()


@fixture()
def woodworking_domain() -> Domain:
    return DomainParser(WOODWORKING_DOMAIN_PATH, partial_parsing=True).parse_domain()


@fixture()
def woodworking_problem(woodworking_domain: Domain) -> Problem:
    return ProblemParser(problem_path=WOODWORKING_PROBLEM_PATH, domain=woodworking_domain).parse_problem()


def test_create_vocabulary_creates_grounded_predicates_only_for_those_with_matching_types(
        elevators_domain: Domain, vocabulary_creator: VocabularyCreator, elevators_problem: Problem):
    vocabulary_predicates = vocabulary_creator.create_vocabulary(
        domain=elevators_domain,
        observed_objects={"n1": elevators_problem.objects["n1"], "n2": elevators_problem.objects["n2"]})
    assert list(vocabulary_predicates.keys()) == ['(above ?floor1 ?floor2)', '(next ?n1 ?n2)']


def test_create_vocabulary_creates_grounded_predicates_when_given_two_types_of_objects(
        elevators_domain: Domain, vocabulary_creator: VocabularyCreator, elevators_problem: Problem):
    vocabulary_predicates = vocabulary_creator.create_vocabulary(
        domain=elevators_domain,
        observed_objects={"p0": elevators_problem.objects["p0"], "slow0-0": elevators_problem.objects["slow0-0"]})
    assert list(vocabulary_predicates.keys()) == ['(boarded ?person ?lift)']


def test_create_vocabulary_creates_grounded_predicates_when_constants_and_objects(
        woodworking_domain: Domain, vocabulary_creator: VocabularyCreator, woodworking_problem: Problem):
    vocabulary_predicates = vocabulary_creator.create_vocabulary(
        domain=woodworking_domain,
        observed_objects={"b0": woodworking_problem.objects["b0"],
                          "verysmooth": woodworking_domain.constants["verysmooth"],
                          "grinder0": woodworking_problem.objects["grinder0"]})
    assert set(vocabulary_predicates.keys()) == {'(surface-condition ?obj ?surface)', '(available ?obj)',
                                                 '(is-smooth ?surface)', '(has-colour ?agent ?colour)',
                                                 '(grind-treatment-change ?agent ?old ?new)'}
