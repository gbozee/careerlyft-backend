from cv_utils.utils import classproperty

class SharedMixin(object):
    db_route = "services"

    @classproperty
    def s_objects(cls):
        return cls.objects.using(cls.db_route)
