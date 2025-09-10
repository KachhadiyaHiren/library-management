from setuptools import setup, find_packages

setup(
    name="library-management-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A basic Library Management System using Flask",
    packages=find_packages(),
    install_requires=[
        "Flask>=2.3.0",
        "Werkzeug>=2.3.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)