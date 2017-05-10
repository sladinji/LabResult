from setuptools import setup, find_packages

setup(
    name='labresult_demo',
    version="1.0",
    description="Demo login page for labresult",
    author="Julien Almarcha",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["labresult"],
    entry_points="""
    [labresult.plugin.login]
    demo_login=labresult_demo:get_plugin_view
    [labresult.plugin.menu]
    demo_menu=labresult_demo:get_plugin_menu
""",
)


