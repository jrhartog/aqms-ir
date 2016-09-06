from setuptools import setup

setup(name="aqms-ir", 
    version="0.0.1",
    description="translation between obspy Inventory object and AQMS schema",
    url="http://github.com/jrhartog/aqms-ir",
    author="Renate Hartog",
    license="MIT",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Science/Research',
    ],
    packages=["aqms-ir"],
    scripts=["inventory2aqms"],
    install_requires=["numpy","obspy>=0.10.2","SQLAlchemy","psycopg2"],
    zip_safe=False)

