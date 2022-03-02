import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='hsim',
    version='0.0.3',
    author='Lorenzo',
    author_email='_',
    description='_',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/lorenzo-ragazzini/hsim',
    license='MIT',
    packages=['hsim'],
    # install_requires=['requests'],
)