from setuptools import setup, find_packages

setup(
    name="video_transcriber",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.7.0',
        'faster-whisper>=0.10.0',
        'torch>=2.2.0',
        'numpy>=1.24.0',
        'ffmpeg-python>=0.2.0',
    ],
    entry_points={
        'console_scripts': [
            'video_transcriber=run:main',
        ],
    },
    package_data={
        'src.ui': ['resources/*'],
        'config': ['*.json'],
    },
    python_requires='>=3.8',
    author="Your Name",
    description="A video transcription application using Whisper AI",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)
