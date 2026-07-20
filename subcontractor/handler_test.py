import re
from subcontractor.handler import _hideify


def test_hideify():
  parameters = { 'a': 'b' }
  assert _hideify( parameters ) == { 'a': 'b' }
  assert parameters == { 'a': 'b' }

  parameters = { 'password': 'my secret' }
  assert _hideify( parameters ) == { 'password': 'salt:488c46661db89a7f78d82aefb033d59b665b21e86a199a3569cb471368f40799' }
  assert parameters == { 'password': 'my secret' }

  parameters = [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]
  assert _hideify( parameters ) == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]
  assert parameters == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]

  parameters = [ { 'a': 'b', 'token': 'no lookie', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'private' } ]
  assert _hideify( parameters ) == [ { 'a': 'b', 'token': 'salt:a6ef67665525e498ae5b6a82726cedae8cc44827cec915250e47abb9dadfdd96', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'salt:522f43f233f7f3b4e40f0b728d8e5fb518ff709806fe3b264bb26026f5bde9d5' } ]
  assert parameters == [ { 'a': 'b', 'token': 'no lookie', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'private' } ]

  parameters = 'asdf'
  assert _hideify( parameters ) == 'asdf'
  assert parameters == 'asdf'

  parameters = 123
  assert _hideify( parameters ) == 123
  assert parameters == 123

  parameters = {}
  assert _hideify( parameters ) == {}
  assert parameters == {}

  parameters = []
  assert _hideify( parameters ) == []
  assert parameters == []

  tmp_obj = object()
  parameters = { 'a': re.compile( '' ), 'password': 'my secret', 'b': tmp_obj }
  assert _hideify( parameters ) == { 'a': re.compile( '' ), 'password': 'salt:488c46661db89a7f78d82aefb033d59b665b21e86a199a3569cb471368f40799', 'b': tmp_obj }
  assert parameters == { 'a': re.compile( '' ), 'password': 'my secret', 'b': tmp_obj }

  parameters = [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'hi' } ] } ] ]
  assert _hideify( parameters ) == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'salt:4925ec767f025a510a1b549340f21f139573007c80b1a8f137ecfa9f4d43b305' } ] } ] ]
  assert parameters == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'hi' } ] } ] ]
