from setuptools import setup, find_packages

setup(
    name="ai-agentic",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "openai",
        "python-dotenv",
        "google-generativeai",
    ],
    entry_points={
        "console_scripts": [
            "aios=runtime.cli:main",
        ],
    },
)
