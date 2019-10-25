from pathlib import Path


DEFAULT_TRACK = 'Plenary'
DEFAULT_SKILL = 'Beginner'
project_root = Path(__file__).resolve().parents[1]
tokenpath = project_root / '_private/TOKEN.txt'
TOKEN = tokenpath.open().read().strip()

base_url = 'https://pretalx.adass2020.es'
event = 'adass2020'
headers = {'Accept': 'application/json, text/javascript',
           'Authorization': f'Token {TOKEN}'}

submissions_path = project_root / Path('_private/submissions.json')
speakers_path = project_root / Path('_private/speakers.json')
clean_submissions_f = project_root / Path("website/databags/submissions.json")
schedule_path = project_root / Path("website/databags/schedule_databag.json")

ANSWER_ID = {
    1: 'skill',
    2: 'domain_expertise',
    3: 'domains',
    4: 'short_description',
    5: 'affiliation',
    6: 'position',
    7: 'homepage',
    8: '@twitter',
    9: 'residence',
    10: 'github',
}
ANSWER_ID_REV = {v: k for k, v in ANSWER_ID.items()}
PLENARY_TYPES = (
    'Keynote',
    'Lightning Talk',
    'Talk (15 minutes)',
    'Talk (30 minutes)',
    'Opening / Closing Remarks'
)
ICONS = {
    'Coffee Break': 'fa-coffee',
    'Lunch': 'fa-cutlery',
    'Registration': 'fa-ticket',
    'Opening / Closing Remarks': 'fa-rocket',
    'BoF (90 minutes)': 'fa-users',
    'BoF (60 minutes)': 'fa-users',
    'BoF': 'fa-users',
    'Social Event': 'fa-users',
}
