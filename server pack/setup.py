from setuptools import setup, find_packages

setup(name='client_chat_for_task',
      version='0.1',
      description='Client packet',
      packages=find_packages(),
      author_email='test@gmail.com',
      author='Smiker',
      install_requeres=['PyQt5', 'sqlalchemy', 'pycruptodome', 'pycryptodomex']
      )