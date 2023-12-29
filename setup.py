from setuptools import setup, find_packages

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
        'openai==1.0.0',
        'transformers==4.36.0',
        'pydantic==1.10.7',
        'Flask==3.0.0',
        'yara-python==4.3.1',
        'configparser==5.3.0',
        'pandas==2.0.0',
        'pyarrow==14.0.1',
        'sentence-transformers==2.2.2',
        'chromadb==0.4.17',
        'streamlit==1.26.0',
        'numpy==1.25.2',
        'loguru==0.7.2',
        'nltk==3.8.1',
        'datasets==2.15.0'
    ],
    python_requires=">=3.9",
    project_urls={ 
        "Homepage": "https://vigil.deadbits.ai",
        "Source": "https://github.com/deadbits/vigil-llm",
    },
)
