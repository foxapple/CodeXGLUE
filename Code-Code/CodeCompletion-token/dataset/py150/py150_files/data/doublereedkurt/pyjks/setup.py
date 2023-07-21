
import os
from setuptools import setup, find_packages


try:
    readme_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'README.md')
    with open(readme_path) as f:
        long_description = f.read()
except:
    long_description = None

setup(
    name='pyjks',
    version='0.3.1',
    author="Kurt Rose",
    author_email="kurt@kurtrose.com",
    description='pure python jks file parser',
    keywords="JKS JCEKS java keystore",
    license="MIT",
    url="http://github.com/doublereedkurt/pyjks",
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
    ],
    packages=find_packages(),
    install_requires=['pyasn1', 'pyasn1_modules', 'javaobj-py3', 'pycrypto'],
    test_suite="tests.test_jks",
)
