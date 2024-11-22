from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-agent-state",
    version='0.1.12',
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
        "chromadb>=0.3.0,<1.0.0",
        "openai>=0.27.0,<1.0.0",
        "python-dotenv>=0.19.0,<1.0.0",
        "numpy>=1.20.0,<2.0.0",
        "pandas>=1.2.0,<2.0.0",
        "tqdm>=4.60.0,<5.0.0",
        "sentence-transformers>=2.0.0,<3.0.0",
        "typing-extensions>=3.7.4,<5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0,<8.0.0",
            "pytest-cov>=2.10.0,<4.0.0",
        ],
        "viz": [
            "graphviz>=0.16,<1.0.0",
        ],
    },
)