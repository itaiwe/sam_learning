"""Creates the trajectories that will be used in the trajectory"""
import logging
import shutil
import sys
from pathlib import Path
from typing import NoReturn, List

from pddl_plus_parser.exporters import MetricFFParser, TrajectoryExporter, ENHSPParser
from pddl_plus_parser.lisp_parsers import DomainParser, ProblemParser
from pddl_plus_parser.multi_agent import MultiAgentDomainsConverter, MultiAgentProblemsConverter, PlanConverter, \
    MultiAgentTrajectoryExporter

from utilities import SolverType


class ExperimentTrajectoriesCreator:
    """Class responsible for creating the trajectories that will be used in the experiments."""
    logger: logging.Logger

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_domain_trajectories(self, problems_directory: Path, plans_directory: Path, output_folder: Path,
                                   agent_names: List[str], planner_prefix: str) -> NoReturn:
        """Creates the domain trajectory files."""
        for problem_folder in problems_directory.glob("*"):
            self.logger.info(f"Creating trajectories for {problem_folder.stem}")
            domain_converter = MultiAgentDomainsConverter(working_directory_path=problem_folder)
            problem_converter = MultiAgentProblemsConverter(working_directory_path=problem_folder,
                                                            problem_file_prefix="problem")

            problem_folder_name = problem_folder.stem
            combined_domain_file_name = "combined_domain.pddl"
            domain_file_path = problem_folder / combined_domain_file_name
            domain_converter.export_combined_domain()
            problem_converter.export_combined_problem(combined_domain_path=domain_file_path)
            combined_domain = DomainParser(domain_path=domain_file_path, partial_parsing=False).parse_domain()
            combined_problem = ProblemParser(problem_path=problem_folder / "combined_problem.pddl",
                                             domain=combined_domain).parse_problem()
            plan_converter = PlanConverter(ma_domain=combined_domain)
            plan_folder_path = plans_directory / f"{planner_prefix}_{problem_folder_name}"
            plan_sequence = plan_converter.convert_plan(plan_file_path=plan_folder_path / "Plan.txt",
                                                        agent_names=agent_names)
            combined_plan_path = problem_folder / f"{problem_folder_name}.solution"
            plan_converter.export_plan(plan_file_path=combined_plan_path, plan_actions=plan_sequence)
            trajectory_exporter = MultiAgentTrajectoryExporter(combined_domain)
            triplets = trajectory_exporter.parse_plan(problem=combined_problem, plan_path=combined_plan_path)
            trajectory_exporter.export_to_file(triplets, problem_folder / f"{problem_folder_name}.trajectory")
            self._copy_domain_files(problem_folder, output_folder)

    def _copy_domain_files(self, problem_folder: Path, output_folder: Path) -> NoReturn:
        """

        :param problem_folder:
        :param output_folder:
        :return:
        """
        self.logger.info("Copying domain related files...")
        combined_domain_file_name = "combined_domain.pddl"
        combined_problem_file_name = "combined_problem.pddl"
        problem_folder_name = problem_folder.stem
        domain_file_path = problem_folder / combined_domain_file_name
        combined_plan_path = problem_folder / f"{problem_folder_name}.solution"
        shutil.copy(domain_file_path, output_folder)
        shutil.copy(problem_folder / combined_problem_file_name, output_folder / f"{problem_folder_name}.pddl")
        shutil.copy(combined_plan_path, output_folder)
        shutil.copy(problem_folder / f"{problem_folder_name}.trajectory", output_folder)
