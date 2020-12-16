from setuptools import find_packages, setup


setup(
    name="pynuki",
    version="1.4.1",
    license="GPL3",
    description="Python bindings for nuki.io bridges",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Philipp Schmitt",
    author_email="philipp@schmitt.co",
    url="https://github.com/pschmitt/pynuki",
    packages=find_packages(),
    install_requires=["requests"],
)
