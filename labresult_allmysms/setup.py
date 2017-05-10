from setuptools import setup, find_packages

setup(
    name='labresult_allmysms',
    version="1.0",
    description="LabResult plugin for sending SMS",
    author="Julien Almarcha",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["labresult"],
    entry_points="""
    [labresult.plugin.sms]
    sms=labresult_allmysms:get_sms_plugin
""",
)


