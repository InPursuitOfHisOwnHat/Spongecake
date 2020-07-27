import setuptools

with open("README.txt", "r") as fh:
    long_description = fh.read()
print('Number of pacakages: {0}'.format(len(setuptools.find_packages())))
for p in setuptools.find_packages():
    print('Pacckage: ' + p)

setuptools.setup(
    name='spongecake',
    version='1.0',
    author="Chris Akers",
    description="Equity Data Analyser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
