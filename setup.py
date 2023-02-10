from re import findall
from setuptools import setup, find_packages


with open("kvsqlite/__init__.py", "r") as f:
    version = findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", "r") as f:
    readme = f.read()

with open("requirements.txt", "r") as f:
    requirements = [x.strip() for x in f.readlines()]


setup(
    name="Kvsqlite",
    version=version,
    description="Easy-to-use asynchronous key-value database backed by sqlite3.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="AYMEN Mohammed",
    author_email="let.me.code.safe@gmail.com",
    url="https://github.com/AYMENJD/kvsqlite",
    license="MIT",
    python_requires=">=3.8",
    install_requires=requirements,
    project_urls={
        "Source": "https://github.com/AYMENJD/kvsqlite",
        "Tracker": "https://github.com/AYMENJD/kvsqlite/issues",
    },
    packages=find_packages(exclude=["docs", "test", "benchmark"]),
    keywords=[
        "asyncio",
        "sqlite",
        "sqlite3",
        "key-value",
        "database",
        "redis",
    ],
)
