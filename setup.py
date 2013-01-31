from setuptools import setup, find_packages

setup(
    name="breezeminder",
    version='0.1',
    author="Shaun Duncan",
    author_email="shaun.duncan@gmail.com",
    description=("Breeze Card Automated Reminders"),
    long_description=open("README.rst").read(),
    url="https://github.com/shaunduncan/breezeminder",
    zip_safe=False,
    include_package_data=True,
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst', '.html'],
    },
    packages=find_packages(),
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Flask",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ]
)
