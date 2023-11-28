from setuptools import setup, find_packages  # type: ignore

setup(
    name="vigil-llm",
    version="0.8.7",
    description="LLM prompt and response security scanner",
    long_description=open("README.md", "r", encoding="utf8").read(),
    long_description_content_type="text/markdown",
    author="Adam M. Swanda",
    author_email="adam@deadbits.org",
    url="https://github.com/deadbits/vigil-llm",
    packages=find_packages(),
    install_requires=[
        line
        for line in open("requirements.txt").read().splitlines()
        if not line.startswith("#")
    ],
    python_requires=">=3.9",
    project_urls={
        "Homepage": "https://vigil.deadbits.ai",
        "Source": "https://github.com/deadbits/vigil-llm",
    },
)
