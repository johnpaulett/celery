from __future__ import absolute_import

from .. import current_app
from ..utils import uuid

from .sets import TaskSet


class Chord(current_app.Task):
    name = "celery.chord"

    def run(self, set, body, interval=1, max_retries=None,
            propagate=False, **kwargs):
        if not isinstance(set, TaskSet):
            set = TaskSet(set)
        r = []
        setid = uuid()
        for task in set.tasks:
            tid = uuid()
            task.options.update(task_id=tid, chord=body)
            r.append(current_app.AsyncResult(tid))
        current_app.TaskSetResult(setid, r).save()
        self.backend.on_chord_apply(setid, body, interval,
                                    max_retries=max_retries,
                                    propagate=propagate)
        return set.apply_async(taskset_id=setid)


class chord(object):
    Chord = Chord

    def __init__(self, tasks, **options):
        self.tasks = tasks
        self.options = options

    def __call__(self, body, **options):
        tid = body.options.setdefault("task_id", uuid())
        self.Chord.apply_async((list(self.tasks), body), self.options,
                                **options)
        return body.type.app.AsyncResult(tid)