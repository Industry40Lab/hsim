import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hsim",
    version="0.0.1",
    author="Lorenzo",
    author_email="@",
    description="hsim",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lorenzo-ragazzini/hsim@full",
    packages=setuptools.find_namespace_packages()+setuptools.find_packages(),
    package_data={'hsim': ['hsim/c/dataset.csv']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    license="MIT",
    platforms="Python 3",
)
