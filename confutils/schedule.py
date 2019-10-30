import json
from pathlib import Path
from . import utils
from .model import Schedule
from .constants import MIDDAY, DAY_START, DAY_END


def dump_date_room_timeslot_view(schedule: Schedule, outpath: Path) -> None:
    output_schedule = {'dates': []}
    for date_index, day_schedule in enumerate(schedule):
        dt = schedule.dates[date_index]

        day = {}
        day['day'] = utils.human_format_date(dt)
        day['datum'] = utils.format_date(dt)
        day['rooms'] = []

        for room_index, room_events in enumerate(day_schedule.T):
            room_name = schedule.rooms[room_index]

            # TODO: Get room details from somewhere sensible.
            room_schedule = {
                'room_name': room_name,
                'location': 'center',
                'use': 'talks/keynotes',
                'data_tab': f'{day["datum"]}-{room_name}',
                'sessions': []
            }
            for slot_index, event in enumerate(room_events):
                slot_time = schedule.slots[slot_index]

                if event is None:
                    item = {
                        'code': '',
                        'name': '',
                        'track': '',
                        'duration': '',
                        'description': '',
                        'short_description': '',
                        'skill': '',
                        'domain_expertise': '',
                        'domains': '',
                        'slug': '',
                        'title': '',
                        'speaker_names': '',
                        'type': '',
                        'url': '',
                        'plenary': '',
                        'add_to_class': '',
                        'clipcard_icon': '',
                        'time': utils.format_time(slot_time),
                        'start': utils.format_time(slot_time),
                        'end': '',
                    }
                else:
                    item = {
                        'code': event.slug,
                        'name': event.name,
                        'track': event.track,
                        'duration': utils.format_duration(event.duration),
                        'description': event.description,
                        'short_description': event.abstract,
                        'skill': event.skill,
                        'domain_expertise': event.domain_expertise,
                        'domains': event.domains,
                        'slug': event.slug,
                        'title': event.title,
                        'speaker_names': event.speaker_names,
                        'type': event.type,
                        'url': event.url,
                        'plenary': event.plenary,
                        'add_to_class': event.add_to_class,
                        'clipcard_icon': event.clipcard_icon,
                        'time': utils.format_time(slot_time),
                        'start': utils.format_time(slot_time),
                        'end': utils.format_time(event.end),
                    }
                room_schedule['sessions'].append(item)
            day['rooms'].append(room_schedule)
        output_schedule['dates'].append(day)

    print(f'Updating {str(outpath)}... ', end='')
    with outpath.open('w') as f:
        json.dump(output_schedule, f, indent=4)
    print('DONE')


def dump_date_timeslot_room_view(schedule: Schedule, outpath: Path) -> None:
    """ swap times and rooms """

    # Remember that schedule events are already sorted by date and time.

    output_schedule = {'dates': []}
    for date_index, day_schedule in enumerate(schedule):
        dt = schedule.dates[date_index]
        daystr = utils.human_format_date(dt)

        morning = {
            'datum': f'{utils.format_date(dt)} Morning',
            'day': f'{daystr} Morning',
            'times': []
        }
        afternoon = {
            'datum': f'{utils.format_date(dt)} Afternoon',
            'day': f'{daystr} Afternoon',
            'times': []
        }

        # Events are sorted by time already
        for slot_index, event_list in enumerate(day_schedule):
            # event_list are all events starting at the same time, in the
            # various rooms.

            slot_schedule = {}
            slot_time = schedule.slots[slot_index]
            if DAY_START > slot_time > DAY_END:
                print('Warning: skipping time slot {slot_time}')
                continue

            slot_timestr = utils.format_time(slot_time)
            for room_index, event in enumerate(event_list):
                room_name = schedule.rooms[room_index]

                session = morning
                suffix = 'Morning'
                if slot_time >= MIDDAY:
                    session = afternoon
                    suffix = 'Afternoon'

                if not slot_schedule:
                    # This is the first valid event of the time slot.
                    slot_schedule = {
                        'data_tab': f'{slot_timestr.replace(":", "-")}-' +
                                    f'{suffix.lower()}',
                        'time': slot_timestr,
                        'day_sec': f'{slot_timestr}-{suffix.lower()}',
                        'sessions': []
                    }

                if event:
                    item = {
                        'code': event.slug,
                        'name': event.name,
                        'track': event.track,
                        'duration': utils.format_duration(event.duration),
                        'description': event.description,
                        'short_description': event.abstract,
                        'skill': event.skill,
                        'domain_expertise': event.domain_expertise,
                        'domains': event.domains,
                        'slug': event.slug,
                        'title': event.title,
                        'speaker_names': event.speaker_names,
                        'type': event.type,
                        'url': event.url,
                        'plenary': event.plenary,
                        'add_to_class': event.add_to_class,
                        'clipcard_icon': event.clipcard_icon,
                        'time': slot_timestr,
                        'start': slot_timestr,
                        'end': utils.format_time(event.end),
                        'room_name': room_name,
                        # FIXME: Get these pieces from somewhere sensible.
                        'location': 'center',
                        'use': 'talks/keynotes',
                        'sessionname': '',
                    }
                else:
                    item = {
                        'code': '',
                        'name': '',
                        'track': '',
                        'duration': '',
                        'description': '',
                        'short_description': '',
                        'skill': '',
                        'domain_expertise': '',
                        'domains': '',
                        'slug': '',
                        'title': '',
                        'speaker_names': '',
                        'type': '',
                        'url': '',
                        'plenary': '',
                        'add_to_class': '',
                        'clipcard_icon': '',
                        'time': slot_timestr,
                        'start': slot_timestr,
                        'end': '',
                        'room_name': room_name,
                        # FIXME: Get these pieces from somewhere sensible.
                        'location': 'center',
                        'use': 'talks/keynotes',
                        'sessionname': '',
                    }

                slot_schedule['sessions'].append(item)
            session['times'].append(slot_schedule)
        if morning['times']:
            output_schedule['dates'].append(morning)
        if afternoon['times']:
            output_schedule['dates'].append(afternoon)

    print(f'Updating {str(outpath)}... ', end='')
    with outpath.open('w') as f:
        json.dump(output_schedule, f, indent=4)
    print('DONE')


def dump_table_view(schedule: Schedule, outpath: Path) -> None:
    output_schedule = {
        'header': ['time'] + schedule.rooms,
        'dates': []
    }

    for date_index, day_schedule in enumerate(schedule):
        dt = schedule.dates[date_index]
        daystr = utils.human_format_date(dt)

        day = {'day': daystr, 'sessions': []}

        # Events are sorted by time already
        for slot_index, event_list in enumerate(day_schedule):
            # event_list are all events starting at the same time, in the
            # various rooms.

            slot_time = schedule.slots[slot_index]
            if DAY_START > slot_time > DAY_END:
                print('Warning: skipping time slot {slot_time}')
                continue

            slot_timestr = utils.format_time(slot_time)

            sessions = [slot_timestr, ]
            for event in event_list:
                if event:
                    item = {
                        'title': event.title,
                        'speakers': event.speaker_names,
                        'code': event.slug,
                        'slug': event.slug,
                        'subm_type': event.type,
                        'duration': utils.format_duration(event.duration),
                        'colspan': 1,
                        'rowspan': 1,
                    }
                else:
                    item = {
                        'title': '',
                        'speakers': '',
                        'code': '',
                        'slug': '',
                        'subm_type': '',
                        'duration': '',
                        'colspan': 1,
                        'rowspan': 1,
                    }
                sessions.append(item)
            day['sessions'].append(sessions)
        output_schedule['dates'].append(day)

    print(f'Updating {str(outpath)}... ', end='')
    with outpath.open('w') as f:
        json.dump(output_schedule, f, indent=4)
    print('DONE')
