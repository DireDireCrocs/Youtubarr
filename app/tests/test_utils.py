from youtubarr.utils import guess_artist_from_title

def test_guess_artist_basic():
    assert guess_artist_from_title("Artist - Song", "X") == "Artist"

def test_guess_from_topic_channel():
    assert guess_artist_from_title("Weird Title", "Foo - Topic") == "Foo"

def test_guess_empty():
    assert guess_artist_from_title("Song Name Only", "Channel") == ""
