from optomechanics.data_management.file_management import make_path
def test_empty(): assert make_path([])==""
def test_one(): assert make_path(["a"])=="a\\"
def test_two(): assert make_path(["a","b"])=="a\\b\\"
def test_three(): assert make_path(["a","b","c"])=="a\\b\\c\\"
def test_trailing(): r=make_path(["x"]); assert r[-1]=="\\"
def test_nonempty(): assert len(make_path(["z"]))>0
