import factory
from youtubarr import models

class PlaylistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Playlist
    playlist_id = factory.Sequence(lambda n: f"PL_TEST_{n}")

class ArtistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Artist
    name = factory.Sequence(lambda n: f"Artist {n}")
    mbid = factory.Faker("uuid4")

class TrackItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TrackItem
    playlist = factory.SubFactory(PlaylistFactory)
    video_id = factory.Sequence(lambda n: f"vid{n}")
    title = factory.Sequence(lambda n: f"Title {n}")
    channel_title = "Foo - Topic"
    artist_name_guess = "Foo"
