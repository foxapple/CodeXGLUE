from distutils.core import setup
 
setup(
    name='pvlib',
    version='0.1',
	author='Dan Riley, Clifford Hanson and Rob Andrews',
	author_email='Rob.Andrews@calamaconsulting.ca',
	packages=['pvlib','pvlib.test'],
    license='The BSD 3-Clause License',
    url = 'https://github.com/Sandia-Labs/PVLIB_Python', #
  	download_url = 'https://github.com/Sandia-Labs/PVLIB_Python/tarball/0.1', # I'll explain this in a second
    long_description=open('README.txt').read(),
)



