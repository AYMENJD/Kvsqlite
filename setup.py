from re import findall
from setuptools import setup, find_packages


with open("kvsqlite/__init__.py", "r") as f:
    version = findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", "r") as f:
    readme = f.read()


setup(
    name="Kvsqlite",
    version=version,
    description="Easy-to-use synchronous/asynchronous key-value database backed by sqlite3.",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="AYMEN Mohammed",
    author_email="let.me.code.safe@gmail.com",
    url="https://github.com/AYMENJD/Kvsqlite",
    license="MIT",
    python_requires=">=3.8",
    project_urls={
        "Source": "https://github.com/AYMENJD/Kvsqlite",
        "Tracker": "https://github.com/AYMENJD/Kvsqlite/issues",
        "Documentation": "https://kvsqlite.rtfd.io/",
    },
    packages=find_packages(exclude=["docs"]),
    keywords=[
        "sync",
        "asyncio",
        "sqlite",
        "sqlite3",
        "key-value",
        "database",
        "redis",
    ],
)
