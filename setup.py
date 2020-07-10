"""Package install configuration."""

import setuptools

# pylint: disable=invalid-name

version='0.5.1'

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='gcpinfra',
    version=version,
    author='Alex Newman',
    author_email='a.newmanvs@gmail.com',
    description='Google Cloud Platform non-official framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/anewmanvs/gcpinfra',
    download_url='https://github.com/anewmanvs/gcpinfra/archive/v{}.tar.gz'.format(
        version),
    packages=setuptools.find_packages(),
    keywords=['gcp', 'google cloud platform', 'framework'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3'
    ],
    include_package_data=True,
    install_requires=[
        'pandas>=1.0.1',
        'setuptools>=36.5.0',
        'google-cloud-storage>=1.26.0',
        'google-cloud-dataproc>=0.6.1',
        'google-auth>=1.11.2',
        'crc32c>=2.0',
        'pyarrow>=0.16.0',
        'google-api-python-client>=1.7.11'
    ],
    python_requires='>=3'
)
