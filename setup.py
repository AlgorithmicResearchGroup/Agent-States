from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-agent-state",
    version='0.1.13',
    author="Algorithmic Research Group",
    author_email="matt@algorithmicresearchgroup.com",
    description="A library for managing state machines in AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AlgorithmicResearchGroup/Agent-States",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "chromadb",
        "openai",
        "python-dotenv",
        "numpy",
        "pandas",
        "tqdm",
        "sentence-transformers",
        "typing-extensions",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
        ],
        "viz": [
            "graphviz",
        ],
    },
)