from datetime import timedelta
import hashlib
import re
import subprocess
from unicodedata import normalize
from .constants import project_root, ANSWER_ID_REV, PLENARY_TYPES, ICONS
from typing import Dict, List, Tuple, Any
from dateutil.parser import parse


def compute_endtime(raw_item):
    """
    Return the datetime of the end time for the schedule item. What out for
    events crossing the midnight!
    """
    start = parse(raw_item['date'])
    delta = raw_item['duration']

    tokens = [float(t) for t in delta.split(':')]
    if len(tokens) == 3:
        # hour, minutes, seconds
        s = tokens[0] * 3600 + tokens[1] * 60 + tokens[2]
    elif len(tokens) == 2:
        # hour, minutes
        s = tokens[0] * 3600 + tokens[1] * 60
    else:
        raise NotImplementedError(f'Unsupported duration format {delta}')

    delta = timedelta(seconds=s)
    return start + delta


def format_endtime(dt):
    # TODO: Handle the case of talks ending after midnight!
    return dt.strftime('%H:%M')


def format_icon(raw_item):
    """
    This should be customised to your needs. Return the most appropriate icon
    name (usually from fa), if any, for the given schedule item.
    """
    return ICONS.get(raw_item['type'], '')


def is_plenary(raw_item: Dict[str, Any]) -> bool:
    """
    This should be customised to your needs: what makes a talk plenary? Maybe
    a given track, maybe a talk type. You decide.

    Return True/False
    """
    return raw_item['type'] in PLENARY_TYPES


def _fetch_answer(raw_answers, _id):
    for raw_answer in raw_answers:
        if raw_answer['question'] == _id:
            return raw_answer['answer']
    return


def format_domains(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['domains'])


def format_domain_expertise(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['domain_expertise'])


def format_skill(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['skill'])


def format_speakers(raw_persons: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Given a persons section of a pretalx schedule JSON object, extract speaker
    names and affiliations and compose two strings of the form

    <public_name> [, <public_name>]*
    <public_name> (<affiliation>)[, <public_name> (<affiliation>)]*

    and return both, in that order.
    """
    spkrs = []
    spkrs_affil = []
    answer_id = ANSWER_ID_REV['affiliation']
    for raw_person in raw_persons:
        name = raw_person['public_name']
        affil = _fetch_answer(raw_person['answers'], answer_id)

        spkrs.append(name)
        if affil:
            spkrs_affil.append(f'{name} ({affil})')
        else:
            spkrs_affil.append(name)
    return ', '.join(spkrs), ', '.join(spkrs_affil)


def slugify(text, delim="-"):
    """Generates an slightly worse ASCII-only slug."""

    _punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    _regex = re.compile("[^a-z0-9]")
    # First parameter is the replacement, second parameter is your input string

    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize("NFKD", word).encode("ascii", "ignore")
        word = word.decode("ascii")
        word = _regex.sub("", word)
        if word:
            result.append(word)
    return str(delim.join(result))


def date2identifier(dt):
    if dt.second == 59:
        dt += timedelta(seconds=1)
    return dt.strftime("%a-%H:%M").lower()


def human_format_date(dt):
    return dt.strftime('%A, %B %d')


def format_date(dt):
    if dt.second == 59:
        dt += timedelta(seconds=1)
    return dt.strftime("%A %H:%M").lower()


def gen_gravatar(email):
    h = hashlib.md5(email.encode("utf-8")).hexdigest()
    return "https://www.gravatar.com/avatar/{}".format(h)


def git_push():
    commands = [
        f"cd {project_root.absolute()}",
        "git add --all",
        "git commit -am website-auto-update",
        "git push"
    ]
    for command in commands:
        print("command:", command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        proc_stdout, proc_error = process.communicate()
        if proc_error:
            raise RuntimeError(
                f"git did return an error {proc_error}: {proc_stdout}"
            )
        for line in proc_stdout.decode('utf-8').split('\n'):
            print(line)


def git_pull():
    commands = [f"cd {project_root.absolute()}", "git pull"]
    for command in commands:
        print("command:", command)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        proc_stdout, proc_error = process.communicate()
        if proc_error:
            raise RuntimeError(
                f"git did return an error {proc_error}: {proc_stdout}"
            )
        for line in proc_stdout.decode('utf-8').split('\n'):
            print(line)


def run_lekor_update():
    command = f"cd {project_root.absolute()}/website && " + \
        "lektor build --output-path ../www"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    for line in proc_stdout.decode('utf-8').split('\n'):
        print(line)
