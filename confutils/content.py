import json
import codecs
from dateutil.parser import parse
import shutil
from pathlib import Path
import pandas as pd
import requests
from .constants import base_url, event, DEFAULT_TRACK, submissions_path
from .constants import speakers_path, clean_submissions_f, schedule_path
from .constants import project_root, DEFAULT_SKILL, ANSWER_ID, headers
from .pretalx import get_all_data_from_pretalx
from . import utils


def update_schedule_pages():
    """Update the three schedule databags: room, time and table."""

    # Fetch the schedule from pretalx in JSON format.
    raw_schedule = requests.get(
        f'{base_url}/{event}/schedule/export/schedule.json',
        headers=headers
    ).json()

    # Get all rooms
    # rooms = load_rooms()

    base_schedule = {'dates': []}
    for raw_day in raw_schedule['schedule']['conference']['days']:
        raw_day['date'] = parse(raw_day['date'])

        day_schedule = {}
        day_schedule['day'] = utils.human_format_date(raw_day['date'])
        day_schedule['datum'] = raw_day['date'].date().isoformat()
        day_schedule['rooms'] = []

        for room_name, raw_list in raw_day['rooms'].items():
            room_schedule = {
                'room_name': room_name,
                'location': 'center',
                'use': 'talks/keynotes',
                'data_tab': f'{day_schedule["datum"]}-{room_name}',
                'sessions': []
            }
            for raw_item in raw_list:
                spkrs, spkrs_affil = utils.format_speakers(raw_item['persons'])
                slug = utils.slugify(
                    f"{raw_item['track']}-" +
                    f"{raw_item['slug']}-" +
                    f"{raw_item['title']}-" +
                    f"{spkrs}"
                )
                answers = raw_item['answers']
                raw_item['end'] = utils.compute_endtime(raw_item)

                item = {
                    'code': raw_item['slug'],
                    'name': '',
                    'track': raw_item['track'],
                    'duration': raw_item['duration'],
                    'description': raw_item['description'],
                    'short_description': raw_item['abstract'],
                    'skill': utils.format_skill(answers),
                    'domain_expertise': utils.format_domain_expertise(answers),
                    'domains': utils.format_domains(answers),
                    'slug': slug,
                    'title': raw_item['title'],
                    'speaker_names': spkrs_affil,
                    'type': raw_item['type'],
                    'url': f'/program/{slug}',
                    'plenary': utils.is_plenary(raw_item),
                    'add_to_class': '',
                    'clipcard_icon': utils.format_icon(raw_item),
                    'time': raw_item['start'],
                    'start': raw_item['start'],
                    'end': utils.format_endtime(raw_item['end']),
                }
                room_schedule['sessions'].append(item)
            day_schedule['rooms'].append(room_schedule)
        base_schedule['dates'].append(day_schedule)

    print(f'Updating {str(schedule_path)}... ', end='')
    with schedule_path.open('w') as f:
        json.dump(base_schedule, f, indent=4)
    print('DONE')


def load_rooms():
    url = f'{base_url}/api/events/{event}/rooms/'
    return get_all_data_from_pretalx(url)


def load_submissions(accepted_only=True):
    url = f'{base_url}/api/events/{event}/submissions/'
    if not accepted_only:
        submissions = get_all_data_from_pretalx(url)
    else:
        submissions = get_all_data_from_pretalx(
            url,
            params={'state': 'accepted'}
        )
        submissions.extend(
            get_all_data_from_pretalx(url, params={'state': 'confirmed'})
        )
    # add custom data
    for submission in submissions:
        spkrs = ' '.join([x.get('name') for x in submission['speakers']])
        track = submission.get('track', {})
        if not track or 'en' not in track:
            submission['track'] = {'en': DEFAULT_TRACK}
        slug = utils.slugify(
            f"{submission['track']['en']}-" +
            f"{submission['code']}-{submission['title']}-{spkrs}"
        )
        submission['slug'] = slug

    print(f'Updating {str(submissions_path)}... ', end='')
    with submissions_path.open('w') as f:
        json.dump(submissions, f, indent=4)
    print('DONE')


def load_speakers():
    url = f'{base_url}/api/events/{event}/speakers'
    speakers = get_all_data_from_pretalx(url)

    the_speakers = []
    for s in speakers:
        speaker = {k: s[k] for k in ['name', 'biography', 'email', 'code']}
        for qa in s['answers']:
            _id = qa.get('question', {}).get('id')
            if _id not in ANSWER_ID:
                continue
            speaker[ANSWER_ID[_id]] = qa.get('answer')
            # normalize twitter
            if ANSWER_ID[_id] == '@twitter':
                speaker['twitter'] = ""
                handle = qa.get('answer').split('/')[-1].replace('@', '')
                handle = handle.strip()
                speaker[ANSWER_ID[_id]] = handle
                if handle:
                    speaker['twitter'] = \
                        f"https://twitter.com/{speaker[ANSWER_ID[_id]]}"
                else:
                    pass
            if ANSWER_ID[_id] == 'github':
                if qa.get('answer').strip() and \
                        'github.com' not in qa.get('answer', ""):
                    speaker['github'] = \
                        f"https://github.com/{qa.get('answer').strip()}"
            if ANSWER_ID[_id] == 'homepage':
                if qa.get('answer').strip() and \
                        'http' not in qa.get('answer', ""):
                    speaker['homepage'] = f"http://{qa.get('answer').strip()}"

        the_speakers.append(speaker)

    print(f'Updating {str(speakers_path)}... ', end='')
    with speakers_path.open('w') as f:
        json.dump(the_speakers, f, indent=4)
    print('DONE')


def load_schedule():
    the_schedule = {}
    if not schedule_path.exists():
        return
    schedule = json.load(schedule_path.open())
    for d in schedule['dates']:
        for r in d['rooms']:
            for s in r['sessions']:
                if s.get('code'):
                    the_schedule[s['code']] = {
                        'time': d['day'].split(',')[0].lower() + "-" +
                        s['time'],
                        'day': d['day'].split(',')[0].lower(),
                        'room': r['room_name'],
                        'start_time': s['time']
                    }
    return the_schedule


def update_session_pages(use_cache=False):
    """
    Refactored for 2019 setup
    - mangle submission data from API
    - make avaibale in databags
    """
    if not use_cache:
        load_submissions()
        load_speakers()
    submissions = json.load(submissions_path.open())
    speakers = json.load(speakers_path.open())
    speakers = {s['code']: s for s in speakers}
    # TODO: add custom sessions as Open Space
    # take on only required attributes

    eq_attr = ['abstract', 'answers', 'code', 'description', 'duration',
               'is_featured', 'speakers', 'state', 'submission_type', 'title',
               'track', 'slug']
    cleaned_submissions = []
    for s in submissions:
        cs = {k: s[k] for k in s if k in eq_attr}
        cs['submission_type'] = cs['submission_type']['en']
        cs['track'] = cs['track']['en']
        cs['submission_type'] = \
            cs['submission_type'].replace('Talk-', 'Talk -')

        for answer in [a for a in cs['answers']
                       if a['question']['id'] in ANSWER_ID]:
            val = answer['answer']
            if answer['id'] == 119:
                val = val.split(', ')
            cs[ANSWER_ID[answer['question']['id']]] = val
        del cs['answers']
        # add speaker info
        enriched_speakers = []
        for x in cs['speakers']:
            take_on = ['affiliation', 'homepage', '@twitter', 'twitter',
                       'github', 'biography']
            _add = {k: speakers[x['code']].get(k, '') for k in take_on}
            x.update(_add)
            enriched_speakers.append(x)
        cs['speakers'] = enriched_speakers
        cleaned_submissions.append(cs)

    print(f'Updating {str(clean_submissions_f)}... ', end='')
    json.dump(cleaned_submissions, clean_submissions_f.open('w'), indent=4)
    print('DONE')


def save_csv_for_banners():
    """
    CSV with banner info only, saved as UTF-16 for useage in Illustrator for
    auto banner generation
    :return:
    """
    cleaned_submissions = json.load(clean_submissions_f.open())
    # save csv for banner generation
    csv = ['code', 'title', 'track', 'speakers', 'affiliation', 'banner_name']
    csv_submissions = []
    for i, c in enumerate(cleaned_submissions, 1):
        record = {_c: c.get(_c, '') for _c in csv}
        record['speakers'] = ', '.join([x.get('name', '')
                                        for x in c['speakers']])
        record['affiliation'] = ', '.join([x.get('affiliation', '')
                                           for x in c['speakers']])
        record['banner_name'] = f'Twitter-{i}.jpg'  # output from Illustrator
        csv_submissions.append(record)
    df = pd.DataFrame(csv_submissions)
    df.to_csv(clean_submissions_f.with_suffix('.csv'), sep='\t',
              encoding='utf-8', index=False)

    print(f'Updating {str(clean_submissions_f.with_suffix(".txt"))}... ',
          end='')
    with codecs.open(
            clean_submissions_f.with_suffix('.txt'), "w", "UTF-16") as f:  #
        f.write('\t'.join(csv) + '\n')
        for line in csv_submissions:
            f.write('\t'.join([line[k] for k in csv]) + '\n')
    print('DONE')


def rename_tmp_banners():
    """
    banners are created in the same order as in the clean_submissions_f.txt
    file
    :return:
    """
    df = pd.read_csv(clean_submissions_f.with_suffix('.txt'), sep='\t',
                     encoding='utf-16')
    for i in range(0, df.shape[0]):
        src = df.iloc[i]['banner_name']
        if i == 0:
            src = src.replace('1', '')
        src = Path('_private/tmp_banners') / Path(src)
        dst = Path('_private/tmp_banners') / \
            Path(df.iloc[i]['code']).with_suffix(src.suffix)
        src.rename(dst)


def generate_session_pages():
    cleaned_submissions = json.load(clean_submissions_f.open())
    # book keeping
    session_path = project_root / 'website/content/program/'
    session_path.mkdir(exist_ok=True)
    in_place_submissions = [x.name for x in session_path.glob('*')
                            if x.name[0] != '.']
    in_place_submissions.remove('contents.lr')  # only dirs
    tpl = """_model: session
---
code: {code}
---
title: {title}
---
description: {short_description}
---
short_description: {short_description}
---
twitter_image: {twitter_image}
---
speakers: {speakers}
---
submission_type: {submission_type}
---
domains: {domains}
---
biography: {biography}
---
affiliation: {affiliation}
---
track: {track}
---
skill: {skill}
---
domain_expertise: {domain_expertise}
---
room: {room}
---
start_time: {start_time}
---
day: {day}
---
meta_title: {meta_title}
---
meta_twitter_title: {meta_twitter_title}
---
categories: {categories_list}
---
slugified_slot_links: {slugified_slot_links}
---
body: {body}

"""
    # collect categories automatically add newly discovered ones
    all_categories = {}
    # simple url with talk code redirecting to full url, used for auto urls
    # from other systems
    redirects = {}

    the_schedule = load_schedule()

    for submission in cleaned_submissions:

        # filter keynotes or other types
        if 'Talk' in submission['submission_type']:
            pass
        elif 'Tutorial' in submission['submission_type']:
            pass
        elif 'Panel' in submission['submission_type']:
            pass
        # published keynotes
        # is_featured = sneak peak must be set in Pretalx
        elif 'Keynote' in submission['submission_type'] and \
             submission['is_featured']:
            pass
        else:
            print(f'skipped: submission {submission["code"]} ' +
                  f'{submission["title"]}')
            continue

        biography = []
        for x in submission['speakers']:
            biography.append(f"#### {x.get('name')}")
            if x.get('affiliation'):
                biography.append(f'Affiliation: {x["affiliation"]}')
            biography.append(f'')
            biography.append(f"{x['biography'] if x['biography'] else ''}")
            social = []
            if x.get('twitter'):
                social.append(f"[Twitter]({x['twitter']})")
            if x.get('github'):
                social.append(f"[Github]({x['github']})")
            if x.get('homepage'):
                social.append(f"[Homepage]({x['homepage']})")
            if social:
                biography.append('visit the speaker at: ' + ' • '.join(social))
        biography = '\n\n'.join(biography)

        speakers = ', '.join([x['name'] for x in submission['speakers']])
        speaker_twitters = ' '.join([x.get('@twitter')
                                     for x in submission['speakers']
                                     if x.get('@twitter')])
        meta_title = f"{submission['title']} {speakers.replace(',', '')} " + \
            "ADASS XXX conference "
        meta_twitter_title = f"{submission['title']} @{speaker_twitters} " + \
            "#adass"

        # easier to handle on website as full text
        skill = f"Skill Level {submission.get('skill', DEFAULT_SKILL)}"
        domain_expertise = "Domain Expertise " + \
            f"{submission.get('domain_expertise', DEFAULT_SKILL)}"

        domains = submission['domains']

        categories = [submission['track'],
                      skill,
                      domain_expertise] + \
            [submission['submission_type'].split(' ')[0]] + domains.split(', ')

        # add date and session start time for navidgation
        slot_links = []
        start_time, room, day = None, None, None
        if submission.get('code') and the_schedule.get(submission.get('code')):
            start_time, room = (
                the_schedule[submission['code']]['start_time'],
                the_schedule[submission['code']]['room']
            )
            day = the_schedule[submission['code']]['day']
            slot_links = [day, the_schedule[submission['code']]['time']]
        categories = categories + slot_links
        slugified_categories = [utils.slugify(x) for x in categories]
        slugified_slot_links = ', '.join([utils.slugify(x)
                                          for x in slot_links])
        categories_list = ', '.join(slugified_categories)
        all_categories.update(
            {utils.slugify(x).replace('---', '-').replace('--', '-'): x
             for x in categories}
        )

        redirects[submission['code']] = submission['slug']
        redir_dirname = session_path / submission['code']
        if submission['code'] in in_place_submissions:
            in_place_submissions.remove(submission['code'])
        create_redirect(redir_dirname, submission['slug'])

        dirname = session_path / submission['slug']
        if dirname.name in in_place_submissions:
            # print("slug hasn't changed")
            in_place_submissions.remove(dirname.name)

        dirname.mkdir(exist_ok=True)

        print(f'Updating {str(dirname / "contents.tr")}... ', end='')
        with open(dirname / "contents.lr", "w") as f:
            f.write(tpl.format(
                title=submission['title'],
                short_description=submission['short_description'],
                short_description_html=submission['short_description'],
                code=submission['code'],
                body=submission['description'],
                domains=domains,
                track=submission['track'],
                submission_type=submission['submission_type'].split(' ')[0],
                speakers=speakers,
                biography=biography,
                affiliation=', '.join([x['affiliation']
                                       for x in submission['speakers']]),
                twitter_image="/static/media/twitter/" +
                f"{submission['code']}.jpg",
                meta_title=meta_title,
                meta_twitter_title=meta_twitter_title,
                categories=categories,
                categories_list=categories_list,
                skill=skill,
                domain_expertise=domain_expertise,
                slugified_slot_links=slugified_slot_links,
                start_time=start_time,
                room=room,
                day=day,
            ))
        print('DONE')

    if in_place_submissions:  # leftover dirs
        for zombie in in_place_submissions:
            # TODO could try to redirect zombies via code
            zpath = project_root / Path('website/content/program/') / zombie
            try:
                code = zombie.split('-')[1].upper()
                if redirects.get(code):
                    create_redirect(zpath, slug=redirects.get(code))
            except Exception:
                shutil.rmtree(zpath)

    for category in all_categories:
        cpath = (project_root /
                 Path('website/content/program-categories') /
                 category)
        if not cpath.exists():
            cpath.mkdir()

            print(f'Updating {str(cpath / "contents.lr")}... ', end='')
            with open(cpath / 'contents.lr', 'w') as f:
                f.write("""name: {0}
---
title: {0} Session List
---
description: All {0} sessions at the PyConDE & Pydata Berlin 2019 conference
---""".format(all_categories[category]))
            print('DONE')


def create_redirect(redir_dirname, slug):
    redir_dirname.mkdir(exist_ok=True)

    print(f'Updating {str(redir_dirname / "contents.lr")}... ', end='')
    with open(redir_dirname / "contents.lr", "w") as f:
        f.write("""_model: redirect
---
target: /program/{}
---
_discoverable: no""".format(slug))
    print('DONE')
