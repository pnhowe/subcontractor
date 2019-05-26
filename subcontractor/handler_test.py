import re
from subcontractor.handler import _hideify


def test_hideify():
  paramaters = { 'a': 'b' }
  assert _hideify( paramaters ) == { 'a': 'b' }
  assert paramaters == { 'a': 'b' }

  paramaters = { 'password': 'my secret' }
  assert _hideify( paramaters ) == { 'password': 'salt:488c46661db89a7f78d82aefb033d59b665b21e86a199a3569cb471368f40799' }
  assert paramaters == { 'password': 'my secret' }

  paramaters = [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]
  assert _hideify( paramaters ) == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]
  assert paramaters == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 } ]

  paramaters = [ { 'a': 'b', 'token': 'no lookie', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'private' } ]
  assert _hideify( paramaters ) == [ { 'a': 'b', 'token': 'salt:a6ef67665525e498ae5b6a82726cedae8cc44827cec915250e47abb9dadfdd96', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'salt:522f43f233f7f3b4e40f0b728d8e5fb518ff709806fe3b264bb26026f5bde9d5' } ]
  assert paramaters == [ { 'a': 'b', 'token': 'no lookie', 'c': 'd' }, { 'z': 'x', 'y': 43, 'password': 'private' } ]

  paramaters = 'asdf'
  assert _hideify( paramaters ) == 'asdf'
  assert paramaters == 'asdf'

  paramaters = 123
  assert _hideify( paramaters ) == 123
  assert paramaters == 123

  paramaters = {}
  assert _hideify( paramaters ) == {}
  assert paramaters == {}

  paramaters = []
  assert _hideify( paramaters ) == []
  assert paramaters == []

  tmp_obj = object()
  paramaters = { 'a': re.compile( '' ), 'password': 'my secret', 'b': tmp_obj }
  assert _hideify( paramaters ) == { 'a': re.compile( '' ), 'password': 'salt:488c46661db89a7f78d82aefb033d59b665b21e86a199a3569cb471368f40799', 'b': tmp_obj }
  assert paramaters == { 'a': re.compile( '' ), 'password': 'my secret', 'b': tmp_obj }

  paramaters = [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'hi' } ] } ] ]
  assert _hideify( paramaters ) == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'salt:4925ec767f025a510a1b549340f21f139573007c80b1a8f137ecfa9f4d43b305' } ] } ] ]
  assert paramaters == [ { 'a': 'b', 'c': 'd' }, { 'z': 'x', 'y': 43 }, [ { 'sdf': 'sdf', 'bob': [ 1, 23, 3, 4, { 'token': 'hi' } ] } ] ]
