from datetime import date

from django.db import models
from django.contrib.auth.models import User

import reflection

class Profile(models.Model):
    user_ptr = models.ForeignKey(User, unique=True)
    nickname = models.CharField(max_length=100)
    www = models.URLField()
    birth = models.DateField()

    class Meta:
        app_label="reflection"

class OtherProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    nickname = models.CharField(max_length=100)
    website = models.URLField()
    dob = models.DateField()

    class Meta:
        app_label="reflection"

class MyProfileLayer(reflection.ModelLayer):
    model = Profile
    fields = ["nickname"]
    aliases = {
        "site": "www",
        "day_of_birth": "birth"
    }
    key = 'user_ptr'

class OtherProfileLayer(reflection.ModelLayer):
    model = OtherProfile
    fields = ["nickname"]
    aliases = {
        "site": "website",
        "day_of_birth": "dob"
    }
    key = 'user'
    create = True

reflection.track([MyProfileLayer, OtherProfileLayer])

__test__ = {'': r"""
>>> user = User.objects.create_user('test', 'foobar@foo.bar')
>>> profile = Profile.objects.create(user_ptr=user, nickname='test_foo',
...                                  www='test_foo', birth=date(1987, 6, 25))

>>> OtherProfile.objects.filter(user=user).count()
1
>>> other = OtherProfile.objects.get(user=user)
>>> other.nickname, other.website, other.dob
(u'test_foo', u'test_foo', datetime.date(1987, 6, 25))

>>> other.website = 'http://bar.foo'
>>> other.save()
>>> Profile.objects.get(user_ptr=user).www
u'http://bar.foo'

>>> profile.www = 'http://foo.bar'
>>> profile.save()
>>> OtherProfile.objects.get(user=user).website
u'http://foo.bar'
"""}
