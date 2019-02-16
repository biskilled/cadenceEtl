from setuptools import setup

setup(
    name='popEye-Etl',
    version='1.1.0',
    packages=['lib.popEye-Etl', 'lib.popEye-Etl.glob', 'lib.popEye-Etl.mapp', 'lib.popEye-Etl.loader',
              'lib.popEye-Etl.connections', 'docs.rst', 'docs._themes', 'docs._themes.sphinx_rtd_theme'],
    url='',
    license='MIT',
    author='Tal Shany',
    author_email='tal@BiSkilled.com',
    description='Fast data modeling in integration platform '
)
