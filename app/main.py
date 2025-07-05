import click

from app.impl import CrawlingImpl, ToDBImpl

from .appcontext import AppContext

pass_repo = click.make_pass_decorator(AppContext)


@click.group()
@click.option("--debug", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    app = AppContext(debug)
    app.implementations(
        CrawlingImpl(app),
        ToDBImpl(app),
    )
    ctx.obj = app


main = cli


@cli.command()
@pass_repo
def crawling(app: AppContext):
    app.usecases["crawling"].invoke()


@cli.command()
@pass_repo
def todb(app: AppContext):
    app.usecases["todb"].invoke()
