from setuptools import setup, find_packages

setup(
    name='labresult_admin',
    version="1.0",
    description="LabResult plugin for admin access",
    author="Julien Almarcha",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["labresult"],
    entry_points="""
    [labresult.plugin.admin]
    admin=labresult_admin:load_views
""",
)
