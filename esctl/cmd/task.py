import datetime

from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter


class TaskList(EsctlLister):
    """Returns a list of tasks."""

    def take_action(self, parsed_args):
        tasks = self.transform(
            self.es.tasks.list(
                actions=parsed_args.actions,
                detailed=parsed_args.detailed,
                parent_task_id=parsed_args.parent_task_id,
            ).get("nodes")
        )

        return JSONToCliffFormatter(tasks).format_for_lister(
            columns=[
                ("name"),
                ("node"),
                ("id"),
                ("type"),
                ("action"),
                ("start_time_human_readable"),
                ("running_time_in_nanos"),
                ("parent_task_id"),
                ("cancellable"),
                ("headers"),
            ]
        )

    def convert_timestamp_in_ms_to_human_readable(self, time_in_ms: int) -> str:
        miliseconds = str(round((time_in_ms / 1000) % 1, 3)).split(".")[1]
        return (
            datetime.datetime.utcfromtimestamp(time_in_ms / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            + f".{miliseconds}"
        )

    def transform(self, nodes):
        tasks = []

        for _, node_definition in nodes.items():
            for task_name, task in node_definition.get("tasks").items():
                task["name"] = task_name

                if "parent_task_id" not in task:
                    task["parent_task_id"] = ""

                task[
                    "start_time_human_readable"
                ] = self.convert_timestamp_in_ms_to_human_readable(
                    task.get("start_time_in_millis")
                )

                tasks.append(task)

        return tasks

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--actions",
            help="A comma-separated list of actions that should be returned",
        )
        parser.add_argument(
            "--detailed",
            help="Return detailed task information (default: false)",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--parent_task_id",
            help="Return tasks with specified parent task id (node_id:task_number)",
        )

        return parser
