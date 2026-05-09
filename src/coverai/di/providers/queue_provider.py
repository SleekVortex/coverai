from dishka import Provider, Scope, from_context

from coverai.domain.generation_job_queue import GenerationJobQueue


class QueueProvider(Provider):
    generation_job_queue = from_context(GenerationJobQueue, scope=Scope.REQUEST)
