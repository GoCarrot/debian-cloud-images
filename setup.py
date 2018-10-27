import setuptools

setuptools.setup(
    name='debian_cloud_images',
    version='0',
    packages=setuptools.find_namespace_packages(exclude=['tests', 'tests.*']),
    entry_points={
        'console_scripts': ['debian-cloud-images=debian_cloud_images.cli.all:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)"
        "Operating System :: POSIX :: Linux",
    ],
)
