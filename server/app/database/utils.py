"""
Author: Nick Yu
Date created: 23/7/2019
"""
import click
import os
from typing import List, Optional
from flask.cli import AppGroup

from app.database.models import db

db_cli = AppGroup('db')


def get_model(name: str) -> Optional[db.Model]:
    """
    Get Model if it exists

    :param name: name of the table to find
    :return: Type object of db.Model
    """
    name = name.lower()

    if name in db.metadata.tables:
        gen = (v for k, v in db.Model._decl_class_registry.items() if k.lower() == name)
        return next(gen, None)

    return None


@db_cli.command('reset')
@click.option('-f', '--force', is_flag=True)
def reset(force):
    """Setup data persistence"""
    database_name = os.environ.get('DB_NAME')
    data_path = os.environ.get('DATA_FOLDER', default='./data')

    if not database_name:
        print('DB_NAME is not defined in environment, defaulting to \'db.sqlite\'')
        database_name = 'db.sqlite'

    path = os.path.realpath(os.path.join(data_path, database_name))

    already_exists = os.path.exists(path)

    if already_exists and force:
        db.drop_all()
        db.create_all()
        print('Reset tables')
    elif already_exists:
        while True:
            inp = input(f'{path} already exists, reset tables? (y/n) ').lower()

            if inp in ('y', 'n'):
                break

        if inp == 'y':
            db.drop_all()
            db.create_all()
            print('Reset tables')
    else:
        try:
            # ignore FileExistsError
            os.mkdir('data')
        except FileExistsError:
            pass

        db.create_all()
        print('Created tables')


@db_cli.command('remove')
@click.confirmation_option(prompt='Are you sure you want to remove the db?')
def remove():
    """Removes database entirely"""
    database_name = os.environ.get('DB_NAME')
    data_path = os.environ.get('DATA_FOLDER', default='./data')

    if not database_name:
        print('DB_NAME is not defined in environment, cancelling')
        return

    path = os.path.realpath(os.path.join(data_path, database_name))

    os.remove(path)
    print('Removed')


@db_cli.command('view')
@click.argument('table')
def view(table: str):
    """
    Prints given objects in 'table'

    :param table: name of the table to view
    """
    cls: db.Model = get_model(table)

    if cls:
        for item in cls.query.limit(5):
            print(item)
    else:
        print(f'{table} does not exist')


@db_cli.command('insert')
@click.argument('table')
@click.argument('args', nargs=-1)
def insert(table: str, args: List[str]):
    """
    Inserts given object into table

    Horribly hacky code!, should only ever be allowed for testing
    :param table: which table to insert to
    :param args: arguments, should be formatted as "<KEY>=<VAL>"
    """
    cls: db.Model = get_model(table)

    if cls:
        kwargs = {k: eval(v) for k, v in [tuple(a.split('=')) for a in args]}
        obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
    else:
        print(f'{table} does not exist')
