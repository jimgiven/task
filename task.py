from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from pydantic import BaseModel
from rich import print as rprint


class Task(BaseModel):
    id: int
    title: str


class Project(BaseModel):
    name: str
    next_id: int = 0
    tasks: dict[int, Task] = {}

    @staticmethod
    def read() -> Project:
        return Project.parse_file(Path("tasks.json"))

    def write(self: Project):
        with open("tasks.json", "w") as fh:
            fh.write(self.json())

    @property
    def task_iter(self):
        return sorted([task for task in self.tasks.values()], key=lambda task: task.id)


@click.group()
def cli():
    pass


@click.group("project")
def project():
    pass


@click.group("task")
def task():
    pass


@project.command("init")
@click.argument("project_name")
def init(project_name: str):
    project = Project(name=project_name)
    project.write()


@project.command("info")
def info():
    project = Project.read()
    rprint(f"[bold blue]Project: {project.name}[/bold blue]")


@project.command("migrate")
def migrate():
    Project.read().write()


@task.command("add")
@click.option("--title", "title", prompt="Title")
def add(title: str):
    project = Project.read()

    project.next_id += 1
    task = Task(id=project.next_id, title=title)

    assert project.tasks.get(task.id) is None, "Oops, something went wrong!"

    project.tasks[task.id] = task
    project.write()


cli.add_command(project)
cli.add_command(task)


if __name__ == "__main__":
    cli()
