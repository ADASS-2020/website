from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List
import numpy as np
from dateutil.parser import parse
from . import utils


@dataclass
class Speaker:
    name: str
    affiliation: str


@dataclass
class ScheduleElement:
    """
    An item in a schedule.

    It can be a Talk, a break a tutorial etc. It will be serialised to JSON.
    """
    name: str
    track: str
    duration: timedelta
    description: str
    abstract: str
    skill: str
    domain_expertise: str
    domains: str
    slug: str
    title: str
    speaker_names: List[str]
    type: str
    url: str
    plenary: bool
    start: datetime
    end: datetime
    room_name: str
    add_to_class: str = ''
    clipcard_icon: str = ''
    code: str = ''


@dataclass
class Schedule:
    """
    A Schedule object is a numpy array of Optional[ScheduleElement] values and
    some metadata to help create JSON schedule files needed by the site
    builder.

    Metadata:
        self.rooms: sorted list of room names
        self.slots: sorted list of datetime.time() values (event start times)
        self.dates: sorted list of datetime.date() values (conference days)

    The schedule array (self._schedule)
        For each day:
               | Room1 | Room2 | ...
        time 1 | event | event | ...
        time 2 | event | None  | ...
        ...     ....    ...
    """
    rooms: List[str]
    slots: List[datetime]
    dates: List[date]
    elements: List[ScheduleElement]

    def __post_init__(self):
        self._schedule = np.full(
            shape=(len(self.dates), len(self.slots), len(self.rooms)),
            fill_value=None,
            dtype=ScheduleElement
        )

        for event in self.elements:
            t = self.slots.index(event.start.time())
            r = self.rooms.index(event.room_name)
            d = self.dates.index(event.start.date())
            assert self._schedule[d, t, r] is None
            self._schedule[d, t, r] = event

        # Cleanup self.elements
        del(self.elements)
        return

    def __iter__(self):
        return self._schedule.__iter__()

    @staticmethod
    def _parse_raw_schedule(raw_schedule):
        rooms = set()
        slots = set()
        dates = set()
        elements = []

        for raw_day in raw_schedule['schedule']['conference']['days']:
            dt = parse(raw_day['date'])

            for room_name, raw_list in raw_day['rooms'].items():
                rooms.add(room_name)

                for raw_item in raw_list:
                    spkrs = utils.get_speakers(raw_item['persons'])
                    spkrs_affil = utils.format_speakers_affiliations(spkrs)
                    slug = utils.slugify(
                        f"{raw_item['track']}-" +
                        f"{raw_item['slug']}-" +
                        f"{raw_item['title']}-" +
                        f"{spkrs_affil}"
                    )
                    answers = raw_item['answers']

                    dt = parse(raw_item['date'])
                    elements.append(
                        ScheduleElement(
                            code=raw_item['slug'],
                            name='',
                            track=raw_item['track'],
                            duration=utils.parse_duration(
                                raw_item['duration']
                            ),
                            description=raw_item['description'],
                            abstract=raw_item['abstract'],
                            skill=utils.get_skill(answers),
                            domain_expertise=utils.get_domain_expertise(
                                answers
                            ),
                            domains=utils.get_domains(answers),
                            slug=slug,
                            title=raw_item['title'],
                            speaker_names=spkrs_affil,
                            type=raw_item['type'],
                            url=f'/program/{slug}',
                            plenary=utils.is_plenary(raw_item),
                            add_to_class='',
                            clipcard_icon=utils.format_icon(raw_item),
                            start=dt,
                            end=utils.compute_endtime(raw_item),
                            room_name=room_name
                        )
                    )
                    slots.add(dt.time())
                    dates.add(dt.date())
        return list(rooms), sorted(list(slots)), sorted(list(dates)), elements

    @classmethod
    def from_pretalx(cls, raw_schedule):
        """
        Given a raw schedule dict from pretalx JSON, create a numpy array with
        the schedule information.
        """
        # First of all we need to know the number of days, all the rooms and
        # all the time slots. Once we know these three numbers we can create a
        # matrix
        rooms, slots, dates, elements = cls._parse_raw_schedule(raw_schedule)

        # FIXME: Order????
        return cls(rooms, slots, dates, elements)
