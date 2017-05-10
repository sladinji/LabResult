from setuptools import setup,find_packages

setup(
    name='labresult',
    version='0.1',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'uwsgi',
        'flask-admin == 1.3.0',
        'flask-mongoengine',
        'mongoengine == 0.8.7',
        'pymongo == 2.8',
        'flask-restful',
        'flask-wtf',
        'flask-debugtoolbar',
        'flask-babelex',
        'flask-login',
        'celery',
        'pypdf2',
        'pillow',
        'flask',
        'werkzeug',
        'requests',
        'pdfquery',
    ],
     entry_points={
        'console_scripts': [
            'add_admin = labresult.lib.scripts:add_admin',
            'gen_result = labresult.lib.scripts:gen_result',
            'set_demo_options = labresult.lib.scripts:set_demo_options',
        ],
     },

)
