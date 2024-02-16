from setuptools import setup

setup(
    name='pymusco',
    version=1.0,
    description='python musical score tool',
    url='https://github.com/g-raffy/pymusco',
    author='Guillaume Raffy',
    author_email='guillaume.raffy@univ-rennes1.fr',
    license='MIT',
    packages=['pymusco'],
    package_dir={
        '': 'src'
    },
    scripts = [
        'src/apps/pymusco'
    ],
    install_requires=[
        'PyPDF2>= 3.0.0',  # the syntax has changed between PyPDF2 2.x and PyPDF2 3.x
        'pillow',
        'opencv-python'
    ],
    zip_safe=False)
