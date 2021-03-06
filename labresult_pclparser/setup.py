from setuptools import setup, find_packages

setup(
    name='labresult_pclparser',
    version="1.0",
    description="LabResult plugin to parse PCL documents",
    author="Julien Almarcha",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["labresult"],
    entry_points="""
    [labresult.plugin.parser]
    parser=labresult_pclparser:get_parser_plugin
""",
)


