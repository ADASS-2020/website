from datetime import datetime, timedelta
import hashlib
import re
import subprocess
from unicodedata import normalize
from .constants import project_root, ANSWER_ID_REV, PLENARY_TYPES, ICONS
from typing import Dict, List, Any
from dateutil.parser import parse
from .model import Speaker


def parse_duration(s):
    tokens = [float(t) for t in s.split(':')]
    if len(tokens) == 3:
        # hour, minutes, seconds
        secs = tokens[0] * 3600 + tokens[1] * 60 + tokens[2]
    elif len(tokens) == 2:
        # hour, minutes
        secs = tokens[0] * 3600 + tokens[1] * 60
    else:
        raise NotImplementedError(f'Unsupported duration format {s}')
    return timedelta(seconds=secs)


def compute_endtime(raw_item):
    """
    Return the datetime of the end time for the schedule item. What out for
    events crossing the midnight!
    """
    start = parse(raw_item['date'])
    delta = parse_duration(raw_item['duration'])
    return start + delta


def format_time(dt):
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


def get_domains(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['domains'])


def get_domain_expertise(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['domain_expertise'])


def get_skill(raw_answers):
    return _fetch_answer(raw_answers, ANSWER_ID_REV['skill'])


def get_speakers(raw_persons: List[Dict[str, str]]) -> List[Speaker]:
    """
    Given a persons section of a pretalx schedule JSON object, extract speaker
    names and affiliations and compose two strings of the form

    <public_name> [, <public_name>]*
    <public_name> (<affiliation>)[, <public_name> (<affiliation>)]*

    and return both, in that order.
    """
    spkrs = []
    answer_id = ANSWER_ID_REV['affiliation']
    for raw_person in raw_persons:
        name = raw_person['public_name']
        affil = _fetch_answer(raw_person['answers'], answer_id)
        spkrs.append(Speaker(name, affil))
    return spkrs


def format_speakers(speakers: List[Speaker]) -> str:
    return ', '.join(s.name for s in speakers)


def format_speakers_affiliations(speakers: List[Speaker]) -> str:
    strs = []
    for speaker in speakers:
        if speaker.affiliation:
            strs.append(f'{speaker.name} ({speaker.affiliation})')
        else:
            strs.append(f'{speaker.name}')
    return ', '.join(strs)


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


def format_date(dt):
    return dt.strftime('%Y-%m-%d')


def human_format_date(dt):
    if isinstance(dt, datetime) and dt.second == 59:
        dt += timedelta(seconds=1)
    return dt.strftime("%A, %B %d")


def format_duration(dt: timedelta) -> str:
    s = int(round(dt.total_seconds()))
    assert s < 86400, 'Event durations of one day or longer are not supported'

    mm, ss = divmod(s, 60)
    if ss == 59:
        mm += 1
    hh, mm = divmod(mm, 60)
    return f'{hh:02d}:{mm:02d}'


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
