from __future__ import annotations
from pathlib import Path
import click
from rich import print as rprint
from pydantic import BaseModel

class Task(BaseModel):
    id: int
    title: str

class Project(BaseModel):
    name: str
    next_id: int = 0

    @staticmethod
    def read() -> Project:
        return Project.parse_file(Path('tasks.json'))

    def write(self: Project):
        with open('tasks.json', 'w') as fh:
            fh.write(self.json())

@click.group()
def cli():
    pass

@click.group("project")
def project():
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

@click.group("task")
def task():
    pass


cli.add_command(project)
cli.add_command(task)


if __name__ == "__main__":
    cli()