from __future__ import annotations

import enum
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

import click
import parse
from git.repo import Repo
from pydantic import BaseModel
from rich import print as rprint

repo = Repo()


BRANCH_FORMAT_STRING = "{project_abbv}-{task_id:d}/{task_title}"


def _checkout_branch(branch_name: str):
    branch = repo.create_head(branch_name)
    branch.checkout()


@enum.unique
class TaskStatus(enum.Enum):
    INCOMPLETE = "incomplete"
    STARTED = "started"
    COMPLETE = "complete"


class Task(BaseModel):
    id: int
    title: str
    status: TaskStatus = TaskStatus.INCOMPLETE


class Project(BaseModel):
    name: str
    project_abbv: str
    next_id: int = 0
    tasks: dict[int, Task] = {}

    @staticmethod
    def read() -> Project:
        return Project.parse_file(Path("tasks.json"))

    def write(self: Project):
        with open("tasks.json", "w") as fh:
            fh.write(self.json())

    @property
    def task_iter(self) -> list[Task]:
        return sorted([task for task in self.tasks.values()], key=lambda task: task.id)

    def get_task(self, task_id: int) -> Task:
        task = self.tasks.get(task_id)

        if task is None:
            raise ValueError(f"{task_id} is not a valid ID.")

        return task


@contextmanager
def project_context(read_only: bool = False) -> Generator[Project, None, None]:
    project = Project.read()
    yield project

    if not read_only:
        project.write()


@click.group()
def cli():
    pass


@click.group("project")
def project():
    pass


@click.group("task")
def task():
    pass


@cli.command("scratch")
def scratch():
    pass


@project.command("init")
@click.argument("project_name")
def init(project_name: str):
    project = Project(name=project_name)
    project.write()


@project.command("info")
def info():
    with project_context(read_only=True) as project:
        rprint(f"[bold green]Project: {project.name}[/bold green]")
        for task in project.task_iter:
            symbol = {
                TaskStatus.COMPLETE: "✅",
                TaskStatus.INCOMPLETE: "⭕",
                TaskStatus.STARTED: "⏩",
            }.get(task.status)
            rprint(f"  {symbol} [bold blue]{task.id}: {task.title}[/bold blue]")


@project.command("migrate")
def migrate():
    with project_context() as project:
        pass


@task.command("add")
@click.option("--title", "title", prompt="Title")
def add(title: str):
    with project_context() as project:
        project.next_id += 1
        task = Task(id=project.next_id, title=title)

        assert project.tasks.get(task.id) is None, "Oops, something went wrong!"

        project.tasks[task.id] = task


@task.command("start")
@click.argument("task_id", type=int)
def complete(task_id: int):
    with project_context() as project:
        task = project.get_task(task_id)

        task.status = TaskStatus.STARTED

        branch_name = BRANCH_FORMAT_STRING.format(
            project_abbv=project.project_abbv,
            task_id=task.id,
            task_title=task.title.lower().replace(" ", "-"),
        )
        _checkout_branch(branch_name)


@task.command("complete")
@click.option("--task", "-t", "task_id", type=int)
@click.option("--branch", "-b", "branch", type=str)
def complete(task_id: Optional[int], branch: Optional[str]):
    if branch is not None and task_id is not None:
        raise ValueError(
            "Cannot provide --task [bold]and[/bold] --branch in the same command."
        )

    if branch is None and task_id is None:
        raise ValueError("Must provide at least --task [bold]or[/bold] --branch.")

    if branch:
        print(branch)
        task_id = parse.parse(BRANCH_FORMAT_STRING, branch)["task_id"]

    with project_context() as project:
        task = project.get_task(task_id)

        task.status = TaskStatus.COMPLETE

        rprint(f"[bold green]{task.title} - Complete[/bold green]")


cli.add_command(project)
cli.add_command(task)


if __name__ == "__main__":
    cli()
