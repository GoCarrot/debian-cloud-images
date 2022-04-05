import setuptools

setuptools.setup(
    name='debian_cloud_images',
    version='0',
    install_requires=[
        'apache-libcloud',
        'marshmallow>=3.0.0b14',
        'PyYAML',
    ],
    packages=setuptools.find_namespace_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['debian-cloud-images=debian_cloud_images.cli.__main__:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)"
        "Operating System :: POSIX :: Linux",
    ],
)
