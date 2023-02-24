from macq import generate, extract
from macq.observation import IdentityObservation
import subprocess as sub

traces = generate.pddl.VanillaSampling(problem_id=379, plan_len=20, num_traces=1).traces
observations = traces.tokenize(IdentityObservation)
model = extract.Extract(observations, extract.modes.SAM)
# print(type(list(observations[0][0].state.fluents.keys())[0]))
print(model.details())
# model.to_pddl('sokoban', 'p16', 'sok.pddl', 'p1.pddl')
# import requests
# from macq.generate.pddl.planning_domains_api import get_problem, get_plan
# dom = requests.get(get_problem(123)["domain_url"]).text
# prob = requests.get(get_problem(123)["problem_url"]).text
# sub.Popen(['cat', '{dom}', '>', 'domain.pddl'])
# print(dom)
# print("___________________________")
# print(prob)