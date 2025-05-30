from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="aeon-weapon-generator",
    version="1.0.0",
    author="AEON Team",
    description="AI-powered weapon generation service for AEON MMORPG",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "gpu": [
            "torch>=2.0.0",
            "torchvision",
            "trimesh",
            "transformers",
            "diffusers",
            "accelerate",
        ],
        "dev": [
            "pytest>=7.4.3",
            "black",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "aeon-weapon-generator=main:main",
        ],
    },
)