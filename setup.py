from distutils.core import setup
import py2exe
import modules

setup(
    console=['lisanalyze.py'],
    options={
        "py2exe": {
            "includes": ["pint","jsonschema"],
            "packages": ["modules"]
        }
    }
)
