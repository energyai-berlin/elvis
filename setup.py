"""
Legacy setup.py for backward compatibility.
Modern packaging is handled via pyproject.toml - use 'uv build' or 'pip install .' instead.
"""

import setuptools

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

# Dependencies are now managed via pyproject.toml
REQUIREMENTS = [
    "matplotlib>=3.10.6",
    "networkx>=3.5",
    "numpy>=2.3.0",
    "pyyaml>=6.0.2",
    "pandas>=2.3.2",
    "scipy>=1.16.1",
    "scikit-learn>=1.7.2",
]

setuptools.setup(
    name="py-elvis",
    version="0.1.0",
    author="Moritz Markschläger, Jonas Zell, Marcus Voss, Mahmoud Draz, and Izgh Hadachi",
    author_email="moritz.markschlaeger@dai-labor.de",
    description="A planning and management tool for electric vehicles charging infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EnergyAIBerlin/elvis",
    project_urls={
        "Homepage": "https://github.com/EnergyAIBerlin/elvis",
        "Documentation": "https://github.com/EnergyAIBerlin/elvis#readme",
        "Repository": "https://github.com/EnergyAIBerlin/elvis.git",
        "Issues": "https://github.com/EnergyAIBerlin/elvis/issues",
    },
    packages=setuptools.find_packages(),
    install_requires=REQUIREMENTS,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    keywords=["electric vehicles", "charging infrastructure", "simulation", "energy"],
)
