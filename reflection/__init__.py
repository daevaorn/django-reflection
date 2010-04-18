from django.dispatch import Signal
from django.db.models import signals

instance_changed = Signal(
    providing_args=["instance", "key", "sender", "data", "layer"]
)

class ModelLayerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        try:
            ModelLayer
        except NameError:
            pass
        else:
            if not "model" in attrs:
                raise ValueError("Layer model must be specified")

            if not "fields" in attrs and "aliases" not in attrs:
                raise ValueError("Layer fields or aliases must be specified")

            if not "key" in attrs:# TODO: add composition key
                raise ValueError("Layer model key must be specified")

            if not "create" in attrs:
                attrs["create"] = False

        return type.__new__(cls, name, bases, attrs)

class ModelLayer(object):
    __metaclass__ = ModelLayerMetaclass

    def __init__(self, track_id=None):
        self.track_id = track_id

    def is_locked(self):
        return TRACKING_LOCK[self.track_id]

    def lock_track(self):
        TRACKING_LOCK[self.track_id] = True

    def unlock_track(self):
        TRACKING_LOCK[self.track_id] = False

    def post_save_handler(self, instance, **kwargs):
        if self.is_locked():
            return

        instance_changed.send(
            instance=instance,
            key=getattr(instance, self.key),
            data=self._collect_data(instance),
            sender=self.track_id,
            layer=self
        )

    def instance_changed_handler(self, instance, key, data, sender, layer, **kwargs):
        if layer == self:
            return

        self.lock_track()
        try:
            self._update_instance(key, data)
        except Exception:
            pass
        self.unlock_track()

    def _update_instance(self, key, data):
        try:
            instance = self.model._default_manager.get(**{self.key: key})
        except self.model.DoesNotExist:
            if self.create:
                instance = self.model(**{self.key: key})
            else:
                return

        for name, value in data.iteritems():
            if name in self.fields:
                setattr(instance, name, value)
            elif name in self.aliases:
                setattr(instance, self.aliases[name], value)

        instance.save()

    def _collect_data(self, instance):
        data = {}

        for name in self.fields:
            if hasattr(instance, name):
                data[name] = getattr(instance, name)

        for alias, name in self.aliases.iteritems():
            if hasattr(instance, name):
                data[alias] = getattr(instance, name)

        return data

    def track_changes(self, track_id):
        self.track_id = track_id

        signals.post_save.connect(self.post_save_handler, sender=self.model, weak=False)
        instance_changed.connect(self.instance_changed_handler, sender=self.track_id, weak=False)

TRACKING_LOCK = {}

def track(layers):
    track_id = id(layers)

    TRACKING_LOCK[track_id] = False

    for layer in layers:
        if isinstance(layer, type):
            layer = layer()
        layer.track_changes(track_id)
