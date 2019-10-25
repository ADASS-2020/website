from .content import update_session_pages, generate_session_pages
from .content import update_schedule_pages
from .utils import git_pull, git_push, run_lekor_update


__all__ = ['process_sessions', 'process_schedule', 'update_website',
           'publish_website']


def process_sessions():
    update_session_pages(use_cache=False)
    update_session_pages(use_cache=True)
    generate_session_pages()


def process_schedule():
    update_schedule_pages()


def update_website():
    git_pull()
    process_schedule()
    process_sessions()
    run_lekor_update()


def publish_website():
    update_website()
    git_push()
    print('Now implemnent rsync to production')
