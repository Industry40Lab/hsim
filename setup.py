import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hsim",
    version="0.0.1",
    author="Lorenzo Ragazzini",
    author_email="",
    description="Discrete Event Simulation Framework for Manufacturing Systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Industry40Lab/hsim",
    packages=setuptools.find_namespace_packages() + setuptools.find_packages(),
    package_data={'hsim': ['c/dataset.csv']},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'sortedcontainers>=2.4.0',
        'numpy',
        'pandas',
        'matplotlib',
        'networkx',
        'openpyxl',
        'flask',
        'python-dotenv',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov',
            'pylint',
            'black',
        ],
    },
    license="MIT",
    platforms="any",
    keywords="simulation discrete-event-simulation manufacturing des industry-4.0",
)

