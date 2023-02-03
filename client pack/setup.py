from setuptools import setup, find_packages

setup(name='server_chat_for_task',
      version='0.1',
      description='Server packet',
      packages=find_packages(),
      author_email='test@mail.ru',
      author='Smiker',
      install_requeres=['PyQt5', 'sqlalchemy', 'pycruptodome', 'pycryptodomex']
      )